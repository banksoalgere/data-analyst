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


class AIAnalystService:
    """Service for generating SQL queries and chart configs from natural language"""

    def __init__(self):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for AI analytics.")
        self.client = openai.OpenAI(api_key=api_key)

    def _format_schema_for_prompt(self, schema: List[Dict[str, Any]]) -> str:
        """Convert schema to readable format for AI"""
        lines = []
        for col in schema:
            col_name = col.get('column_name', 'unknown')
            col_type = col.get('column_type', 'unknown')
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

    def _normalize_response(
        self,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        sql = result.get("sql")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("AI response missing valid 'sql' field")

        chart_config = result.get("chart_config")
        if not isinstance(chart_config, dict):
            raise ValueError("AI response missing valid 'chart_config' object")

        chart_type = chart_config.get("type")
        if chart_type not in {"line", "bar", "scatter", "pie", "area"}:
            raise ValueError("AI response has unsupported chart_config.type")

        x_key = chart_config.get("xKey")
        y_key = chart_config.get("yKey")
        if not isinstance(x_key, str) or not x_key.strip():
            raise ValueError("AI response missing valid chart_config.xKey")
        if not isinstance(y_key, str) or not y_key.strip():
            raise ValueError("AI response missing valid chart_config.yKey")

        follow_ups = result.get("follow_up_questions")
        if not isinstance(follow_ups, list):
            raise ValueError("AI response missing valid follow_up_questions list")
        follow_ups = [q.strip() for q in follow_ups if isinstance(q, str) and q.strip()][:3]
        if not follow_ups:
            raise ValueError("AI response follow_up_questions is empty")

        analysis_type = result.get("analysis_type")
        if not isinstance(analysis_type, str) or not analysis_type.strip():
            raise ValueError("AI response missing valid analysis_type")

        insight = result.get("insight")
        if not isinstance(insight, str) or not insight.strip():
            raise ValueError("AI response missing valid insight")

        return {
            "sql": sql.strip(),
            "insight": insight.strip(),
            "analysis_type": analysis_type.strip().lower(),
            "chart_config": chart_config,
            "follow_up_questions": follow_ups,
        }

    def analyze_question(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "uploaded_data",
        profile: Dict[str, Any] | None = None,
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """
        Generate SQL query and chart configuration from natural language

        Args:
            question: User's natural language question
            schema: Database schema
            table_name: Name of the table to query

        Returns:
            Dict with sql, insight, and chart_config
        """
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

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            normalized = self._normalize_response(result)
            logger.info(f"Generated SQL: {normalized['sql'][:100]}...")
            return normalized

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("LLM returned invalid JSON for analysis output.")
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise ValueError(f"LLM analysis failed: {str(e)}")

    def generate_insight_from_data(
        self,
        question: str,
        data: List[Dict[str, Any]],
        sql_query: str
    ) -> str:
        """
        Generate a natural language insight from query results

        Args:
            question: Original user question
            data: Query result data (first few rows)
            sql_query: The SQL query that was executed

        Returns:
            Natural language insight
        """
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data analyst. Provide concise insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            raise ValueError(f"LLM insight generation failed: {str(e)}")
