"""Code Execution with Model Context Protocol (MCP Code Mode) - Nov 2025.

Solves the token-bloat and intermediate-result bottleneck of direct tool calls:
1. Filesystem projection of MCP tools (Progressive Disclosure)
2. Execution-environment data filtering (10,000 rows -> 5 rows in context)
3. Privacy-preserving PII tokenization pipeline
4. Evolutionary Skills repository persistence
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple


class VirtualMCPServer:
    """Represents an MCP server whose tools are exposed as code functions."""

    def __init__(self, server_id: str, tools: Dict[str, Dict[str, Any]]):
        self.server_id = server_id
        self.tools = tools  # tool_name -> metadata, schema, sample_dataset

    def get_tool_list(self, detail_level: str = "summary") -> Dict[str, Any]:
        """Progressive disclosure: loads only as much schema detail as requested."""
        if detail_level == "names_only":
            return {"server": self.server_id, "tools": list(self.tools.keys())}
        elif detail_level == "summary":
            return {
                "server": self.server_id,
                "tools": {name: t["description"] for name, t in self.tools.items()}
            }
        else:  # full
            return {"server": self.server_id, "tools": self.tools}

    def generate_code_api(self, language: str = "typescript") -> str:
        """Generates TypeScript/Python code bindings for this MCP server."""
        lines = [f"// Server: {self.server_id}"]
        for name, spec in self.tools.items():
            params = spec.get("parameters", {})
            param_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in params.items()])
            lines.append(f"/* {spec.get('description', '')} */")
            lines.append(f"export async function {name}(input: {{ {param_str} }}): Promise<any> {{ ... }}")
        return "\n".join(lines)


class PIITokenizer:
    """Tokenizes sensitive user and customer fields before intermediate data touches the LLM context."""

    def __init__(self):
        self.vault: Dict[str, str] = {}
        self.reverse_vault: Dict[str, str] = {}
        self.counter = 0

    def tokenize(self, text: str) -> str:
        # Email pattern
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        
        def replace_email(match):
            original = match.group(0)
            if original in self.reverse_vault:
                return self.reverse_vault[original]
            self.counter += 1
            token = f"[EMAIL_{self.counter}]"
            self.vault[token] = original
            self.reverse_vault[original] = token
            return token

        # Phone pattern
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        def replace_phone(match):
            original = match.group(0)
            if original in self.reverse_vault:
                return self.reverse_vault[original]
            self.counter += 1
            token = f"[PHONE_{self.counter}]"
            self.vault[token] = original
            self.reverse_vault[original] = token
            return token

        masked = re.sub(email_pattern, replace_email, text)
        masked = re.sub(phone_pattern, replace_phone, masked)
        return masked

    def detokenize(self, text: str) -> str:
        detok = text
        for token, original in self.vault.items():
            detok = detok.replace(token, original)
        return detok


class MCPCodeModeEngine:
    """Simulates code execution vs. direct tool calling, computing token economics."""

    def __init__(self):
        self.servers: Dict[str, VirtualMCPServer] = {}
        self.pii_tokenizer = PIITokenizer()
        self.skills: Dict[str, Dict[str, str]] = {}
        self._init_default_servers()

    def _init_default_servers(self):
        # 1. Google Drive server
        self.servers["google-drive"] = VirtualMCPServer("google-drive", {
            "getDocument": {
                "description": "Retrieves full meeting transcripts and documents",
                "parameters": {"documentId": {"type": "string"}},
                "sample_payload_tokens": 48000
            },
            "getSheet": {
                "description": "Fetches large corporate spreadsheet tables",
                "parameters": {"sheetId": {"type": "string"}},
                "sample_payload_tokens": 120000
            }
        })
        # 2. Salesforce server
        self.servers["salesforce"] = VirtualMCPServer("salesforce", {
            "updateRecord": {
                "description": "Updates customer relationship records and opportunity notes",
                "parameters": {"objectType": {"type": "string"}, "recordId": {"type": "string"}, "data": {"type": "object"}},
                "sample_payload_tokens": 50000
            },
            "query": {
                "description": "Executes SOQL queries across CRM objects",
                "parameters": {"query": {"type": "string"}},
                "sample_payload_tokens": 75000
            }
        })
        # 3. Slack server
        self.servers["slack"] = VirtualMCPServer("slack", {
            "getChannelHistory": {
                "description": "Reads message feeds and threads from public/private channels",
                "parameters": {"channel": {"type": "string"}, "limit": {"type": "number"}},
                "sample_payload_tokens": 30000
            },
            "postMessage": {
                "description": "Sends alerts and formatted status reports to channel",
                "parameters": {"channel": {"type": "string"}, "text": {"type": "string"}},
                "sample_payload_tokens": 500
            }
        })

    def compare_token_costs(self, workflow_name: str) -> Dict[str, Any]:
        """Calculates token overhead of Direct Tool Calling vs. Code Mode."""
        if workflow_name == "transcript_to_crm":
            # Scenario: GDrive 45k token transcript piped to Salesforce lead
            direct_schema_tokens = 15000  # loading 50 MCP tool schemas upfront
            direct_intermediate_tokens = 45000 * 2  # document loaded, then echoed into call
            direct_total = direct_schema_tokens + direct_intermediate_tokens

            code_mode_schema_tokens = 850  # only loaded getDocument.ts and updateRecord.ts
            code_mode_intermediate_tokens = 420  # code runs in sandbox; only summary log returned
            code_mode_total = code_mode_schema_tokens + code_mode_intermediate_tokens

            savings_pct = round(((direct_total - code_mode_total) / direct_total) * 100, 1)

            return {
                "scenario": "Meeting Transcript -> Salesforce Lead Sync",
                "direct_tool_tokens": direct_total,
                "code_mode_tokens": code_mode_total,
                "token_savings_pct": savings_pct,
                "direct_breakdown": {
                    "all_schemas_upfront": direct_schema_tokens,
                    "intermediate_transcript_in_context": direct_intermediate_tokens
                },
                "code_mode_breakdown": {
                    "progressive_schema_discovery": code_mode_schema_tokens,
                    "sandboxed_execution_summary": code_mode_intermediate_tokens
                }
            }
        elif workflow_name == "sheet_filter_10k_rows":
            # Scenario: Filter 10k rows in GDrive sheet
            direct_total = 115000
            code_mode_total = 1450
            savings_pct = round(((direct_total - code_mode_total) / direct_total) * 100, 1)
            return {
                "scenario": "10,000-Row Sheet Filter (Pending Orders Only)",
                "direct_tool_tokens": direct_total,
                "code_mode_tokens": code_mode_total,
                "token_savings_pct": savings_pct
            }
        return {}

    def register_skill(self, skill_name: str, code: str, doc: str):
        """Saves a reusable skill into ./skills/<skill_name>/ for evolutionary reuse."""
        self.skills[skill_name] = {
            "code": code,
            "documentation": doc
        }
