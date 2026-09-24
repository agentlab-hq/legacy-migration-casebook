"""Commercial ROI & Token Economics Calculator for AI Agent Deployments.

Used to generate financial audit reports for enterprise prospects, proving
massive cost savings from MCP Code Mode, Auto Mode, and Parallel Autonomous Teams.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class EnterpriseAgentAudit:
    client_name: str
    active_agent_seats: int
    monthly_tool_calls: int
    avg_tokens_per_call: int
    blended_token_cost_per_million: float  # e.g., $3.00 for input, $15.00 for output -> ~$6.00 blended
    dev_hourly_rate: float = 120.0  # US senior software engineer rate

    def compute_mcp_savings(self) -> Dict[str, Any]:
        """Calculates savings by switching from Direct Tool Calling to MCP Code Mode (~94% token reduction)."""
        current_monthly_tokens = self.monthly_tool_calls * self.avg_tokens_per_call
        current_monthly_spend = (current_monthly_tokens / 1_000_000) * self.blended_token_cost_per_million

        # With MCP Code Mode: progressive discovery + in-sandbox data filtering reduces tokens by ~94%
        optimized_monthly_tokens = int(current_monthly_tokens * 0.06)
        optimized_monthly_spend = (optimized_monthly_tokens / 1_000_000) * self.blended_token_cost_per_million

        monthly_savings = current_monthly_spend - optimized_monthly_spend
        annual_savings = monthly_savings * 12

        return {
            "current_monthly_spend": round(current_monthly_spend, 2),
            "optimized_monthly_spend": round(optimized_monthly_spend, 2),
            "monthly_savings": round(monthly_savings, 2),
            "annual_savings": round(annual_savings, 2),
            "savings_percentage": round((1 - optimized_monthly_tokens / current_monthly_tokens) * 100, 1)
        }

    def compute_migration_project_roi(self, codebase_lines: int) -> Dict[str, Any]:
        """Compares human consulting firm migration costs vs. Carlini-style Autonomous Migration."""
        if codebase_lines <= 0:
            raise ValueError("codebase_lines must be positive")

        # Industry standard: 1 senior dev migrates ~250 lines of production code/day (tested, refactored)
        human_dev_days = codebase_lines / 250
        human_hours = human_dev_days * 8
        human_cost = human_hours * self.dev_hourly_rate

        # Autonomous Agent Migration (Opus 4.6 + Oracle Differential Harness + Auto Mode):
        # Tokens required: ~300 tokens per line of code across iterative cycles
        total_tokens = codebase_lines * 300
        llm_api_cost = (total_tokens / 1_000_000) * 12.0  # Opus blended rate
        infrastructure_cost = 150.0  # Docker / VM compute

        total_autonomous_cost = llm_api_cost + infrastructure_cost

        # Commercial pricing: quoted at 60% below the human-consultancy cost
        # (matches the Profit Studio calculator in the dashboard).
        recommended_client_price = round(human_cost * 0.40, 2)
        gross_profit = recommended_client_price - total_autonomous_cost
        gross_margin_pct = round((gross_profit / recommended_client_price) * 100, 1)

        return {
            "codebase_lines": codebase_lines,
            "human_agency_cost": round(human_cost, 2),
            "human_turnaround_weeks": round(human_dev_days / 5, 1),
            "autonomous_runtime_days": round(codebase_lines / 15000, 1) + 1,  # 15k lines/day with 16 agents
            "raw_token_and_infra_cost": round(total_autonomous_cost, 2),
            "recommended_client_price": recommended_client_price,
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": gross_margin_pct
        }


def print_sample_audit():
    audit = EnterpriseAgentAudit(
        client_name="FinTech Corp",
        active_agent_seats=40,
        monthly_tool_calls=500_000,
        avg_tokens_per_call=8_000,
        blended_token_cost_per_million=7.50,
        dev_hourly_rate=140.0
    )

    print("=== CLIENT ROI AUDIT REPORT ===")
    mcp_res = audit.compute_mcp_savings()
    print(f"Current Monthly Token Spend:  ${mcp_res['current_monthly_spend']:,.2f}")
    print(f"Spend with MCP Code Mode:     ${mcp_res['optimized_monthly_spend']:,.2f}")
    print(f"Annual Client Savings:        ${mcp_res['annual_savings']:,.2f}")
    print(f"Your Cut (20% Gain-Share):    ${mcp_res['annual_savings'] * 0.20:,.2f}/year\n")

    mig_res = audit.compute_migration_project_roi(codebase_lines=85_000)
    print("=== 85,000-LINE CODEBASE MIGRATION PROJECT ===")
    print(f"Traditional Human Agency Quote: ${mig_res['human_agency_cost']:,.2f} ({mig_res['human_turnaround_weeks']} weeks)")
    print(f"Your Client Offer (60% off):    ${mig_res['recommended_client_price']:,.2f} ({mig_res['autonomous_runtime_days']} days)")
    print(f"Your Raw Token & Infra Cost:    ${mig_res['raw_token_and_infra_cost']:,.2f}")
    print(f"Your Net Profit on 1 Project:   ${mig_res['gross_profit']:,.2f} ({mig_res['gross_margin_pct']}% Margin!)")


if __name__ == "__main__":
    print_sample_audit()
