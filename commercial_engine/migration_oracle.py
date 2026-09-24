"""Commercial Prototype: Autonomous Code Modernization & Migration Engine.

Combines migration transforms with executable syntax and behavioral smoke tests.
This remains a prototype: real production migrations still require a customer test
suite and accountable human review.
"""

import ast
import re
from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass


@dataclass
class CodeModule:
    path: str
    legacy_code: str
    migrated_code: Optional[str] = None
    status: str = "PENDING"  # PENDING, MIGRATED, VERIFIED_BY_ORACLE, REGRESSION_DETECTED


class TestOracle:
    """Runs syntax checks and representative behavioral checks on migrated code."""

    @staticmethod
    def run_unit_tests(code: str) -> Tuple[bool, str]:
        """Compile and execute the known migration interfaces in an isolated namespace.

        This is deliberately a small smoke-test oracle, not a replacement for the
        client's complete regression suite. It verifies that generated code is valid
        Python, exposes the expected callable interfaces, and preserves the sample
        behavior of the built-in migration fixtures.
        """
        try:
            tree = ast.parse(code, filename="migrated_module.py")
            compiled = compile(tree, filename="migrated_module.py", mode="exec")
        except (SyntaxError, TypeError, ValueError) as exc:
            return False, f"SYNTAX_ERROR: {exc}"

        namespace: Dict[str, Any] = {"__name__": "migrated_module"}
        try:
            exec(compiled, namespace, namespace)
        except Exception as exc:
            return False, f"IMPORT_ERROR: {type(exc).__name__}: {exc}"

        checks = []
        calculate_risk = namespace.get("calculate_risk")
        if calculate_risk is not None:
            if not callable(calculate_risk):
                return False, "BEHAVIOR_ERROR: calculate_risk is not callable."
            try:
                result = calculate_risk(100.0, 2.0)
                if not isinstance(result, (int, float)) or isinstance(result, bool):
                    return False, "BEHAVIOR_ERROR: calculate_risk did not return a number."
                checks.append("calculate_risk smoke test passed")
            except Exception as exc:
                return False, f"BEHAVIOR_ERROR: calculate_risk failed: {exc}"

        process_transaction = namespace.get("process_transaction")
        if process_transaction is not None:
            if not callable(process_transaction):
                return False, "BEHAVIOR_ERROR: process_transaction is not callable."
            try:
                result = process_transaction("tx-smoke", {"amount": 10})
                if not isinstance(result, dict) or result.get("id") != "tx-smoke":
                    return False, "BEHAVIOR_ERROR: process_transaction returned an invalid result."
                checks.append("process_transaction smoke test passed")
            except Exception as exc:
                return False, f"BEHAVIOR_ERROR: process_transaction failed: {exc}"

        if not checks:
            return False, "FAIL: No supported migration interfaces found."

        return True, f"EXECUTABLE SMOKE TESTS PASSED: {len(checks)}/{len(checks)}; " + "; ".join(checks)


class AutonomousMigrationWorker:
    """An autonomous migration agent running in a cattle sandbox."""

    def __init__(self, agent_id: str, oracle: TestOracle):
        self.agent_id = agent_id
        self.oracle = oracle

    def migrate_file(self, module: CodeModule) -> CodeModule:
        """Transforms the built-in legacy fixtures into typed Python code."""
        legacy = module.legacy_code

        migrated = re.sub(
            r"def calculate_risk\(amount, score\):",
            "def calculate_risk(amount: float, score: float) -> float:\n    """Calculates normalized risk index [Modernized v2.0]."""",
            legacy
        )
        migrated = re.sub(
            r"def process_transaction\(tx_id, payload\):",
            "def process_transaction(tx_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:\n    """Processes financial transaction [Strictly Typed]."""",
            migrated
        )
        if "from typing import Dict, Any" not in migrated:
            migrated = "from typing import Dict, Any, Optional\n\n" + migrated

        module.migrated_code = migrated
        module.status = "MIGRATED"

        passed, _test_log = self.oracle.run_unit_tests(migrated)
        module.status = "VERIFIED_BY_ORACLE" if passed else "REGRESSION_DETECTED"
        return module


class CommercialMigrationEngine:
    """Orchestrates migration workers across the prototype repository."""

    def __init__(self):
        self.oracle = TestOracle()
        self.modules: Dict[str, CodeModule] = {
            "services/risk_engine.py": CodeModule(
                path="services/risk_engine.py",
                legacy_code="def calculate_risk(amount, score):\n    return (amount * 0.05) + (score * 1.2)\n"
            ),
            "services/payment_gateway.py": CodeModule(
                path="services/payment_gateway.py",
                legacy_code="def process_transaction(tx_id, payload):\n    return {'status': 'processed', 'id': tx_id}\n"
            )
        }

    def execute_migration(self) -> Dict[str, Any]:
        results = []
        for path, mod in self.modules.items():
            worker = AutonomousMigrationWorker("Worker-01", self.oracle)
            updated = worker.migrate_file(mod)
            results.append({
                "file": updated.path,
                "status": updated.status,
                "lines_migrated": len(updated.legacy_code.splitlines()),
                "migrated_preview": (updated.migrated_code or "")[:180] + "..."
            })

        verified_count = sum(1 for result in results if result["status"] == "VERIFIED_BY_ORACLE")
        return {
            "total_files": len(results),
            "verified_count": verified_count,
            "regressions": len(results) - verified_count,
            "details": results
        }


if __name__ == "__main__":
    engine = CommercialMigrationEngine()
    summary = engine.execute_migration()
    print("MIGRATION FLEET RUN COMPLETE:")
    print(f"Files Verified by Oracle: {summary['verified_count']}/{summary['total_files']}")
    for detail in summary["details"]:
        print(f"\n[{detail['status']}] {detail['file']}:\n{detail['migrated_preview']}")
