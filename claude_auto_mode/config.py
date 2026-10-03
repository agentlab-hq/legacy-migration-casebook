"""JSON configuration loader for the Auto Mode policy CLI."""

import json
from pathlib import Path
from typing import Any, Dict

from .policy_engine import PolicyConfig


_POLICY_FIELDS = {
    "trusted_git_orgs",
    "trusted_domains",
    "trusted_cloud_buckets",
    "current_working_branch",
}


def load_runtime_config(path: str) -> Dict[str, Any]:
    """Load and validate the JSON configuration used by the policy CLI."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read config file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config is not valid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("Config root must be a JSON object.")

    project_root = data.get("project_root", "/project")
    if not isinstance(project_root, str) or not project_root.strip():
        raise ValueError("'project_root' must be a non-empty string.")

    custom_allows = data.get("user_custom_allows", [])
    if not isinstance(custom_allows, list) or not all(isinstance(item, str) for item in custom_allows):
        raise ValueError("'user_custom_allows' must be a list of strings.")

    policy_data = data.get("policy", {})
    if not isinstance(policy_data, dict):
        raise ValueError("'policy' must be an object.")
    unknown_fields = set(policy_data) - _POLICY_FIELDS
    if unknown_fields:
        raise ValueError(f"Unknown policy fields: {', '.join(sorted(unknown_fields))}.")
    for field in ("trusted_git_orgs", "trusted_domains", "trusted_cloud_buckets"):
        if field in policy_data and (
            not isinstance(policy_data[field], list)
            or not all(isinstance(item, str) for item in policy_data[field])
        ):
            raise ValueError(f"'policy.{field}' must be a list of strings.")
    if "current_working_branch" in policy_data and not isinstance(
        policy_data["current_working_branch"], str
    ):
        raise ValueError("'policy.current_working_branch' must be a string.")

    audit_log = data.get("audit_log")
    if audit_log is not None and (not isinstance(audit_log, str) or not audit_log.strip()):
        raise ValueError("'audit_log' must be a non-empty string when provided.")

    return {
        "project_root": project_root,
        "user_custom_allows": custom_allows,
        "policy_config": PolicyConfig(**policy_data),
        "audit_log": audit_log,
    }
