from __future__ import annotations

from datetime import datetime
import math
import random
from typing import Any, Callable
import uuid

import pandas as pd
from fastapi.encoders import jsonable_encoder

from services.ai_service import AIAnalystService
from services.data_service import DataService
from services.runtime import ActionRuntime, CausalRuntime, ChartRuntime, TrustRuntime

DEFAULT_QUERY_LIMIT = 1200
SPRINT_QUERY_LIMIT = 2000
PROBE_QUERY_LIMIT = 900
MAX_EXPLORATION_PROBES = 5
LLM_ROW_SAMPLE_LIMIT = 24
LLM_CHART_SAMPLE_LIMIT = 48
MIN_STRONG_PRIMARY_ROWS = 12


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

    @staticmethod
    def _random_sample_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        if limit <= 0 or not rows:
            return []
        if len(rows) <= limit:
            return rows

        sampled_indexes = sorted(random.sample(range(len(rows)), limit))
        return [rows[index] for index in sampled_indexes]

    @staticmethod
    def _to_safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(converted) or math.isinf(converted):
            return None
        return round(converted, 6)

    def _build_probe_stats(self, frame: pd.DataFrame) -> dict[str, Any]:
        if frame.empty:
            return {
                "column_count": len(frame.columns),
                "numeric_summary": {},
                "top_categories": {},
            }

        numeric_summary: dict[str, dict[str, float | None]] = {}
        numeric_columns = list(frame.select_dtypes(include="number").columns)
        for column in numeric_columns[:6]:
            numeric = pd.to_numeric(frame[column], errors="coerce").dropna()
            if numeric.empty:
                continue
            numeric_summary[column] = {
                "min": self._to_safe_float(numeric.min()),
                "p50": self._to_safe_float(numeric.median()),
                "mean": self._to_safe_float(numeric.mean()),
                "max": self._to_safe_float(numeric.max()),
            }

        top_categories: dict[str, list[dict[str, Any]]] = {}
        categorical_columns = [column for column in frame.columns if column not in numeric_columns]
        for column in categorical_columns[:3]:
            values = frame[column].dropna().astype(str)
            if values.empty:
                continue
            counts = values.value_counts().head(6)
            top_categories[column] = [
                {"value": key, "count": int(count)}
                for key, count in counts.items()
            ]

        return {
            "column_count": len(frame.columns),
            "numeric_summary": numeric_summary,
            "top_categories": top_categories,
        }

    def _build_probe_llm_sample(
        self,
        query_data: list[dict[str, Any]],
        chart_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        columns = list(query_data[0].keys()) if query_data else []
        return {
            "columns": columns,
            "sample_rows": self._random_sample_rows(query_data, LLM_ROW_SAMPLE_LIMIT),
            "chart_sample": self._random_sample_rows(chart_data, LLM_CHART_SAMPLE_LIMIT),
        }

    def _select_primary_probe(
        self,
        requested_probe_id: str,
        executed_probes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not executed_probes:
            raise ValueError("No executed probes are available.")

        by_id = {probe["probe_id"]: probe for probe in executed_probes}
        preferred = by_id.get(requested_probe_id)

        def evidence_score(probe: dict[str, Any]) -> float:
            row_count = int(probe.get("row_count") or 0)
            chart_rows = len(probe.get("chart_data") or [])
            chart_config = (probe.get("chart_options") or [{}])[0]
            x_key = chart_config.get("xKey") if isinstance(chart_config, dict) else None
            unique_x = 0
            if isinstance(x_key, str) and x_key:
                values = {
                    str(item.get(x_key))
                    for item in (probe.get("chart_data") or [])
                    if item.get(x_key) is not None
                }
                unique_x = len(values)

            score = min(row_count, 500) + min(chart_rows, 300) * 0.5 + min(unique_x, 120) * 1.5
            if row_count <= 2:
                score -= 160
            elif row_count < MIN_STRONG_PRIMARY_ROWS:
                score -= 60
            return score

        strongest = max(executed_probes, key=evidence_score)
        if preferred is None:
            return strongest

        preferred_score = evidence_score(preferred)
        strongest_score = evidence_score(strongest)
        preferred_rows = int(preferred.get("row_count") or 0)
        strongest_rows = int(strongest.get("row_count") or 0)

        if preferred_rows == 0 and strongest_rows > 0:
            return strongest
        if (
            preferred_rows < MIN_STRONG_PRIMARY_ROWS
            and strongest_rows >= MIN_STRONG_PRIMARY_ROWS
            and strongest_score >= preferred_score + 20
        ):
            return strongest
        return preferred

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
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid.uuid4())
        plan = self.ai_analyst.plan_exploration(
            question=question,
            schema=session_info["schema"],
            table_name=session_info["table_name"],
            profile=session_info.get("profile"),
            conversation_history=conversation_history,
            max_probes=MAX_EXPLORATION_PROBES,
        )
        if progress_callback:
            progress_callback(
                {
                    "phase": "plan_ready",
                    "analysis_goal": plan["analysis_goal"],
                    "probe_count": len(plan["probes"]),
                }
            )

        executed_probes: list[dict[str, Any]] = []
        for probe in plan["probes"]:
            if progress_callback:
                progress_callback(
                    {
                        "phase": "probe_started",
                        "probe_id": probe["probe_id"],
                        "question": probe["question"],
                        "analysis_type": probe["analysis_type"],
                    }
                )
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
                    "chart_config": chart_options[0] if chart_options else probe["chart_hint"],
                    "llm_sample": self._build_probe_llm_sample(query_data=query_data, chart_data=chart_data),
                    "stats": self._build_probe_stats(df),
                }
            )
            if progress_callback:
                progress_callback(
                    {
                        "phase": "probe_completed",
                        "probe_id": probe["probe_id"],
                        "row_count": len(query_data),
                        "analysis_type": probe["analysis_type"],
                    }
                )

        self.data_service.persist_analysis_artifacts(
            session_id=session_id,
            run_id=run_id,
            question=question,
            analysis_goal=plan["analysis_goal"],
            artifacts=[
                {
                    "probe_id": probe["probe_id"],
                    "question": probe["question"],
                    "analysis_type": probe["analysis_type"],
                    "rationale": probe["rationale"],
                    "sql": probe["sql"],
                    "row_count": probe["row_count"],
                    "chart_config": probe["chart_config"],
                    "graph_data": probe["chart_data"],
                    "llm_sample": probe["llm_sample"],
                    "stats": probe["stats"],
                }
                for probe in executed_probes
            ],
        )

        synthesis_input = self.data_service.load_analysis_artifact_summaries(
            session_id=session_id,
            run_id=run_id,
        )
        if not synthesis_input:
            synthesis_input = [
                {
                    "probe_id": probe["probe_id"],
                    "question": probe["question"],
                    "analysis_type": probe["analysis_type"],
                    "sql": probe["sql"],
                    "rationale": probe["rationale"],
                    "row_count": probe["row_count"],
                    "columns": probe["llm_sample"]["columns"],
                    "sample_rows": probe["llm_sample"]["sample_rows"],
                    "chart_sample": probe["llm_sample"]["chart_sample"],
                    "stats": probe["stats"],
                }
                for probe in executed_probes
            ]

        synthesis = self.ai_analyst.synthesize_exploration(
            question=question,
            exploration_goal=plan["analysis_goal"],
            executed_probes=synthesis_input,
        )

        requested_primary_probe_id = synthesis["primary_probe_id"]
        primary_probe = self._select_primary_probe(
            requested_probe_id=requested_primary_probe_id,
            executed_probes=executed_probes,
        )
        primary_probe_id = primary_probe["probe_id"]
        if progress_callback:
            progress_callback(
                {
                    "phase": "synthesis_completed",
                    "requested_primary_probe_id": requested_primary_probe_id,
                    "primary_probe_id": primary_probe_id,
                    "analysis_type": synthesis["analysis_type"],
                }
            )

        chart_options, chart_data = self._render_chart_payload(
            query_data=primary_probe["query_data"],
            chart_config=synthesis["chart_config"],
            analysis_type=synthesis["analysis_type"],
            sprint_mode=False,
        )

        synthesis_limitations = synthesis.get("limitations", [])
        if primary_probe_id != requested_primary_probe_id:
            switch_note = (
                f"Primary probe switched from {requested_primary_probe_id} to "
                f"{primary_probe_id} due to stronger evidence density."
            )
            if not isinstance(synthesis_limitations, list):
                synthesis_limitations = []
            if switch_note not in synthesis_limitations:
                synthesis_limitations.append(switch_note)

        exploration = {
            "analysis_goal": plan["analysis_goal"],
            "analysis_run_id": run_id,
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
            "synthesis_limitations": synthesis_limitations,
        }

    def run_analysis(
        self,
        session_id: str,
        session_info: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        sprint_mode: bool = False,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
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
                progress_callback=progress_callback,
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
