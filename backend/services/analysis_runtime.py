from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi.encoders import jsonable_encoder

from services.ai_service import AIAnalystService
from services.data_service import DataService
from services.runtime import ActionRuntime, CausalRuntime, ChartRuntime, TrustRuntime

DEFAULT_QUERY_LIMIT = 1200
SPRINT_QUERY_LIMIT = 2000
PROBE_QUERY_LIMIT = 900
MAX_EXPLORATION_PROBES = 3


class AnalysisRuntime:
    """Runtime orchestration for analysis, trust scoring, causal lab, and actions."""

    def __init__(self, ai_analyst: AIAnalystService, data_service: DataService):
        self.ai_analyst = ai_analyst
        self.data_service = data_service
        self.chart_runtime = ChartRuntime()
        self.trust_runtime = TrustRuntime()
        self.causal_runtime = CausalRuntime()
        self.action_runtime = ActionRuntime()

    def build_chart_options(
        self,
        data: list[dict[str, Any]],
        base_config: dict[str, Any],
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        return self.chart_runtime.build_chart_options(
            data=data,
            base_config=base_config,
            analysis_type=analysis_type,
        )

    def optimize_data_for_chart(
        self,
        data: list[dict[str, Any]],
        chart_config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return self.chart_runtime.optimize_data_for_chart(data=data, chart_config=chart_config)

    def build_trust_layer(
        self,
        question: str,
        analysis_type: str,
        sql: str,
        row_count: int,
        visualized_row_count: int,
        chart_config: dict[str, Any],
        profile: dict[str, Any] | None,
        latency_ms: float,
    ) -> dict[str, Any]:
        return self.trust_runtime.build_trust_layer(
            question=question,
            analysis_type=analysis_type,
            sql=sql,
            row_count=row_count,
            visualized_row_count=visualized_row_count,
            chart_config=chart_config,
            profile=profile,
            latency_ms=latency_ms,
        )

    def _render_chart_payload(
        self,
        query_data: list[dict[str, Any]],
        chart_config: dict[str, Any],
        analysis_type: str,
        sprint_mode: bool,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        chart_options = self.build_chart_options(
            data=query_data,
            base_config=chart_config,
            analysis_type=analysis_type,
        )
        chart_data = self.optimize_data_for_chart(query_data, chart_options[0])
        if sprint_mode:
            chart_data = self.chart_runtime.sample_evenly(chart_data, 120)
        return chart_options, chart_data

    def _run_single_pass_analysis(
        self,
        session_id: str,
        session_info: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, str]],
        sprint_mode: bool,
    ) -> dict[str, Any]:
        ai_response = self.ai_analyst.analyze_question(
            question=question,
            schema=session_info["schema"],
            table_name=session_info["table_name"],
            profile=session_info.get("profile"),
            conversation_history=conversation_history,
        )

        df = self.data_service.execute_query(
            session_id=session_id,
            sql=ai_response["sql"],
            max_rows=SPRINT_QUERY_LIMIT if sprint_mode else DEFAULT_QUERY_LIMIT,
        )
        query_data = jsonable_encoder(df.to_dict("records"))

        chart_options, chart_data = self._render_chart_payload(
            query_data=query_data,
            chart_config=ai_response["chart_config"],
            analysis_type=ai_response.get("analysis_type", "other"),
            sprint_mode=sprint_mode,
        )

        return {
            "question": question,
            "insight": ai_response["insight"] if query_data else "No data found matching your query.",
            "chart_config": chart_options[0],
            "chart_options": chart_options,
            "data": chart_data,
            "sql": ai_response["sql"],
            "row_count": len(query_data),
            "visualized_row_count": len(chart_data),
            "analysis_type": ai_response.get("analysis_type", "other"),
            "follow_up_questions": ai_response.get("follow_up_questions", []),
            "exploration": None,
        }

    def _run_multi_step_exploration(
        self,
        session_id: str,
        session_info: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, str]],
    ) -> dict[str, Any]:
        plan = self.ai_analyst.plan_exploration(
            question=question,
            schema=session_info["schema"],
            table_name=session_info["table_name"],
            profile=session_info.get("profile"),
            conversation_history=conversation_history,
            max_probes=MAX_EXPLORATION_PROBES,
        )

        executed_probes: list[dict[str, Any]] = []
        for probe in plan["probes"]:
            try:
                df = self.data_service.execute_query(
                    session_id=session_id,
                    sql=probe["sql"],
                    max_rows=PROBE_QUERY_LIMIT,
                )
            except Exception as exc:
                raise ValueError(f"Exploration probe '{probe['probe_id']}' failed: {exc}") from exc

            query_data = jsonable_encoder(df.to_dict("records"))
            chart_options, chart_data = self._render_chart_payload(
                query_data=query_data,
                chart_config=probe["chart_hint"],
                analysis_type=probe["analysis_type"],
                sprint_mode=False,
            )

            executed_probes.append(
                {
                    "probe_id": probe["probe_id"],
                    "question": probe["question"],
                    "analysis_type": probe["analysis_type"],
                    "sql": probe["sql"],
                    "rationale": probe["rationale"],
                    "row_count": len(query_data),
                    "query_data": query_data,
                    "chart_options": chart_options,
                    "chart_data": chart_data,
                }
            )

        synthesis_input = [
            {
                "probe_id": probe["probe_id"],
                "question": probe["question"],
                "analysis_type": probe["analysis_type"],
                "sql": probe["sql"],
                "rationale": probe["rationale"],
                "row_count": probe["row_count"],
                "columns": list(probe["query_data"][0].keys()) if probe["query_data"] else [],
                "sample_rows": probe["query_data"][:8],
            }
            for probe in executed_probes
        ]

        synthesis = self.ai_analyst.synthesize_exploration(
            question=question,
            exploration_goal=plan["analysis_goal"],
            executed_probes=synthesis_input,
        )

        primary_probe_id = synthesis["primary_probe_id"]
        primary_probe = next((probe for probe in executed_probes if probe["probe_id"] == primary_probe_id), None)
        if not primary_probe:
            raise ValueError("LLM synthesis selected an unknown primary probe.")

        chart_options, chart_data = self._render_chart_payload(
            query_data=primary_probe["query_data"],
            chart_config=synthesis["chart_config"],
            analysis_type=synthesis["analysis_type"],
            sprint_mode=False,
        )

        exploration = {
            "analysis_goal": plan["analysis_goal"],
            "primary_probe_id": primary_probe_id,
            "probes": [
                {
                    "probe_id": probe["probe_id"],
                    "question": probe["question"],
                    "analysis_type": probe["analysis_type"],
                    "rationale": probe["rationale"],
                    "sql": probe["sql"],
                    "row_count": probe["row_count"],
                }
                for probe in executed_probes
            ],
        }

        return {
            "question": question,
            "insight": synthesis["insight"],
            "chart_config": chart_options[0],
            "chart_options": chart_options,
            "data": chart_data,
            "sql": primary_probe["sql"],
            "row_count": primary_probe["row_count"],
            "visualized_row_count": len(chart_data),
            "analysis_type": synthesis["analysis_type"],
            "follow_up_questions": synthesis.get("follow_up_questions", []),
            "exploration": exploration,
            "synthesis_limitations": synthesis.get("limitations", []),
        }

    def run_analysis(
        self,
        session_id: str,
        session_info: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        sprint_mode: bool = False,
    ) -> dict[str, Any]:
        started_at = datetime.utcnow()
        history = conversation_history or []

        if sprint_mode:
            result = self._run_single_pass_analysis(
                session_id=session_id,
                session_info=session_info,
                question=question,
                conversation_history=history,
                sprint_mode=True,
            )
        else:
            result = self._run_multi_step_exploration(
                session_id=session_id,
                session_info=session_info,
                question=question,
                conversation_history=history,
            )

        latency_ms = (datetime.utcnow() - started_at).total_seconds() * 1000
        trust = self.build_trust_layer(
            question=question,
            analysis_type=result.get("analysis_type", "other"),
            sql=result["sql"],
            row_count=result["row_count"],
            visualized_row_count=result["visualized_row_count"],
            chart_config=result["chart_config"],
            profile=session_info.get("profile"),
            latency_ms=latency_ms,
        )

        if result.get("exploration"):
            provenance = trust.setdefault("provenance", {})
            provenance["exploration_probe_count"] = len(result["exploration"]["probes"])
            provenance["exploration_primary_probe_id"] = result["exploration"]["primary_probe_id"]
            provenance["exploration_probes"] = [
                {
                    "probe_id": probe["probe_id"],
                    "question": probe["question"],
                    "sql": probe["sql"],
                    "row_count": probe["row_count"],
                }
                for probe in result["exploration"]["probes"]
            ]

            synthesis_limitations = result.pop("synthesis_limitations", [])
            if isinstance(synthesis_limitations, list) and synthesis_limitations:
                base_limitations = trust.get("limitations", [])
                if not isinstance(base_limitations, list):
                    base_limitations = []
                for item in synthesis_limitations:
                    if isinstance(item, str) and item not in base_limitations:
                        base_limitations.append(item)
                trust["limitations"] = base_limitations[:8]

        result["trust"] = trust
        return result

    def build_causal_lab_result(
        self,
        data_frame: pd.DataFrame,
        target_metric: str,
        max_drivers: int,
    ) -> dict[str, Any]:
        return self.causal_runtime.build_causal_lab_result(
            data_frame=data_frame,
            target_metric=target_metric,
            max_drivers=max_drivers,
        )

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        return self.action_runtime.execute_action(action)
