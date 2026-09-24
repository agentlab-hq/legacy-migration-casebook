"""Data structures and types for the Claude Code Auto Mode pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class DecisionVerdict(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"


class DecisionTier(str, Enum):
    TIER_1_SAFE_ALLOWLIST = "Tier 1: Safe-Tool Allowlist & Settings"
    TIER_2_PROJECT_BOUNDARY = "Tier 2: In-Project File Operations"
    TIER_3_STAGE_1 = "Tier 3: Transcript Classifier (Stage 1 Fast Filter)"
    TIER_3_STAGE_2 = "Tier 3: Transcript Classifier (Stage 2 CoT Reasoning)"


class ThreatCategory(str, Enum):
    OVEREAGER_BEHAVIOR = "Overeager Behavior"
    HONEST_MISTAKE = "Honest Mistake"
    PROMPT_INJECTION = "Prompt Injection"
    MISALIGNED_MODEL = "Misaligned Model"


class BlockRuleCategory(str, Enum):
    DESTROY_OR_EXFILTRATE = "Destroy or Exfiltrate"
    DEGRADE_SECURITY_POSTURE = "Degrade Security Posture"
    CROSS_TRUST_BOUNDARIES = "Cross Trust Boundaries"
    BYPASS_REVIEW_OR_AFFECT_OTHERS = "Bypass Review or Affect Others"


@dataclass
class ToolCall:
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    description: Optional[str] = None  # stripped before Tier 3 classifier
    executable_command: Optional[str] = None  # assembled or extracted command


@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    exit_code: int = 0
    is_error: bool = False
    flagged_injection: bool = False
    injection_warning: Optional[str] = None


@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)


@dataclass
class StrippedClassifierInput:
    """The reasoning-blind view passed to Sonnet 4.6 transcript classifier.
    Contains ONLY user messages and bare executable tool payloads.
    Assistant prose, tool descriptions, and tool results are strictly stripped."""
    user_prompts: List[str]
    executable_actions: List[Dict[str, Any]]
    rendered_prompt: str


@dataclass
class Stage1Result:
    verdict: DecisionVerdict  # BLOCK or ALLOW
    raw_token: str  # "YES" (to block) or "NO" (to allow)
    latency_ms: float
    cached_tokens: int
    new_tokens: int


@dataclass
class Stage2Result:
    verdict: DecisionVerdict  # BLOCK or ALLOW
    chain_of_thought: str
    matched_rules: List[str]
    intent_analysis: str
    latency_ms: float
    prompt_cache_hit_ratio: float


@dataclass
class SubagentHandoffCheck:
    direction: str  # "OUTBOUND_DELEGATION" or "INBOUND_RETURN"
    allowed: bool
    warning: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class AutoModeDecision:
    tier: DecisionTier
    verdict: DecisionVerdict
    reason: str
    stage1_result: Optional[Stage1Result] = None
    stage2_result: Optional[Stage2Result] = None
    retry_feedback: Optional[str] = None
    consecutive_denials: int = 0
    total_denials: int = 0
    escalated_to_human: bool = False
    headless_terminated: bool = False
