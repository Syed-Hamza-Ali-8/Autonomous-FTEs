"""
Plan Generator for analyzing requests and creating execution plans.

This module analyzes incoming action requests and generates structured
execution plans with complexity assessment and risk analysis.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
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


class PlanGenerator:
    """
    Generates execution plans from action requests.

    Analyzes incoming requests, assesses complexity, and creates
    structured plans with steps, prerequisites, and risk assessment.
    """

    def __init__(self, vault_path: str):
        """
        Initialize PlanGenerator.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        # Set up folders
        self.needs_action_folder = self.vault_path / "Needs_Action"
        self.plans_folder = self.vault_path / "Plans"
        self.in_progress_folder = self.vault_path / "In_Progress"

        # Ensure folders exist
        for folder in [self.plans_folder, self.in_progress_folder]:
            ensure_directory_exists(folder)

        # Complexity thresholds
        self.complexity_thresholds = {
            "simple": 3,      # <= 3 steps
            "moderate": 7,    # 4-7 steps
            "complex": 100,   # 8+ steps
        }

        self.logger.info("PlanGenerator initialized")

    def assess_complexity(
        self,
        action_details: Dict[str, Any]
    ) -> Tuple[str, int, Dict[str, Any]]:
        """
        Assess complexity of an action request.

        Args:
            action_details: Dictionary with action details

        Returns:
            Tuple of (complexity_level, estimated_steps, factors)
            - complexity_level: "simple", "moderate", or "complex"
            - estimated_steps: Estimated number of steps
            - factors: Dictionary of complexity factors
        """
        factors = {
            "base_steps": 1,
            "external_dependencies": 0,
            "data_requirements": 0,
            "approval_needed": 0,
            "multi_channel": 0,
            "research_needed": 0,
        }

        # Analyze action type
        action_type = action_details.get("action_type", "unknown")

        # Base complexity by action type
        if action_type in ["send_email", "post_linkedin"]:
            factors["base_steps"] = 2  # Draft + Send
        elif action_type in ["research", "analyze"]:
            factors["base_steps"] = 3  # Search + Analyze + Summarize
            factors["research_needed"] = 1
        elif action_type in ["create_plan", "generate_report"]:
            factors["base_steps"] = 4  # Gather + Analyze + Draft + Review
            factors["research_needed"] = 1
        else:
            factors["base_steps"] = 2

        # Check for external dependencies
        if action_details.get("requires_external_data"):
            factors["external_dependencies"] = 2

        if action_details.get("requires_api_call"):
            factors["external_dependencies"] = 1

        # Check for data requirements
        if action_details.get("requires_vault_search"):
            factors["data_requirements"] = 1

        if action_details.get("requires_file_analysis"):
            factors["data_requirements"] = 2

        # Check if approval needed
        if action_details.get("requires_approval"):
            factors["approval_needed"] = 1

        # Check for multi-channel coordination
        if action_details.get("multi_channel"):
            factors["multi_channel"] = 2

        # Calculate total estimated steps
        estimated_steps = sum(factors.values())

        # Determine complexity level
        if estimated_steps <= self.complexity_thresholds["simple"]:
            complexity_level = "simple"
        elif estimated_steps <= self.complexity_thresholds["moderate"]:
            complexity_level = "moderate"
        else:
            complexity_level = "complex"

        self.logger.info(
            f"Complexity assessment: {complexity_level} "
            f"({estimated_steps} steps)"
        )

        return complexity_level, estimated_steps, factors

    def generate_plan(
        self,
        action_file: Path,
        complexity_level: Optional[str] = None
    ) -> str:
        """
        Generate execution plan from action file.

        Args:
            action_file: Path to action file in Needs_Action/
            complexity_level: Optional override for complexity level

        Returns:
            Plan ID

        Raises:
            FileNotFoundError: If action file not found
            ValueError: If action file is invalid
        """
        if not action_file.exists():
            raise FileNotFoundError(f"Action file not found: {action_file}")

        # Read action file
        content = read_file(action_file)
        frontmatter, body = parse_frontmatter(content)

        # Extract action details
        action_id = frontmatter.get("id")
        action_type = frontmatter.get("action_type", "unknown")
        channel = frontmatter.get("channel", "unknown")

        if not action_id:
            raise ValueError(f"Action file missing ID: {action_file}")

        # Build action details for complexity assessment
        action_details = {
            "action_type": action_type,
            "channel": channel,
            "requires_approval": self._requires_approval(action_type),
            "requires_external_data": self._requires_external_data(body),
            "requires_vault_search": self._requires_vault_search(body),
            "requires_api_call": action_type in ["send_email", "post_linkedin"],
            "multi_channel": False,  # Single channel for now
        }

        # Assess complexity
        if complexity_level is None:
            complexity_level, estimated_steps, factors = self.assess_complexity(
                action_details
            )
        else:
            _, estimated_steps, factors = self.assess_complexity(action_details)

        # Generate plan ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_id = f"plan_{timestamp}_{action_type}"

        # Generate plan steps
        steps = self._generate_steps(action_type, action_details, body)

        # Generate prerequisites
        prerequisites = self._generate_prerequisites(action_type, action_details)

        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(
            action_type,
            action_details,
            complexity_level
        )

        # Create plan frontmatter
        plan_frontmatter = {
            "id": plan_id,
            "action_id": action_id,
            "action_type": action_type,
            "channel": channel,
            "status": "pending",
            "complexity": complexity_level,
            "estimated_steps": estimated_steps,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Create plan body
        plan_body = self._create_plan_body(
            action_type=action_type,
            action_details=action_details,
            original_request=body,
            steps=steps,
            prerequisites=prerequisites,
            risk_assessment=risk_assessment,
            complexity_level=complexity_level,
            estimated_steps=estimated_steps,
        )

        # Write plan file
        plan_filename = f"{plan_id}.md"
        plan_path = self.plans_folder / plan_filename

        plan_content = serialize_frontmatter(plan_frontmatter, plan_body)
        write_file(plan_path, plan_content)

        self.logger.info(f"Generated plan: {plan_id}")
        return plan_id

    def _requires_approval(self, action_type: str) -> bool:
        """Check if action type requires approval."""
        sensitive_actions = [
            "send_email",
            "post_linkedin",
            "delete_file",
            "api_call",
        ]
        return action_type in sensitive_actions

    def _requires_external_data(self, body: str) -> bool:
        """Check if request requires external data."""
        keywords = [
            "research",
            "find information",
            "look up",
            "search online",
            "get data from",
        ]
        body_lower = body.lower()
        return any(keyword in body_lower for keyword in keywords)

    def _requires_vault_search(self, body: str) -> bool:
        """Check if request requires vault search."""
        keywords = [
            "in my notes",
            "from vault",
            "in obsidian",
            "my previous",
            "find in",
        ]
        body_lower = body.lower()
        return any(keyword in body_lower for keyword in keywords)

    def _generate_steps(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        original_request: str
    ) -> List[Dict[str, str]]:
        """Generate execution steps for the plan."""
        steps = []

        # Common patterns by action type
        if action_type == "send_email":
            steps = [
                {
                    "step": "1",
                    "action": "Extract email details",
                    "description": "Parse recipient, subject, and body from request",
                },
                {
                    "step": "2",
                    "action": "Draft email content",
                    "description": "Compose professional email based on request",
                },
                {
                    "step": "3",
                    "action": "Request approval",
                    "description": "Create approval request for email sending",
                },
                {
                    "step": "4",
                    "action": "Send email",
                    "description": "Execute email sending via Gmail API",
                },
                {
                    "step": "5",
                    "action": "Confirm delivery",
                    "description": "Verify email was sent successfully",
                },
            ]

        elif action_type == "research":
            steps = [
                {
                    "step": "1",
                    "action": "Define research scope",
                    "description": "Identify key topics and questions",
                },
                {
                    "step": "2",
                    "action": "Search vault",
                    "description": "Search existing notes for relevant information",
                },
                {
                    "step": "3",
                    "action": "Analyze findings",
                    "description": "Synthesize information from vault",
                },
                {
                    "step": "4",
                    "action": "Create summary",
                    "description": "Generate research summary document",
                },
            ]

        elif action_type == "create_plan":
            steps = [
                {
                    "step": "1",
                    "action": "Analyze request",
                    "description": "Understand goals and constraints",
                },
                {
                    "step": "2",
                    "action": "Break down tasks",
                    "description": "Identify individual tasks and dependencies",
                },
                {
                    "step": "3",
                    "action": "Assess resources",
                    "description": "Determine required resources and timeline",
                },
                {
                    "step": "4",
                    "action": "Generate plan",
                    "description": "Create structured execution plan",
                },
            ]

        else:
            # Generic steps
            steps = [
                {
                    "step": "1",
                    "action": "Analyze request",
                    "description": "Understand requirements and context",
                },
                {
                    "step": "2",
                    "action": "Execute action",
                    "description": f"Perform {action_type} operation",
                },
                {
                    "step": "3",
                    "action": "Verify completion",
                    "description": "Confirm action completed successfully",
                },
            ]

        return steps

    def _generate_prerequisites(
        self,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> List[str]:
        """Generate prerequisites for the plan."""
        prerequisites = []

        # Common prerequisites by action type
        if action_type == "send_email":
            prerequisites = [
                "Gmail API credentials configured",
                "Recipient email address validated",
                "Email content approved (if required)",
            ]

        elif action_type == "post_linkedin":
            prerequisites = [
                "LinkedIn API credentials configured",
                "Post content approved",
                "Account has posting permissions",
            ]

        elif action_type == "research":
            prerequisites = [
                "Vault search functionality available",
                "Research scope clearly defined",
            ]

        else:
            prerequisites = [
                "Required permissions available",
                "Dependencies satisfied",
            ]

        # Add approval prerequisite if needed
        if action_details.get("requires_approval"):
            prerequisites.append("Human approval obtained")

        return prerequisites

    def _generate_risk_assessment(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        complexity_level: str
    ) -> Dict[str, Any]:
        """Generate risk assessment for the plan."""
        risk_assessment = {
            "overall_risk": "low",
            "factors": [],
            "mitigation": [],
        }

        # Assess risk factors
        if action_type in ["send_email", "post_linkedin"]:
            risk_assessment["factors"].append(
                "External communication - content visible to others"
            )
            risk_assessment["mitigation"].append(
                "Require human approval before sending"
            )
            risk_assessment["overall_risk"] = "medium"

        if action_type == "delete_file":
            risk_assessment["factors"].append(
                "Irreversible action - data loss possible"
            )
            risk_assessment["mitigation"].append(
                "Require explicit confirmation"
            )
            risk_assessment["overall_risk"] = "high"

        if complexity_level == "complex":
            risk_assessment["factors"].append(
                "High complexity - multiple steps and dependencies"
            )
            risk_assessment["mitigation"].append(
                "Break into smaller sub-tasks with checkpoints"
            )

        if action_details.get("requires_external_data"):
            risk_assessment["factors"].append(
                "External dependencies - may fail or timeout"
            )
            risk_assessment["mitigation"].append(
                "Implement retry logic and error handling"
            )

        # Default if no specific risks
        if not risk_assessment["factors"]:
            risk_assessment["factors"].append("Standard operational risk")
            risk_assessment["mitigation"].append("Follow standard procedures")

        return risk_assessment

    def _create_plan_body(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        original_request: str,
        steps: List[Dict[str, str]],
        prerequisites: List[str],
        risk_assessment: Dict[str, Any],
        complexity_level: str,
        estimated_steps: int,
    ) -> str:
        """Create plan body content."""
        # Format action type for display
        action_title = action_type.replace("_", " ").title()

        # Format steps
        steps_lines = []
        for step in steps:
            steps_lines.append(
                f"### Step {step['step']}: {step['action']}\n\n"
                f"{step['description']}\n"
            )
        steps_str = "\n".join(steps_lines)

        # Format prerequisites
        prereq_lines = [f"- {prereq}" for prereq in prerequisites]
        prereq_str = "\n".join(prereq_lines)

        # Format risk assessment
        risk_factors = "\n".join([f"- {factor}" for factor in risk_assessment["factors"]])
        risk_mitigation = "\n".join([f"- {mit}" for mit in risk_assessment["mitigation"]])

        # Extract original request summary
        request_lines = original_request.split("\n")
        request_summary = "\n".join(request_lines[:5])  # First 5 lines

        body = f"""# Execution Plan: {action_title}

**Status**: ⏳ Pending Execution
**Complexity**: {complexity_level.title()} ({estimated_steps} steps)
**Created**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}

## Original Request

{request_summary}

## Goal

Execute {action_title} as requested, ensuring all prerequisites are met and risks are mitigated.

## Prerequisites

{prereq_str}

## Execution Steps

{steps_str}

## Risk Assessment

**Overall Risk**: {risk_assessment['overall_risk'].upper()}

### Risk Factors
{risk_factors}

### Mitigation Strategies
{risk_mitigation}

## Expected Outcome

- Action completed successfully
- All steps verified
- Results documented
- User notified of completion

## Notes

- This plan was automatically generated based on the action request
- Review and modify steps as needed before execution
- Update status in frontmatter as plan progresses
"""
        return body

    def generate_plans_for_pending_actions(self) -> List[str]:
        """
        Generate plans for all pending actions in Needs_Action folder.

        Returns:
            List of generated plan IDs
        """
        plan_ids = []

        try:
            # Get all action files
            action_files = list_files(self.needs_action_folder, "*.md")
            self.logger.info(f"Found {len(action_files)} pending actions")

            for action_file in action_files:
                try:
                    plan_id = self.generate_plan(action_file)
                    plan_ids.append(plan_id)
                except Exception as e:
                    self.logger.error(
                        f"Failed to generate plan for {action_file}: {e}"
                    )

            return plan_ids

        except Exception as e:
            self.logger.error(f"Failed to generate plans: {e}")
            return []


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize generator
        generator = PlanGenerator(vault_path)

        # Generate plans for pending actions
        print("Generating plans for pending actions...")
        plan_ids = generator.generate_plans_for_pending_actions()

        if plan_ids:
            print(f"\n✅ Generated {len(plan_ids)} plans:")
            for plan_id in plan_ids:
                print(f"   - {plan_id}")
        else:
            print("\n⚠️  No pending actions found or no plans generated")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
