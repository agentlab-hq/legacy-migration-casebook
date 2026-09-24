"""Transcript Sanitizer for Tier 3 Classifier.

Strips assistant prose, chain-of-thought rationalizations, tool descriptions,
and tool output bodies. Preserves only:
1. User messages (to evaluate authorization and intent)
2. Bare executable tool calls / payloads (what the agent actually does)

This makes the classifier reasoning-blind and structurally immune to prompt
injections embedded in tool results.
"""

from typing import List, Dict, Any
from .types import Message, ToolCall, StrippedClassifierInput


class TranscriptSanitizer:
    """Transforms raw conversation history into the stripped input required by Sonnet 4.6."""

    @staticmethod
    def extract_executable_payload(tool_call: ToolCall) -> Dict[str, Any]:
        """Extracts purely the functional action payload, stripping natural language wrappers."""
        payload = {
            "tool": tool_call.tool_name,
        }
        # If command or code is present, extract it cleanly
        if tool_call.executable_command:
            payload["command"] = tool_call.executable_command
        elif "command" in tool_call.arguments:
            payload["command"] = tool_call.arguments["command"]
        elif "path" in tool_call.arguments:
            payload["path"] = tool_call.arguments["path"]
            if "content" in tool_call.arguments:
                # Include preview of content if small, or length
                c = tool_call.arguments["content"]
                payload["content_preview"] = c[:200] + ("..." if len(c) > 200 else "")
        else:
            # Include clean arguments without prose descriptions
            payload["args"] = {
                k: v for k, v in tool_call.arguments.items()
                if k not in ("description", "explanation", "reasoning", "thought")
            }
        return payload

    def sanitize(self, history: List[Message], current_tool_call: ToolCall) -> StrippedClassifierInput:
        """Processes conversation history and returns stripped representation."""
        user_prompts = []
        actions = []

        for msg in history:
            if msg.role == "user":
                user_prompts.append(msg.content.strip())
            elif msg.role == "assistant":
                # STRICTLY STRIP msg.content (assistant rationalizations, thinking, prose)
                # Keep prior tool calls if needed for sequence context
                for tc in msg.tool_calls:
                    actions.append(self.extract_executable_payload(tc))
            elif msg.role == "tool":
                # STRICTLY STRIP tool output / execution results to prevent injection leakage
                pass

        # Append current action under evaluation
        current_action_payload = self.extract_executable_payload(current_tool_call)
        actions.append(current_action_payload)

        # Render canonical prompt template
        lines = ["=== USER AUTHORIZATION CONTEXT ==="]
        for i, u in enumerate(user_prompts, 1):
            lines.append(f"[User Message {i}]: {u}")

        lines.append("\n=== EXECUTABLE ACTIONS (REASONING-BLIND) ===")
        for i, a in enumerate(actions, 1):
            is_current = " (CURRENT ACTION PENDING APPROVAL)" if i == len(actions) else ""
            lines.append(f"[Action {i}{is_current}]: {a}")

        rendered = "\n".join(lines)

        return StrippedClassifierInput(
            user_prompts=user_prompts,
            executable_actions=actions,
            rendered_prompt=rendered
        )
