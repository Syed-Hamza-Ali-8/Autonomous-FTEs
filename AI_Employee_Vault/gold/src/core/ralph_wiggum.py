"""
Ralph Wiggum Loop

Self-improvement cycle for autonomous operation.
Gold Tier Requirement #10: Ralph Wiggum Loop (Self-Improvement)

Named after Ralph Wiggum's famous quote: "I'm learnding!"
This component enables the AI to monitor its performance, identify improvements,
and autonomously optimize its behavior.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType


class RalphWiggumLoop:
    """Self-improvement cycle for autonomous AI operation."""

    def __init__(self, vault_path: str):
        """
        Initialize Ralph Wiggum loop.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path
        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Performance tracking
        self.performance_history = []
        self.improvement_log = []

    def iterate(self) -> Dict[str, Any]:
        """
        Execute one iteration of the Ralph Wiggum loop.

        Steps:
        1. Observe - Gather performance metrics
        2. Analyze - Identify patterns and issues
        3. Learn - Generate improvement hypotheses
        4. Act - Implement improvements
        5. Measure - Track impact of changes

        Returns:
            Dict with iteration results
        """
        start_time = datetime.now()
        iteration_id = f"ralph_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Step 1: Observe
            metrics = self._observe_performance()

            # Step 2: Analyze
            analysis = self._analyze_patterns(metrics)

            # Step 3: Learn
            improvements = self._generate_improvements(analysis)

            # Step 4: Act
            actions_taken = self._implement_improvements(improvements)

            # Step 5: Measure
            impact = self._measure_impact(actions_taken)

            # Record iteration
            iteration_result = {
                "iteration_id": iteration_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "analysis": analysis,
                "improvements": improvements,
                "actions_taken": actions_taken,
                "impact": impact,
                "status": "success"
            }

            self.performance_history.append(iteration_result)
            self._save_iteration_log(iteration_result)

            # Log iteration
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.RALPH_WIGGUM_ITERATION,
                actor_type=ActorType.SYSTEM,
                actor_id="ralph_wiggum_loop",
                status="success",
                duration_ms=duration_ms,
                domain="system",
                metadata={
                    "iteration_id": iteration_id,
                    "improvements_identified": len(improvements),
                    "actions_taken": len(actions_taken)
                }
            )

            return iteration_result

        except Exception as e:
            # Log failure
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.RALPH_WIGGUM_ITERATION,
                actor_type=ActorType.SYSTEM,
                actor_id="ralph_wiggum_loop",
                status="failure",
                duration_ms=duration_ms,
                domain="system",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def _observe_performance(self) -> Dict[str, Any]:
        """
        Observe current performance metrics.

        Returns:
            Dict with performance metrics
        """
        # Get recent audit logs (last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)

        logs = self.audit_logger.search_logs(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        # Calculate metrics
        total_actions = len(logs)
        successful_actions = len([log for log in logs if log.get("status") == "success"])
        failed_actions = len([log for log in logs if log.get("status") == "failure"])
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

        # Average duration
        durations = [log.get("duration_ms", 0) for log in logs if log.get("duration_ms")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Error types
        errors = [log.get("error", {}) for log in logs if log.get("error")]
        error_types = {}
        for error in errors:
            error_type = error.get("type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Action type distribution
        action_types = {}
        for log in logs:
            action_type = log.get("action_type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "hours": 24
            },
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "error_types": error_types,
            "action_types": action_types
        }

    def _analyze_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patterns in performance metrics.

        Args:
            metrics: Performance metrics

        Returns:
            Dict with analysis results
        """
        issues = []
        strengths = []

        # Analyze success rate
        if metrics["success_rate"] < 90:
            issues.append({
                "category": "reliability",
                "severity": "high",
                "description": f"Success rate of {metrics['success_rate']}% is below target (90%)",
                "metric": "success_rate",
                "current_value": metrics["success_rate"],
                "target_value": 90
            })
        elif metrics["success_rate"] >= 95:
            strengths.append({
                "category": "reliability",
                "description": f"Excellent success rate of {metrics['success_rate']}%",
                "metric": "success_rate",
                "value": metrics["success_rate"]
            })

        # Analyze performance
        if metrics["avg_duration_ms"] > 5000:
            issues.append({
                "category": "performance",
                "severity": "medium",
                "description": f"Average duration of {metrics['avg_duration_ms']:.0f}ms is high",
                "metric": "avg_duration_ms",
                "current_value": metrics["avg_duration_ms"],
                "target_value": 5000
            })

        # Analyze error patterns
        if metrics["error_types"]:
            most_common_error = max(metrics["error_types"].items(), key=lambda x: x[1])
            if most_common_error[1] > 5:
                issues.append({
                    "category": "errors",
                    "severity": "high",
                    "description": f"Frequent {most_common_error[0]} errors ({most_common_error[1]} occurrences)",
                    "metric": "error_frequency",
                    "error_type": most_common_error[0],
                    "count": most_common_error[1]
                })

        return {
            "issues": issues,
            "strengths": strengths,
            "issue_count": len(issues),
            "strength_count": len(strengths),
            "overall_health": "good" if len(issues) == 0 else "needs_improvement"
        }

    def _generate_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate improvement hypotheses based on analysis.

        Args:
            analysis: Analysis results

        Returns:
            List of improvement suggestions
        """
        improvements = []

        for issue in analysis["issues"]:
            if issue["category"] == "reliability":
                improvements.append({
                    "issue_id": issue.get("metric"),
                    "category": "reliability",
                    "hypothesis": "Increase retry attempts for transient errors",
                    "action": "adjust_retry_config",
                    "parameters": {"max_attempts": 5, "base_delay": 2.0},
                    "expected_impact": "Increase success rate by 5-10%",
                    "priority": "high"
                })

            elif issue["category"] == "performance":
                improvements.append({
                    "issue_id": issue.get("metric"),
                    "category": "performance",
                    "hypothesis": "Add caching to reduce API call latency",
                    "action": "enable_caching",
                    "parameters": {"cache_ttl": 300},
                    "expected_impact": "Reduce average duration by 20-30%",
                    "priority": "medium"
                })

            elif issue["category"] == "errors":
                improvements.append({
                    "issue_id": issue.get("error_type"),
                    "category": "errors",
                    "hypothesis": f"Add specific handling for {issue.get('error_type')} errors",
                    "action": "add_error_handler",
                    "parameters": {"error_type": issue.get("error_type")},
                    "expected_impact": "Reduce error frequency by 50%",
                    "priority": "high"
                })

        return improvements

    def _implement_improvements(self, improvements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Implement improvement actions.

        Args:
            improvements: List of improvements to implement

        Returns:
            List of actions taken
        """
        actions_taken = []

        for improvement in improvements:
            # For now, log the improvement suggestion
            # In production, this would actually modify configuration
            action = {
                "improvement_id": improvement["issue_id"],
                "action": improvement["action"],
                "parameters": improvement["parameters"],
                "timestamp": datetime.now().isoformat(),
                "status": "logged",
                "note": "Improvement logged for manual review"
            }

            actions_taken.append(action)

            # Create improvement suggestion in vault
            self._create_improvement_suggestion(improvement)

        return actions_taken

    def _measure_impact(self, actions_taken: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Measure impact of implemented improvements.

        Args:
            actions_taken: List of actions taken

        Returns:
            Dict with impact measurements
        """
        # For now, return placeholder impact
        # In production, this would compare metrics before/after changes
        return {
            "actions_evaluated": len(actions_taken),
            "improvements_verified": 0,
            "improvements_pending": len(actions_taken),
            "note": "Impact measurement requires time to collect data"
        }

    def _create_improvement_suggestion(self, improvement: Dict[str, Any]):
        """
        Create an improvement suggestion file in the vault.

        Args:
            improvement: Improvement details
        """
        suggestion_id = f"improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        suggestion_path = os.path.join(
            self.vault_path,
            "Needs_Action",
            f"{suggestion_id}.md"
        )

        content = f"""---
type: system_improvement
category: {improvement['category']}
priority: {improvement['priority']}
status: pending_review
created: {datetime.now().isoformat()}
suggestion_id: {suggestion_id}
---

# System Improvement Suggestion

## Issue
**Category**: {improvement['category']}
**Priority**: {improvement['priority']}

## Hypothesis
{improvement['hypothesis']}

## Proposed Action
**Action**: `{improvement['action']}`
**Parameters**: {json.dumps(improvement['parameters'], indent=2)}

## Expected Impact
{improvement['expected_impact']}

## Actions
- [ ] Review and approve
- [ ] Implement manually
- [ ] Reject

**To approve**: Check the "Review and approve" box above.
**To reject**: Check the "Reject" box above.

---

*Generated by Ralph Wiggum Loop - I'm learnding!*
"""

        os.makedirs(os.path.dirname(suggestion_path), exist_ok=True)
        with open(suggestion_path, 'w') as f:
            f.write(content)

    def _save_iteration_log(self, iteration_result: Dict[str, Any]):
        """
        Save iteration log to vault.

        Args:
            iteration_result: Iteration results
        """
        log_path = os.path.join(
            self.vault_path,
            "Logs",
            "Ralph_Wiggum",
            f"{iteration_result['iteration_id']}.json"
        )

        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump(iteration_result, f, indent=2)

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of performance over time.

        Returns:
            Dict with performance summary
        """
        if not self.performance_history:
            return {
                "iterations": 0,
                "message": "No iterations yet"
            }

        total_iterations = len(self.performance_history)
        total_improvements = sum(len(it["improvements"]) for it in self.performance_history)
        total_actions = sum(len(it["actions_taken"]) for it in self.performance_history)

        # Calculate average success rate
        success_rates = [it["metrics"]["success_rate"] for it in self.performance_history]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0

        return {
            "iterations": total_iterations,
            "total_improvements_identified": total_improvements,
            "total_actions_taken": total_actions,
            "avg_success_rate": round(avg_success_rate, 2),
            "latest_iteration": self.performance_history[-1]["iteration_id"],
            "overall_trend": "improving" if len(success_rates) > 1 and success_rates[-1] > success_rates[0] else "stable"
        }


if __name__ == "__main__":
    # Test Ralph Wiggum loop
    vault_path = os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    loop = RalphWiggumLoop(vault_path)

    print("🔄 Running Ralph Wiggum Loop iteration...")
    result = loop.iterate()

    print(f"✅ Iteration complete: {result['iteration_id']}")
    print(f"   Total actions: {result['metrics']['total_actions']}")
    print(f"   Success rate: {result['metrics']['success_rate']}%")
    print(f"   Issues found: {result['analysis']['issue_count']}")
    print(f"   Improvements suggested: {len(result['improvements'])}")
    print(f"   Actions taken: {len(result['actions_taken'])}")

    # Get performance summary
    summary = loop.get_performance_summary()
    print(f"\n📊 Performance Summary:")
    print(f"   Iterations: {summary['iterations']}")
    print(f"   Improvements identified: {summary['total_improvements_identified']}")
    print(f"   Actions taken: {summary['total_actions_taken']}")
