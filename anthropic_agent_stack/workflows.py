"""Foundational Agentic Workflows from 'Building Effective Agents' (Dec 2024).

Implements the five core workflow patterns and autonomous agent loops:
1. Prompt Chaining (with validation gates)
2. Routing (intent/complexity classification)
3. Parallelization (Sectioning and Voting)
4. Orchestrator-Workers (dynamic task decomposition)
5. Evaluator-Optimizer (iterative generation and critique)
6. Autonomous Agent Loop (environment feedback + stop conditions)
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
import json


class PromptChainingWorkflow:
    """Decomposes a task into sequential LLM/function steps with intermediate validation gates."""

    def __init__(self, steps: List[Dict[str, Any]]):
        self.steps = steps  # List of dicts with 'name', 'fn', 'gate_fn'

    def run(self, initial_input: Any) -> Dict[str, Any]:
        history = []
        current_data = initial_input

        for idx, step in enumerate(self.steps):
            step_name = step.get("name", f"Step_{idx + 1}")
            fn = step["fn"]
            gate_fn = step.get("gate_fn")

            # Execute step
            output = fn(current_data)
            
            # Check programmatic gate
            passed_gate = True
            gate_reason = "Passed"
            if gate_fn:
                passed_gate, gate_reason = gate_fn(output)

            history.append({
                "step": step_name,
                "input": current_data,
                "output": output,
                "gate_passed": passed_gate,
                "gate_reason": gate_reason
            })

            if not passed_gate:
                return {
                    "success": False,
                    "halted_at_step": step_name,
                    "reason": gate_reason,
                    "history": history
                }

            current_data = output

        return {
            "success": True,
            "final_output": current_data,
            "history": history
        }


class RoutingWorkflow:
    """Classifies an input and routes it to specialized downstream processors or models."""

    def __init__(self, router_fn: Callable[[str], str], routes: Dict[str, Callable[[str], Any]]):
        self.router_fn = router_fn
        self.routes = routes

    def run(self, user_query: str) -> Dict[str, Any]:
        route_key = self.router_fn(user_query)
        handler = self.routes.get(route_key, self.routes.get("default"))
        if not handler:
            raise ValueError(f"No handler configured for route: {route_key}")

        result = handler(user_query)
        return {
            "query": user_query,
            "selected_route": route_key,
            "result": result
        }


class ParallelizationWorkflow:
    """Executes parallel tasks via Sectioning (independent subtasks) or Voting (consensus)."""

    @staticmethod
    def section(input_data: Any, tasks: List[Dict[str, Any]], aggregator_fn: Callable[[List[Any]], Any]) -> Dict[str, Any]:
        """Runs multiple distinct subtasks in parallel on input and aggregates results."""
        results = []
        for t in tasks:
            task_name = t["name"]
            res = t["fn"](input_data)
            results.append({"task": task_name, "result": res})
        
        aggregated = aggregator_fn(results)
        return {
            "mode": "Sectioning",
            "section_results": results,
            "aggregated": aggregated
        }

    @staticmethod
    def vote(input_data: Any, reviewers: List[Callable[[Any], Dict[str, Any]]], threshold: float = 0.5) -> Dict[str, Any]:
        """Runs the same task across diverse prompts/models and aggregates votes."""
        votes = []
        for r in reviewers:
            vote_data = r(input_data)
            votes.append(vote_data)
        
        positive_votes = sum(1 for v in votes if v.get("vote") is True)
        ratio = positive_votes / len(votes) if votes else 0.0
        consensus = ratio >= threshold

        return {
            "mode": "Voting",
            "total_reviewers": len(reviewers),
            "positive_votes": positive_votes,
            "consensus": consensus,
            "threshold_required": threshold,
            "details": votes
        }


class OrchestratorWorkersWorkflow:
    """Central orchestrator dynamically plans subtasks, delegates to workers, and synthesizes."""

    def __init__(self, planner_fn: Callable[[str], List[Dict[str, Any]]],
                 worker_fn: Callable[[Dict[str, Any]], Any],
                 synthesizer_fn: Callable[[str, List[Dict[str, Any]]], Any]):
        self.planner_fn = planner_fn
        self.worker_fn = worker_fn
        self.synthesizer_fn = synthesizer_fn

    def run(self, complex_goal: str) -> Dict[str, Any]:
        # 1. Orchestrator plans dynamic subtasks based on goal
        planned_tasks = self.planner_fn(complex_goal)

        # 2. Worker execution
        worker_results = []
        for task in planned_tasks:
            out = self.worker_fn(task)
            worker_results.append({
                "task": task,
                "worker_output": out
            })

        # 3. Orchestrator synthesizes worker results
        final_solution = self.synthesizer_fn(complex_goal, worker_results)

        return {
            "goal": complex_goal,
            "planned_subtasks": planned_tasks,
            "worker_results": worker_results,
            "final_synthesis": final_solution
        }


class EvaluatorOptimizerWorkflow:
    """Iterative loop where generator produces output and evaluator provides targeted feedback."""

    def __init__(self, generator_fn: Callable[[str, Optional[str]], str],
                 evaluator_fn: Callable[[str, str], Tuple[bool, str, float]],
                 max_iterations: int = 4):
        self.generator_fn = generator_fn
        self.evaluator_fn = evaluator_fn
        self.max_iterations = max_iterations

    def run(self, task: str) -> Dict[str, Any]:
        iterations = []
        feedback = None
        current_response = ""
        accepted = False

        for i in range(1, self.max_iterations + 1):
            current_response = self.generator_fn(task, feedback)
            is_acceptable, critique, score = self.evaluator_fn(task, current_response)
            
            iterations.append({
                "iteration": i,
                "response": current_response,
                "score": score,
                "critique": critique,
                "accepted": is_acceptable
            })

            if is_acceptable:
                accepted = True
                break
            
            feedback = critique

        return {
            "task": task,
            "accepted": accepted,
            "total_iterations": len(iterations),
            "final_response": current_response,
            "history": iterations
        }
