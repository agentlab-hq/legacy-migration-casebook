"""Common types and data structures across the Anthropic Agent Engineering Stack."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Callable


class WorkflowPattern(str, Enum):
    PROMPT_CHAINING = "Prompt Chaining"
    ROUTING = "Routing"
    PARALLELIZATION_SECTIONING = "Parallelization (Sectioning)"
    PARALLELIZATION_VOTING = "Parallelization (Voting)"
    ORCHESTRATOR_WORKERS = "Orchestrator-Workers"
    EVALUATOR_OPTIMIZER = "Evaluator-Optimizer"
    AUTONOMOUS_AGENT = "Autonomous Agent Loop"


class DecisionVerdict(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"


class DecisionTier(str, Enum):
    TIER_1_SAFE_ALLOWLIST = "Tier 1: Safe-Tool Allowlist"
    TIER_2_PROJECT_BOUNDARY = "Tier 2: In-Project File Operations"
    TIER_3_STAGE_1 = "Tier 3: Fast Single-Token Classifier"
    TIER_3_STAGE_2 = "Tier 3: Chain-of-Thought Classifier"


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
