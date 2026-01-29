import openai
import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


class AIAnalystService:
    """Service for generating SQL queries and chart configs from natural language"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=api_key)

    def _format_schema_for_prompt(self, schema: List[Dict[str, Any]]) -> str:
        """Convert schema to readable format for AI"""
        lines = []
        for col in schema:
            col_name = col.get('column_name', 'unknown')
            col_type = col.get('column_type', 'unknown')
            lines.append(f"  - {col_name} ({col_type})")
        return "\n".join(lines)

    def analyze_question(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "uploaded_data"
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

        system_prompt = f"""You are a data analyst assistant specializing in SQL and data visualization.

You have access to a table named "{table_name}" with the following schema:
{schema_str}

Your task is to:
1. Generate a valid SQL SELECT query to answer the user's question
2. Provide a brief insight about what the data shows or will show
3. Suggest the best chart type and configuration for visualizing the results

Rules:
- Only SELECT queries are allowed (no INSERT/UPDATE/DELETE/DROP)
- Use appropriate aggregations (SUM, AVG, COUNT, etc.) for analytical questions
- Limit results to 1000 rows maximum
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
  "sql": "SELECT ... FROM {table_name} ...",
  "insight": "Brief explanation of what this query reveals",
  "chart_config": {{
    "type": "line|bar|scatter|pie|area",
    "xKey": "column_name_from_select",
    "yKey": "column_name_from_select",
    "groupBy": "optional_column_for_multiple_series"
  }}
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

            # Validate required fields
            if "sql" not in result:
                raise ValueError("AI response missing 'sql' field")
            if "insight" not in result:
                result["insight"] = "Analysis generated"
            if "chart_config" not in result:
                result["chart_config"] = {"type": "bar", "xKey": "", "yKey": ""}

            logger.info(f"Generated SQL: {result['sql'][:100]}...")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("AI returned invalid JSON response")
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise ValueError(f"Failed to generate SQL query: {str(e)}")

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
        # Limit data to first 10 rows for token efficiency
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
            return "Analysis complete - see chart for details"
