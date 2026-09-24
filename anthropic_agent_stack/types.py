"""Common types and data structures across the Anthropic Agent Engineering Stack.

The safety enums (``DecisionVerdict`` / ``DecisionTier``) are defined once in
``claude_auto_mode.types`` — the canonical policy layer — and re-exported here
so the integrated stack and the standalone layer share a single definition.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional

from claude_auto_mode.types import DecisionVerdict, DecisionTier  # noqa: F401  (canonical re-export)


class WorkflowPattern(str, Enum):
    PROMPT_CHAINING = "Prompt Chaining"
    ROUTING = "Routing"
    PARALLELIZATION_SECTIONING = "Parallelization (Sectioning)"
    PARALLELIZATION_VOTING = "Parallelization (Voting)"
    ORCHESTRATOR_WORKERS = "Orchestrator-Workers"
    EVALUATOR_OPTIMIZER = "Evaluator-Optimizer"
    AUTONOMOUS_AGENT = "Autonomous Agent Loop"


@dataclass
class ToolDefinition:
    server: str
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    code_signature: str


@dataclass
class ToolExecutionPayload:
    server: str
    tool_name: str
    arguments: Dict[str, Any]
    code_snippet: Optional[str] = None


@dataclass
class TaskLock:
    task_id: str
    agent_id: str
    file_path: str
    acquired_at: float
    status: str = "LOCKED"  # LOCKED, COMPLETED, CONFLICT, RELEASED


@dataclass
class OracleTestResult:
    test_id: str
    input_file: str
    oracle_passed: bool
    agent_passed: bool
    is_regression: bool
    diagnostic_diff: Optional[str] = None


@dataclass
class AutoModeEvaluation:
    tier: DecisionTier
    verdict: DecisionVerdict
    stage1_verdict: Optional[DecisionVerdict] = None
    stage2_reasoning: Optional[str] = None
    prompt_cache_hit: bool = False
    consecutive_denials: int = 0
    total_denials: int = 0
    escalated_to_human: bool = False
    reason: str = ""
    retry_guidance: Optional[str] = None
