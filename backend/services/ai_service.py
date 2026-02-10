import json
import logging
import os
from typing import Any, Dict, List

import openai
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

CHART_TYPES = {"line", "bar", "scatter", "pie", "area"}
CHART_TYPE_ALIASES = {
    "lines": "line",
    "time_series": "line",
    "timeseries": "line",
    "column": "bar",
    "columns": "bar",
    "histogram": "bar",
    "stacked_bar": "bar",
    "stacked_column": "bar",
    "dot": "scatter",
    "bubble": "scatter",
    "donut": "pie",
}
ANALYSIS_TYPES = {"trend", "correlation", "comparison", "distribution", "overview", "other"}


class AIAnalystService:
    """Service for generating SQL-driven analytics workflows from natural language."""

    def __init__(self):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for AI analytics.")
        self.client = openai.OpenAI(api_key=api_key)

    def _format_schema_for_prompt(self, schema: List[Dict[str, Any]]) -> str:
        lines = []
        for col in schema:
            col_name = col.get("column_name", "unknown")
            col_type = col.get("column_type", "unknown")
            lines.append(f"  - {col_name} ({col_type})")
        return "\n".join(lines)

    def _format_history_for_prompt(self, conversation_history: List[Dict[str, str]]) -> str:
        if not conversation_history:
            return "No previous context."

        turns = conversation_history[-6:]
        formatted = []
        for turn in turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "").strip().replace("\n", " ")
            if not content:
                continue
            formatted.append(f"- {role}: {content[:500]}")
        return "\n".join(formatted) if formatted else "No previous context."

    def _normalize_chart_config(self, chart_config: Any, field_name: str = "chart_config") -> Dict[str, Any]:
        if not isinstance(chart_config, dict):
            raise ValueError(f"AI response missing valid '{field_name}' object")

        chart_type_raw = chart_config.get("type")
        if not isinstance(chart_type_raw, str) or not chart_type_raw.strip():
            raise ValueError(f"AI response missing valid {field_name}.type")

        chart_type = chart_type_raw.strip().lower()
        chart_type = CHART_TYPE_ALIASES.get(chart_type, chart_type)
        if chart_type not in CHART_TYPES:
            raise ValueError(f"AI response has unsupported {field_name}.type")

        x_key = chart_config.get("xKey")
        y_key = chart_config.get("yKey")
        if not isinstance(x_key, str) or not x_key.strip():
            raise ValueError(f"AI response missing valid {field_name}.xKey")
        if not isinstance(y_key, str) or not y_key.strip():
            raise ValueError(f"AI response missing valid {field_name}.yKey")

        normalized = {
            "type": chart_type,
            "xKey": x_key.strip(),
            "yKey": y_key.strip(),
        }
        group_by = chart_config.get("groupBy")
        if isinstance(group_by, str) and group_by.strip():
            normalized["groupBy"] = group_by.strip()
        return normalized

    def _normalize_follow_up_questions(self, follow_ups: Any, require_non_empty: bool = True) -> List[str]:
        if not isinstance(follow_ups, list):
            raise ValueError("AI response missing valid follow_up_questions list")

        cleaned = [q.strip() for q in follow_ups if isinstance(q, str) and q.strip()][:3]
        if require_non_empty and not cleaned:
            raise ValueError("AI response follow_up_questions is empty")
        return cleaned

    def _normalize_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        sql = result.get("sql")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("AI response missing valid 'sql' field")

        analysis_type = result.get("analysis_type")
        if not isinstance(analysis_type, str) or analysis_type.strip().lower() not in ANALYSIS_TYPES:
            raise ValueError("AI response missing valid analysis_type")

        insight = result.get("insight")
        if not isinstance(insight, str) or not insight.strip():
            raise ValueError("AI response missing valid insight")

        return {
            "sql": sql.strip(),
            "insight": insight.strip(),
            "analysis_type": analysis_type.strip().lower(),
            "chart_config": self._normalize_chart_config(result.get("chart_config")),
            "follow_up_questions": self._normalize_follow_up_questions(result.get("follow_up_questions")),
        }

    def _normalize_exploration_plan(self, result: Dict[str, Any], max_probes: int) -> Dict[str, Any]:
        analysis_goal = result.get("analysis_goal")
        if not isinstance(analysis_goal, str) or not analysis_goal.strip():
            raise ValueError("LLM exploration output missing analysis_goal.")

        probes = result.get("probes")
        if not isinstance(probes, list):
            raise ValueError("LLM exploration output missing probes list.")
        if len(probes) < 2 or len(probes) > max_probes:
            raise ValueError(f"LLM exploration must return between 2 and {max_probes} probes.")

        normalized: List[Dict[str, Any]] = []
        probe_ids: set[str] = set()
        sql_signatures: set[str] = set()

        for index, probe in enumerate(probes):
            if not isinstance(probe, dict):
                raise ValueError(f"LLM exploration probe {index + 1} is invalid.")

            probe_id = probe.get("probe_id")
            probe_question = probe.get("question")
            probe_sql = probe.get("sql")
            analysis_type = probe.get("analysis_type")
            rationale = probe.get("rationale")

            if not isinstance(probe_id, str) or not probe_id.strip():
                raise ValueError(f"LLM exploration probe {index + 1} missing probe_id.")
            probe_id = probe_id.strip()
            if probe_id in probe_ids:
                raise ValueError("LLM exploration contains duplicate probe_id values.")

            if not isinstance(probe_question, str) or not probe_question.strip():
                raise ValueError(f"LLM exploration probe {probe_id} missing question.")
            if not isinstance(probe_sql, str) or not probe_sql.strip():
                raise ValueError(f"LLM exploration probe {probe_id} missing sql.")
            if not isinstance(analysis_type, str) or analysis_type.strip().lower() not in ANALYSIS_TYPES:
                raise ValueError(f"LLM exploration probe {probe_id} has invalid analysis_type.")
            if not isinstance(rationale, str) or not rationale.strip():
                raise ValueError(f"LLM exploration probe {probe_id} missing rationale.")

            sql_signature = probe_sql.strip().lower()
            if sql_signature in sql_signatures:
                raise ValueError("LLM exploration contains duplicate SQL probes.")

            normalized.append(
                {
                    "probe_id": probe_id,
                    "question": probe_question.strip(),
                    "analysis_type": analysis_type.strip().lower(),
                    "sql": probe_sql.strip(),
                    "chart_hint": self._normalize_chart_config(
                        probe.get("chart_hint"),
                        field_name=f"probes[{probe_id}].chart_hint",
                    ),
                    "rationale": rationale.strip(),
                }
            )
            probe_ids.add(probe_id)
            sql_signatures.add(sql_signature)

        return {
            "analysis_goal": analysis_goal.strip(),
            "probes": normalized,
        }

    def _normalize_exploration_synthesis(
        self,
        result: Dict[str, Any],
        valid_probe_ids: set[str],
    ) -> Dict[str, Any]:
        analysis_type = result.get("analysis_type")
        if not isinstance(analysis_type, str) or analysis_type.strip().lower() not in ANALYSIS_TYPES:
            raise ValueError("LLM synthesis output missing valid analysis_type.")

        primary_probe_id = result.get("primary_probe_id")
        if not isinstance(primary_probe_id, str) or primary_probe_id.strip() not in valid_probe_ids:
            raise ValueError("LLM synthesis output has invalid primary_probe_id.")

        insight = result.get("insight")
        if not isinstance(insight, str) or not insight.strip():
            raise ValueError("LLM synthesis output missing insight.")

        limitations_raw = result.get("limitations", [])
        if not isinstance(limitations_raw, list):
            raise ValueError("LLM synthesis output has invalid limitations list.")
        limitations = [item.strip() for item in limitations_raw if isinstance(item, str) and item.strip()][:5]

        return {
            "analysis_type": analysis_type.strip().lower(),
            "primary_probe_id": primary_probe_id.strip(),
            "insight": insight.strip(),
            "chart_config": self._normalize_chart_config(result.get("chart_config")),
            "follow_up_questions": self._normalize_follow_up_questions(result.get("follow_up_questions")),
            "limitations": limitations,
        }

    def _call_json_model(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty JSON content.")
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model JSON output: {e}")
            raise ValueError("LLM returned invalid JSON output.") from e
        except Exception as e:
            logger.error(f"Model JSON call failed: {e}")
            raise ValueError(f"LLM request failed: {str(e)}") from e

    def analyze_question(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "uploaded_data",
        profile: Dict[str, Any] | None = None,
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        schema_str = self._format_schema_for_prompt(schema)
        history_str = self._format_history_for_prompt(conversation_history or [])
        profile_json = json.dumps(profile or {}, indent=2, default=str)

        system_prompt = f"""You are a principal data analyst assistant.

You have access to a table named "{table_name}" with the following schema:
{schema_str}

Dataset profile:
{profile_json}

Recent conversation context:
{history_str}

Your task is to:
1. Generate a valid SQL SELECT query to answer the user's question
2. Classify the analysis intent (trend, correlation, comparison, distribution, overview, other)
3. Provide a brief insight about what the data shows or will show
4. Suggest the best chart type and configuration for visualizing the results
5. Suggest up to 3 follow-up questions to continue exploration

Rules:
- Only single SELECT/CTE queries are allowed (no INSERT/UPDATE/DELETE/DROP)
- Use appropriate aggregations (SUM, AVG, COUNT, etc.) for analytical questions
- Keep SQL compatible with DuckDB
- Always include aliases for derived columns
- For time series, ensure proper date formatting and ordering
- Column names in chart_config must match the SELECT clause output columns
- Choose chart types based on data shape; do not default to bar unless it is clearly best.
- Prefer scatter for numeric-vs-numeric correlation questions and line/area for time trends.

Chart types available:
- "line" - for trends over time
- "bar" - for comparisons across categories
- "scatter" - for correlations between two variables
- "pie" - for part-to-whole relationships (use sparingly)
- "area" - for cumulative trends

Return your response as valid JSON only."""

        user_prompt = f"""User Question: {question}

Return JSON in this exact format:
{{
  "analysis_type": "trend|correlation|comparison|distribution|overview|other",
  "sql": "SELECT ... FROM {table_name} ...",
  "insight": "Brief explanation of what this query reveals",
  "chart_config": {{
    "type": "line|bar|scatter|pie|area",
    "xKey": "column_name_from_select",
    "yKey": "column_name_from_select",
    "groupBy": "optional_column_for_multiple_series"
  }},
  "follow_up_questions": [
    "Next analytical question 1",
    "Next analytical question 2",
    "Next analytical question 3"
  ]
}}"""

        try:
            logger.info(f"Generating SQL for question: {question[:100]}...")
            result = self._call_json_model(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            normalized = self._normalize_response(result)
            logger.info(f"Generated SQL: {normalized['sql'][:100]}...")
            return normalized
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise ValueError(f"LLM analysis failed: {str(e)}")

    def plan_exploration(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "uploaded_data",
        profile: Dict[str, Any] | None = None,
        conversation_history: List[Dict[str, str]] | None = None,
        max_probes: int = 3,
    ) -> Dict[str, Any]:
        if max_probes < 2:
            raise ValueError("max_probes must be at least 2.")

        schema_str = self._format_schema_for_prompt(schema)
        history_str = self._format_history_for_prompt(conversation_history or [])
        profile_json = json.dumps(profile or {}, indent=2, default=str)

        system_prompt = f"""You are a principal analytics investigator.
Your job is to design a short multi-step exploration plan to answer a user question.

Table name: {table_name}
Schema:
{schema_str}

Dataset profile:
{profile_json}

Conversation context:
{history_str}

You must return between 2 and {max_probes} probes.
Each probe must include:
- probe_id
- question
- analysis_type
- sql
- chart_hint
- rationale

Rules:
- SQL must be single SELECT/CTE and DuckDB compatible
- Use different probes to triangulate the answer (trend, segmentation, correlation, outliers as appropriate)
- SQL statements must not be duplicates
- chart_hint columns must match projected SQL columns
- For broad/overview questions, include:
  - one KPI aggregate probe (single-row is allowed),
  - one segmented probe with GROUP BY (multi-row),
  - one trend or distribution probe (multi-row).
- Do not make all probes single-row aggregates.
- Prefer probes that return interpretable evidence (not only a single summary row).
- Return valid JSON only
"""

        user_prompt = f"""User question: {question}

Return JSON in this exact shape:
{{
  "analysis_goal": "short objective",
  "probes": [
    {{
      "probe_id": "probe_1",
      "question": "what this probe checks",
      "analysis_type": "trend|correlation|comparison|distribution|overview|other",
      "sql": "SELECT ... FROM {table_name} ...",
      "chart_hint": {{
        "type": "line|bar|scatter|pie|area",
        "xKey": "column_from_select",
        "yKey": "column_from_select",
        "groupBy": "optional"
      }},
      "rationale": "why this probe helps"
    }}
  ]
}}"""

        result = self._call_json_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return self._normalize_exploration_plan(result, max_probes=max_probes)

    def synthesize_exploration(
        self,
        question: str,
        exploration_goal: str,
        executed_probes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not executed_probes:
            raise ValueError("No executed probes were provided for synthesis.")

        valid_probe_ids = {
            str(item.get("probe_id", "")).strip() for item in executed_probes if str(item.get("probe_id", "")).strip()
        }
        if not valid_probe_ids:
            raise ValueError("Executed probes missing probe_id values.")

        probes_json = json.dumps(executed_probes, indent=2, default=str)

        system_prompt = """You are a principal data analyst.
Synthesize multiple probe results into one clear answer.

Rules:
- Choose exactly one primary_probe_id from the provided probe_ids
- Select the probe with strongest evidence density as primary when possible
  (prefer richer multi-row probes over single-row aggregates unless all probes are sparse)
- Insight must reference concrete evidence from probe results
- Keep insight concise but specific
- Include up to 3 precise follow-up questions
- Add limitations when evidence is weak or incomplete
- Return valid JSON only
"""

        user_prompt = f"""User question: {question}
Exploration goal: {exploration_goal}
Executed probe summaries:
{probes_json}

Each probe summary may include:
- columns
- sample_rows (random, limited)
- chart_sample (random, limited)
- stats (numeric and categorical aggregates)
Use these compact summaries as evidence, not exhaustive raw data.

Return JSON in this exact shape:
{{
  "analysis_type": "trend|correlation|comparison|distribution|overview|other",
  "primary_probe_id": "one_of_{sorted(valid_probe_ids)}",
  "insight": "final answer grounded in the probes",
  "chart_config": {{
    "type": "line|bar|scatter|pie|area",
    "xKey": "column_from_primary_probe",
    "yKey": "column_from_primary_probe",
    "groupBy": "optional"
  }},
  "follow_up_questions": [
    "question 1",
    "question 2",
    "question 3"
  ],
  "limitations": [
    "optional limitation 1",
    "optional limitation 2"
  ]
}}"""

        result = self._call_json_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return self._normalize_exploration_synthesis(result, valid_probe_ids=valid_probe_ids)

    def generate_insight_from_data(
        self,
        question: str,
        data: List[Dict[str, Any]],
        sql_query: str,
    ) -> str:
        if not data:
            return "No rows were returned for this query."

        sample_data = data[:10]
        prompt = f"""Based on this SQL query and results, provide a brief insight.

User Question: {question}
SQL Query: {sql_query}

Sample Results (first {len(sample_data)} rows):
{json.dumps(sample_data, indent=2, default=str)}

Provide a 1-2 sentence insight highlighting key findings or trends."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a data analyst. Provide concise insights."},
                    {"role": "user", "content": prompt},
                ],
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            raise ValueError(f"LLM insight generation failed: {str(e)}")

    def generate_hypotheses(
        self,
        schema: List[Dict[str, Any]],
        profile: Dict[str, Any] | None = None,
        table_name: str = "uploaded_data",
        count: int = 20,
    ) -> Dict[str, Any]:
        if count < 5:
            raise ValueError("Hypothesis count must be at least 5.")

        schema_str = self._format_schema_for_prompt(schema)
        profile_json = json.dumps(profile or {}, indent=2, default=str)

        system_prompt = f"""You are a principal analytics strategist.
Generate exactly {count} high-value, concrete analysis questions for exploratory data analysis.

Table name: {table_name}
Schema:
{schema_str}

Dataset profile:
{profile_json}

Coverage requirements:
- Include trend-break questions
- Include segment delta questions
- Include correlation/relationship questions
- Include outlier/anomaly questions
- Include operational/business actionability

Rules:
- Questions must be specific and answerable with SQL on this dataset
- No duplicates or near-duplicates
- Keep each question under 20 words
- Return valid JSON only
"""

        user_prompt = f"""Return JSON in this exact shape:
{{
  "hypotheses": ["q1", "q2", "... exactly {count} total ..."],
  "rationale_summary": "1-2 sentence summary"
}}"""

        result = self._call_json_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        hypotheses = result.get("hypotheses")
        if not isinstance(hypotheses, list):
            raise ValueError("LLM hypothesis output missing hypotheses list.")

        cleaned = []
        seen = set()
        for item in hypotheses:
            if not isinstance(item, str):
                continue
            candidate = item.strip()
            if not candidate:
                continue
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(candidate)

        if len(cleaned) != count:
            raise ValueError(f"LLM must return exactly {count} unique hypotheses.")

        rationale = result.get("rationale_summary")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("LLM hypothesis output missing rationale_summary.")

        return {
            "hypotheses": cleaned,
            "rationale_summary": rationale.strip(),
        }

    def draft_actions(
        self,
        question: str,
        insight: str,
        sql: str,
        analysis_type: str,
        trust: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        trust_json = json.dumps(trust, indent=2, default=str)
        system_prompt = """You are an analytics operations agent.
Given an analysis result, draft concrete next actions.
Return exactly 4 actions with these required types:
- sql_view
- dbt_model
- jira_ticket
- slack_summary

Rules:
- Be specific and actionable.
- Use realistic payload fields for each type.
- Return valid JSON only.
"""
        user_prompt = f"""Analysis context:
Question: {question}
Insight: {insight}
Analysis type: {analysis_type}
SQL used:
{sql}
Trust layer:
{trust_json}

Return JSON in this exact shape:
{{
  "actions": [
    {{
      "type": "sql_view|dbt_model|jira_ticket|slack_summary",
      "title": "Short title",
      "description": "What and why",
      "payload": {{}}
    }}
  ]
}}
"""

        result = self._call_json_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        actions = result.get("actions")
        if not isinstance(actions, list):
            raise ValueError("LLM action output missing actions list.")

        allowed_types = {"sql_view", "dbt_model", "jira_ticket", "slack_summary"}
        normalized: List[Dict[str, Any]] = []
        seen_types: set[str] = set()

        for action in actions:
            if not isinstance(action, dict):
                continue
            action_type = action.get("type")
            title = action.get("title")
            description = action.get("description")
            payload = action.get("payload")
            if action_type not in allowed_types:
                continue
            if not isinstance(title, str) or not title.strip():
                continue
            if not isinstance(description, str) or not description.strip():
                continue
            if not isinstance(payload, dict):
                continue
            seen_types.add(action_type)
            normalized.append(
                {
                    "type": action_type,
                    "title": title.strip(),
                    "description": description.strip(),
                    "payload": payload,
                }
            )

        if seen_types != allowed_types:
            raise ValueError("LLM actions must include sql_view, dbt_model, jira_ticket, and slack_summary.")

        return normalized
