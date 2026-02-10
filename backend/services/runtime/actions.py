from __future__ import annotations

from typing import Any


class ActionRuntime:
    @staticmethod
    def _slugify(value: str) -> str:
        safe = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
        safe = "_".join(filter(None, safe.split("_")))
        return safe or "artifact"

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        action_type = action["type"]
        payload = action.get("payload", {})

        if action_type == "sql_view":
            view_name = payload.get("view_name") or f"vw_{self._slugify(action['title'])}"
            sql_query = payload.get("sql") or payload.get("query") or "-- Provide SELECT query here"
            statement = f"CREATE OR REPLACE VIEW {view_name} AS\\n{sql_query};"
            return {"mode": "dry_run", "artifact_type": "sql", "artifact": statement}

        if action_type == "dbt_model":
            model_name = payload.get("model_name") or self._slugify(action["title"])
            model_sql = payload.get("sql") or payload.get("model_sql") or "-- dbt model SQL"
            model_path = f"models/{model_name}.sql"
            return {"mode": "dry_run", "artifact_type": "dbt_model", "path": model_path, "artifact": model_sql}

        if action_type == "jira_ticket":
            ticket = {
                "project": payload.get("project", "DATA"),
                "summary": payload.get("summary") or action["title"],
                "description": payload.get("description") or action["description"],
                "labels": payload.get("labels", ["analytics", "auto-generated"]),
            }
            return {"mode": "dry_run", "artifact_type": "jira_payload", "artifact": ticket}

        if action_type == "slack_summary":
            message = payload.get("message") or f"*{action['title']}*\\n{action['description']}"
            return {
                "mode": "dry_run",
                "artifact_type": "slack_message",
                "artifact": {"channel": payload.get("channel", "#data-alerts"), "message": message},
            }

        raise ValueError(f"Unsupported action type '{action_type}'.")
