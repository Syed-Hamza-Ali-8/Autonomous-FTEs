"""
Task Analyzer for breaking down plans into actionable tasks.

This module analyzes execution plans and breaks them down into
discrete, actionable tasks with dependencies and acceptance criteria.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from ..utils import (
    get_logger,
    load_yaml_file,
    parse_frontmatter,
    serialize_frontmatter,
    read_file,
    write_file,
    list_files,
    ensure_directory_exists,
)


class TaskAnalyzer:
    """
    Breaks down execution plans into actionable tasks.

    Analyzes plan steps, identifies dependencies, and creates
    discrete tasks with clear acceptance criteria.
    """

    def __init__(self, vault_path: str):
        """
        Initialize TaskAnalyzer.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        # Set up folders
        self.plans_folder = self.vault_path / "Plans"
        self.tasks_folder = self.vault_path / "Tasks"
        self.in_progress_folder = self.vault_path / "In_Progress"

        # Ensure folders exist
        for folder in [self.tasks_folder]:
            ensure_directory_exists(folder)

        self.logger.info("TaskAnalyzer initialized")

    def analyze_plan(self, plan_file: Path) -> Dict[str, Any]:
        """
        Analyze a plan file and extract task information.

        Args:
            plan_file: Path to plan file in Plans/

        Returns:
            Dictionary with plan analysis:
            - plan_id: str
            - action_type: str
            - complexity: str
            - steps: List[Dict]
            - dependencies: List[str]
            - estimated_duration: int (minutes)

        Raises:
            FileNotFoundError: If plan file not found
            ValueError: If plan file is invalid
        """
        if not plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")

        # Read plan file
        content = read_file(plan_file)
        frontmatter, body = parse_frontmatter(content)

        # Extract plan details
        plan_id = frontmatter.get("id")
        action_type = frontmatter.get("action_type", "unknown")
        complexity = frontmatter.get("complexity", "moderate")
        estimated_steps = frontmatter.get("estimated_steps", 3)

        if not plan_id:
            raise ValueError(f"Plan file missing ID: {plan_file}")

        # Parse steps from body
        steps = self._parse_steps_from_body(body)

        # Identify dependencies
        dependencies = self._identify_dependencies(steps, action_type)

        # Estimate duration
        estimated_duration = self._estimate_duration(
            complexity,
            estimated_steps,
            action_type
        )

        analysis = {
            "plan_id": plan_id,
            "action_type": action_type,
            "complexity": complexity,
            "steps": steps,
            "dependencies": dependencies,
            "estimated_duration": estimated_duration,
            "estimated_steps": estimated_steps,
        }

        self.logger.info(
            f"Analyzed plan {plan_id}: {len(steps)} steps, "
            f"{estimated_duration}min estimated"
        )

        return analysis

    def _parse_steps_from_body(self, body: str) -> List[Dict[str, Any]]:
        """
        Parse execution steps from plan body.

        Args:
            body: Plan body content

        Returns:
            List of step dictionaries
        """
        steps = []
        lines = body.split("\n")

        current_step = None
        in_steps_section = False

        for line in lines:
            # Check if we're in the Execution Steps section
            if "## Execution Steps" in line:
                in_steps_section = True
                continue

            # Exit steps section if we hit another section
            if in_steps_section and line.startswith("## "):
                break

            # Parse step headers (### Step N: Title)
            if in_steps_section and line.startswith("### Step "):
                if current_step:
                    steps.append(current_step)

                # Extract step number and title
                parts = line.replace("### Step ", "").split(":", 1)
                if len(parts) == 2:
                    step_num = parts[0].strip()
                    step_title = parts[1].strip()

                    current_step = {
                        "step": step_num,
                        "title": step_title,
                        "description": "",
                        "requires_approval": False,
                        "requires_external": False,
                    }

            # Collect step description
            elif in_steps_section and current_step and line.strip():
                if not line.startswith("#"):
                    current_step["description"] += line.strip() + " "

                    # Check for approval keywords
                    if "approval" in line.lower():
                        current_step["requires_approval"] = True

                    # Check for external keywords
                    if any(kw in line.lower() for kw in ["api", "external", "send", "post"]):
                        current_step["requires_external"] = True

        # Add last step
        if current_step:
            steps.append(current_step)

        return steps

    def _identify_dependencies(
        self,
        steps: List[Dict[str, Any]],
        action_type: str
    ) -> List[str]:
        """
        Identify dependencies for the plan.

        Args:
            steps: List of plan steps
            action_type: Type of action

        Returns:
            List of dependency descriptions
        """
        dependencies = []

        # Check for approval dependencies
        if any(step.get("requires_approval") for step in steps):
            dependencies.append("Human approval required")

        # Check for external dependencies
        if any(step.get("requires_external") for step in steps):
            if action_type == "send_email":
                dependencies.append("Gmail API credentials")
            elif action_type == "post_linkedin":
                dependencies.append("LinkedIn API credentials")
            else:
                dependencies.append("External API access")

        # Check for vault dependencies
        if action_type in ["research", "analyze"]:
            dependencies.append("Vault search functionality")

        # Sequential dependency (each step depends on previous)
        if len(steps) > 1:
            dependencies.append("Sequential execution (steps must complete in order)")

        return dependencies

    def _estimate_duration(
        self,
        complexity: str,
        estimated_steps: int,
        action_type: str
    ) -> int:
        """
        Estimate task duration in minutes.

        Args:
            complexity: Complexity level
            estimated_steps: Number of steps
            action_type: Type of action

        Returns:
            Estimated duration in minutes
        """
        # Base duration per step
        base_minutes_per_step = {
            "simple": 2,
            "moderate": 5,
            "complex": 10,
        }

        base_duration = base_minutes_per_step.get(complexity, 5) * estimated_steps

        # Add overhead for specific action types
        if action_type in ["send_email", "post_linkedin"]:
            base_duration += 5  # Approval wait time

        if action_type in ["research", "analyze"]:
            base_duration += 10  # Research time

        return base_duration

    def break_down_plan(
        self,
        plan_file: Path,
        create_task_files: bool = True
    ) -> List[str]:
        """
        Break down a plan into discrete tasks.

        Args:
            plan_file: Path to plan file
            create_task_files: Whether to create task files

        Returns:
            List of task IDs

        Raises:
            FileNotFoundError: If plan file not found
            ValueError: If plan file is invalid
        """
        # Analyze plan
        analysis = self.analyze_plan(plan_file)

        task_ids = []

        # Create a task for each step
        for i, step in enumerate(analysis["steps"]):
            task_id = self._create_task(
                plan_id=analysis["plan_id"],
                action_type=analysis["action_type"],
                step=step,
                step_index=i,
                total_steps=len(analysis["steps"]),
                dependencies=analysis["dependencies"],
                create_file=create_task_files,
            )
            task_ids.append(task_id)

        self.logger.info(
            f"Broke down plan {analysis['plan_id']} into {len(task_ids)} tasks"
        )

        return task_ids

    def _create_task(
        self,
        plan_id: str,
        action_type: str,
        step: Dict[str, Any],
        step_index: int,
        total_steps: int,
        dependencies: List[str],
        create_file: bool = True
    ) -> str:
        """
        Create a task from a plan step.

        Args:
            plan_id: Parent plan ID
            action_type: Type of action
            step: Step dictionary
            step_index: Index of step (0-based)
            total_steps: Total number of steps
            dependencies: List of dependencies
            create_file: Whether to create task file

        Returns:
            Task ID
        """
        # Generate task ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_id = f"task_{timestamp}_{action_type}_step{step['step']}"

        # Determine task status
        if step_index == 0:
            status = "ready"  # First task is ready to start
        else:
            status = "blocked"  # Other tasks are blocked by previous tasks

        # Create task frontmatter
        task_frontmatter = {
            "id": task_id,
            "plan_id": plan_id,
            "action_type": action_type,
            "step_number": step["step"],
            "step_index": step_index,
            "total_steps": total_steps,
            "status": status,
            "requires_approval": step.get("requires_approval", False),
            "requires_external": step.get("requires_external", False),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Add dependencies
        if step_index > 0:
            # This task depends on the previous task
            prev_task_id = f"task_*_{action_type}_step{step_index}"
            task_frontmatter["depends_on"] = prev_task_id

        # Create task body
        task_body = self._create_task_body(
            step=step,
            step_index=step_index,
            total_steps=total_steps,
            dependencies=dependencies,
            action_type=action_type,
        )

        if create_file:
            # Write task file
            task_filename = f"{task_id}.md"
            task_path = self.tasks_folder / task_filename

            task_content = serialize_frontmatter(task_frontmatter, task_body)
            write_file(task_path, task_content)

            self.logger.info(f"Created task: {task_id}")

        return task_id

    def _create_task_body(
        self,
        step: Dict[str, Any],
        step_index: int,
        total_steps: int,
        dependencies: List[str],
        action_type: str,
    ) -> str:
        """Create task body content."""
        # Format action type for display
        action_title = action_type.replace("_", " ").title()

        # Format dependencies
        if dependencies:
            deps_lines = [f"- {dep}" for dep in dependencies]
            deps_str = "\n".join(deps_lines)
        else:
            deps_str = "- None"

        # Determine status icon
        if step_index == 0:
            status_icon = "🟢"
            status_text = "Ready to Start"
        else:
            status_icon = "🔴"
            status_text = "Blocked (waiting for previous step)"

        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(step, action_type)
        criteria_lines = [f"- [ ] {criterion}" for criterion in acceptance_criteria]
        criteria_str = "\n".join(criteria_lines)

        body = f"""# Task: {step['title']}

**Status**: {status_icon} {status_text}
**Step**: {step['step']} of {total_steps}
**Action Type**: {action_title}
**Created**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}

## Description

{step['description'].strip()}

## Dependencies

{deps_str}

## Acceptance Criteria

{criteria_str}

## Notes

- This task is part of a larger execution plan
- Complete all acceptance criteria before marking as done
- Update status in frontmatter as task progresses
- If blocked, wait for previous task to complete

## Next Steps

1. Review task description and acceptance criteria
2. Ensure all dependencies are satisfied
3. Execute the task
4. Verify all acceptance criteria are met
5. Update status to "completed"
6. Move to next task in sequence
"""
        return body

    def _generate_acceptance_criteria(
        self,
        step: Dict[str, Any],
        action_type: str
    ) -> List[str]:
        """Generate acceptance criteria for a task."""
        criteria = []

        # Common criteria
        criteria.append("Task description understood")
        criteria.append("All prerequisites verified")

        # Specific criteria based on step content
        if step.get("requires_approval"):
            criteria.append("Approval obtained from human")

        if step.get("requires_external"):
            criteria.append("External API call successful")
            criteria.append("Response validated")

        if "draft" in step["title"].lower():
            criteria.append("Content drafted and reviewed")

        if "send" in step["title"].lower() or "post" in step["title"].lower():
            criteria.append("Action executed successfully")
            criteria.append("Confirmation received")

        if "verify" in step["title"].lower() or "confirm" in step["title"].lower():
            criteria.append("Verification completed")
            criteria.append("Results documented")

        # Always end with completion criteria
        criteria.append("Task marked as completed in frontmatter")

        return criteria

    def break_down_all_plans(self) -> Dict[str, List[str]]:
        """
        Break down all pending plans into tasks.

        Returns:
            Dictionary mapping plan_id to list of task_ids
        """
        results = {}

        try:
            # Get all plan files
            plan_files = list_files(self.plans_folder, "*.md")
            self.logger.info(f"Found {len(plan_files)} plans to break down")

            for plan_file in plan_files:
                try:
                    # Read plan to check status
                    content = read_file(plan_file)
                    frontmatter, _ = parse_frontmatter(content)

                    # Only break down pending plans
                    if frontmatter.get("status") == "pending":
                        task_ids = self.break_down_plan(plan_file)
                        results[frontmatter["id"]] = task_ids
                except Exception as e:
                    self.logger.error(
                        f"Failed to break down plan {plan_file}: {e}"
                    )

            return results

        except Exception as e:
            self.logger.error(f"Failed to break down plans: {e}")
            return {}


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize analyzer
        analyzer = TaskAnalyzer(vault_path)

        # Break down all pending plans
        print("Breaking down pending plans into tasks...")
        results = analyzer.break_down_all_plans()

        if results:
            print(f"\n✅ Broke down {len(results)} plans:")
            for plan_id, task_ids in results.items():
                print(f"\n   Plan: {plan_id}")
                print(f"   Tasks: {len(task_ids)}")
                for task_id in task_ids:
                    print(f"      - {task_id}")
        else:
            print("\n⚠️  No pending plans found or no tasks generated")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
