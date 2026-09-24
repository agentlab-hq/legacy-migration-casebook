"""Policy Engine and Customizable Slots.

Implements the three customizable slots:
1. Environment Trust Boundary (trusted Git orgs, S3 buckets, internal domains)
2. Block Rules (20+ rules grouped into 4 threat categories)
3. Allow Exceptions (declared manifests, standard credential flows, working branch)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .types import BlockRuleCategory


@dataclass
class BlockRule:
    id: str
    category: BlockRuleCategory
    name: str
    description: str
    pattern: str  # regex pattern or semantic matcher
    enabled: bool = True


@dataclass
class AllowException:
    id: str
    name: str
    description: str
    pattern: str
    enabled: bool = True


@dataclass
class PolicyConfig:
    # Slot 1: Trusted Environment Boundary
    trusted_git_orgs: List[str] = field(default_factory=lambda: ["my-org"])
    trusted_domains: List[str] = field(default_factory=lambda: ["internal.corp.net", "api.github.com"])
    trusted_cloud_buckets: List[str] = field(default_factory=lambda: ["my-project-dev-bucket"])
    current_working_branch: str = "feature/agent-task"
    
    # Slot 2: Block Rules (20+ built-in rules across 4 categories)
    block_rules: List[BlockRule] = field(default_factory=list)
    
    # Slot 3: Allow Exceptions
    allow_exceptions: List[AllowException] = field(default_factory=list)

    def __post_init__(self):
        if not self.block_rules:
            self.block_rules = self._get_default_block_rules()
        if not self.allow_exceptions:
            self.allow_exceptions = self._get_default_allow_exceptions()

    @staticmethod
    def _get_default_block_rules() -> List[BlockRule]:
        return [
            # Group 1: Destroy or Exfiltrate
            BlockRule("DE-01", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "Force Push Git History",
                      "Prevent overwriting remote history with git push --force",
                      r"git\s+push\s+.*?(?:--force|-f\b)"),
            BlockRule("DE-02", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "Remote Branch Deletion",
                      "Prevent destructive batch or remote git branch deletion",
                      r"git\s+push\s+.*?(?:--delete|-d\b)"),
            BlockRule("DE-03", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "Public Gist / Pastebin Exfil",
                      "Prevent sharing code/data to public gist or pastebins",
                      r"(?:gh\s+gist\s+create|curl\s+.*?(?:pastebin|gist\.github))"),
            BlockRule("DE-04", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "Cloud Storage Mass Deletion",
                      "Prevent mass bucket or object deletion in cloud",
                      r"(?:aws\s+s3\s+rb|gcloud\s+storage\s+rm|az\s+storage\s+blob\s+delete-batch)"),
            BlockRule("DE-05", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "External HTTP POST of Data",
                      "Prevent sending internal data or env vars to external endpoints",
                      # Lookaheads make the match independent of flag order.
                      r"curl\s+(?=.*?(?:-X\s*POST|--request\s+POST))(?=.*?(?:-d\b|--data(?:\s|=)))[^\n]*https?://(?!localhost|127\.0\.0\.1)"),
            BlockRule("DE-06", BlockRuleCategory.DESTROY_OR_EXFILTRATE, "Recursive Root/System Deletion",
                      "Prevent destructive rm -rf outside project directory",
                      r"rm\s+-(?:r[fF]|[fF]r)\s+(?:/|\~|/etc|/var|/usr|/home)"),

            # Group 2: Degrade Security Posture
            BlockRule("SP-01", BlockRuleCategory.DEGRADE_SECURITY_POSTURE, "Disable Logging or Audit",
                      "Prevent disabling system logs or security monitoring agents",
                      r"(?:systemctl\s+stop\s+(?:auditd|rsyslog|syslog)|setenforce\s+0)"),
            BlockRule("SP-02", BlockRuleCategory.DEGRADE_SECURITY_POSTURE, "SSH Key Persistence",
                      "Prevent unauthorized installation of SSH public keys into authorized_keys",
                      r"(?:cat\s+.*?>+?\s*~?/\.ssh/authorized_keys|ssh-copy-id)"),
            BlockRule("SP-03", BlockRuleCategory.DEGRADE_SECURITY_POSTURE, "Cron / Daemon Persistence",
                      "Prevent installing background cron jobs or system services without explicit approval",
                      r"(?:crontab\s+-(?:e|r)|systemctl\s+enable)"),
            BlockRule("SP-04", BlockRuleCategory.DEGRADE_SECURITY_POSTURE, "Modify Agent Permissions Config",
                      "Prevent modifying agent permission settings or bypassing guardrails",
                      # Read-only mentions (e.g. `grep claude.json README`) must NOT trip;
                      # require a write/modify operator touching the config file.
                      r"(?:sed\s+-i[^\n]*|(?:(?:echo|printf|tee|cp|mv|rm|chmod|chown)\s[^\n]*)|(?:>+\s?))\S*(?:\.claude/permissions\.json|claude\.json|\.agent_guard)|(?:\.claude/permissions\.json|claude\.json|\.agent_guard)\s*(?:>+\s|$)"),
            BlockRule("SP-05", BlockRuleCategory.DEGRADE_SECURITY_POSTURE, "Firewall / Security Group Weakening",
                      "Prevent opening firewall ports or disabling iptables/ufw",
                      r"(?:ufw\s+disable|iptables\s+-F)"),

            # Group 3: Cross Trust Boundaries
            BlockRule("TB-01", BlockRuleCategory.CROSS_TRUST_BOUNDARIES, "Credential Grepping / Exploration",
                      "Prevent scanning filesystem or env vars for unrelated API keys and tokens",
                      # Exploration only: recursive scans or env dumps. Targeted
                      # project reads (e.g. `grep API_KEY src/config.py`) are
                      # governed by the Tier 2 sensitive-path gate instead.
                      r"(?:grep|find)\s+(?:[a-zA-Z-]*r[a-zA-Z]*\s+|--recursive\s+)[^\n]*(?:API_KEY|AWS_SECRET|TOKEN|PASSWORD|PRIVATE_KEY|\.env)|find\s+/(?:\s|$)(?=[^\n]*(?:API_KEY|AWS_SECRET|TOKEN|PASSWORD|PRIVATE_KEY|\.env))|\b(?:printenv|env)\b\s*(?:$|\|)"),
            BlockRule("TB-02", BlockRuleCategory.CROSS_TRUST_BOUNDARIES, "Execute Cloned External Repo Code",
                      "Prevent immediate arbitrary execution of code downloaded from external unvetted remotes",
                      r"(?:git\s+clone\s+https?://.*?&&.*?(?:python|node|bash|make))"),
            BlockRule("TB-03", BlockRuleCategory.CROSS_TRUST_BOUNDARIES, "Curl to Shell Execution",
                      "Prevent piping untrusted web scripts directly into shell interpreter",
                      r"curl\s+https?://[^\s]+\s*\|\s*(?:bash|sh|zsh)"),
            BlockRule("TB-04", BlockRuleCategory.CROSS_TRUST_BOUNDARIES, "Untrusted External Remotes",
                      "Prevent pushing or pulling from untrusted git remotes outside organization",
                      # The lookahead must sit directly after the scheme so the
                      # trusted-org URL is actually exempted.
                      r"git\s+remote\s+add\s+\S+\s+https?://(?!github\.com/my-org/)"),
            BlockRule("TB-05", BlockRuleCategory.CROSS_TRUST_BOUNDARIES, "Access Non-Project AWS/GCP Accounts",
                      "Prevent assuming arbitrary cloud roles or switching to foreign profiles",
                      r"(?:aws\s+sts\s+assume-role|gcloud\s+config\s+set\s+account)"),

            # Group 4: Bypass Review or Affect Others
            BlockRule("BR-01", BlockRuleCategory.BYPASS_REVIEW_OR_AFFECT_OTHERS, "Push Directly to Main Branch",
                      "Prevent pushing unreviewed code directly to production branches",
                      r"git\s+push\s+(?:origin|upstream)\s+(?:main|master|prod|production)\b"),
            BlockRule("BR-02", BlockRuleCategory.BYPASS_REVIEW_OR_AFFECT_OTHERS, "Production Deploys",
                      "Prevent triggering automated production deployments without manual review",
                      r"(?:kubectl\s+apply\s+-n\s+(?:prod|production)|helm\s+upgrade\s+.*prod|terraform\s+apply.*prod)"),
            BlockRule("BR-03", BlockRuleCategory.BYPASS_REVIEW_OR_AFFECT_OTHERS, "Cancel Shared Cluster Jobs",
                      "Prevent deleting or cancelling jobs or pods not definitively owned by agent session",
                      r"(?:kubectl\s+delete\s+(?:pod|job|deployment)|scontrol\s+cancel|kill\s+-\d+)"),
            BlockRule("BR-04", BlockRuleCategory.BYPASS_REVIEW_OR_AFFECT_OTHERS, "Safety-Check Skip Flags",
                      "Prevent skipping CI/CD or deployment safety checks and verification flags",
                      r"(?:--skip-verification|--no-verify|--skip-validation|--force-apply)"),
            BlockRule("BR-05", BlockRuleCategory.BYPASS_REVIEW_OR_AFFECT_OTHERS, "Database Migration on Production",
                      "Prevent running schema migrations against live production databases",
                      r"(?:alembic\s+upgrade\s+head|prisma\s+migrate\s+deploy|flyway\s+migrate).*?(?:prod|database\.prod)"),
        ]

    @staticmethod
    def _get_default_allow_exceptions() -> List[AllowException]:
        return [
            AllowException("EX-01", "Declared Manifest Package Installs",
                           "Installing dependencies already declared in package.json or requirements.txt",
                           r"^(?:npm\s+install|yarn\s+install|pip\s+install\s+-r\s+requirements\.txt|bundle\s+install|poetry\s+install)$"),
            AllowException("EX-02", "Session Working Branch Pushes",
                           "Pushing commits to the session's active feature/working branch",
                           r"^git\s+push\s+(?:origin\s+)?(?:HEAD|feature/|fix/|chore/)[a-zA-Z0-9_\-\/]+$"),
            AllowException("EX-03", "Standard Project Build/Test",
                           "Running standard test runners and linters",
                           r"^(?:npm\s+test|pytest|cargo\s+test|go\s+test|make\s+test|npm\s+run\s+lint).*$"),
        ]


class PolicyEngine:
    """Evaluates raw commands against block rules and carve-out exceptions."""

    def __init__(self, config: Optional[PolicyConfig] = None):
        self.config = config or PolicyConfig()

    def check_command(self, command: str) -> Tuple[List[BlockRule], Optional[AllowException]]:
        """Checks command against rules. Returns (matched_blocks, matched_exception)."""
        clean_cmd = command.strip()

        # 1. Check Allow Exceptions first (mandatory carve-outs)
        for exc in self.config.allow_exceptions:
            if exc.enabled and re.search(exc.pattern, clean_cmd, re.IGNORECASE):
                return [], exc

        # 2. Check Block Rules
        matched_blocks = []
        for rule in self.config.block_rules:
            if rule.enabled and re.search(rule.pattern, clean_cmd, re.IGNORECASE):
                matched_blocks.append(rule)

        return matched_blocks, None
