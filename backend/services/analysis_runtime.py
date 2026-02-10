from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi.encoders import jsonable_encoder

from services.ai_service import AIAnalystService
from services.data_service import DataService
from services.runtime import ActionRuntime, CausalRuntime, ChartRuntime, TrustRuntime


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

    def run_analysis(
        self,
        session_id: str,
        session_info: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        sprint_mode: bool = False,
    ) -> dict[str, Any]:
        started_at = datetime.utcnow()

        ai_response = self.ai_analyst.analyze_question(
            question=question,
            schema=session_info["schema"],
            table_name=session_info["table_name"],
            profile=session_info.get("profile"),
            conversation_history=conversation_history or [],
        )

        df = self.data_service.execute_query(
            session_id=session_id,
            sql=ai_response["sql"],
            max_rows=2000 if sprint_mode else 1200,
        )

        query_data = jsonable_encoder(df.to_dict("records"))
        chart_options = self.build_chart_options(
            data=query_data,
            base_config=ai_response["chart_config"],
            analysis_type=ai_response.get("analysis_type", "other"),
        )
        chart_data = self.optimize_data_for_chart(query_data, chart_options[0])
        if sprint_mode:
            chart_data = self.chart_runtime.sample_evenly(chart_data, 120)

        insight = ai_response["insight"] if query_data else "No data found matching your query."
        latency_ms = (datetime.utcnow() - started_at).total_seconds() * 1000
        trust = self.build_trust_layer(
            question=question,
            analysis_type=ai_response.get("analysis_type", "other"),
            sql=ai_response["sql"],
            row_count=len(query_data),
            visualized_row_count=len(chart_data),
            chart_config=chart_options[0],
            profile=session_info.get("profile"),
            latency_ms=latency_ms,
        )

        return {
            "question": question,
            "insight": insight,
            "chart_config": chart_options[0],
            "chart_options": chart_options,
            "data": chart_data,
            "sql": ai_response["sql"],
            "row_count": len(query_data),
            "visualized_row_count": len(chart_data),
            "analysis_type": ai_response.get("analysis_type", "other"),
            "follow_up_questions": ai_response.get("follow_up_questions", []),
            "trust": trust,
        }

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
