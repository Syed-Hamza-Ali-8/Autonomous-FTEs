#!/usr/bin/env python3
"""
Ralph Wiggum Stop Hook - Autonomous Task Persistence

This hook intercepts Claude Code's exit and checks if a task is complete.
If not complete, it re-injects the prompt to keep Claude working.

Completion Strategy: File Movement
- Task file starts in /Tasks/
- When moved to /Done/, task is complete
- Hook checks file location to determine completion

Usage:
    This hook runs automatically when Claude tries to exit.
    No manual invocation needed.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Configuration
VAULT_PATH = Path(__file__).parent.parent.parent.absolute()
TASKS_DIR = VAULT_PATH / "Tasks"
DONE_DIR = VAULT_PATH / "Done"
MAX_ITERATIONS = 10
STATE_FILE = VAULT_PATH / ".claude" / "ralph_state.json"

def load_state():
    """Load Ralph Wiggum loop state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save Ralph Wiggum loop state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_active_task():
    """Get the currently active task file."""
    state = load_state()
    task_file = state.get('current_task')
    if task_file:
        return Path(task_file)
    return None

def is_task_complete(task_file):
    """Check if task is complete by checking if file moved to /Done."""
    if not task_file:
        return True

    # Check if task file is in /Done
    done_path = DONE_DIR / task_file.name
    if done_path.exists():
        return True

    # Check if task file still exists in /Tasks
    if task_file.exists():
        return False

    # File doesn't exist anywhere - consider complete
    return True

def check_max_iterations():
    """Check if we've exceeded max iterations."""
    state = load_state()
    iteration = state.get('iteration', 0)
    return iteration >= MAX_ITERATIONS

def increment_iteration():
    """Increment iteration counter."""
    state = load_state()
    state['iteration'] = state.get('iteration', 0) + 1
    save_state(state)
    return state['iteration']

def reset_state():
    """Reset Ralph Wiggum state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()

def main():
    """
    Stop hook entry point.

    Returns:
        0: Allow exit (task complete)
        1: Block exit (continue working)
    """
    # Check if Ralph loop is active
    state = load_state()
    if not state.get('active'):
        # No active Ralph loop, allow normal exit
        return 0

    # Get active task
    task_file = get_active_task()
    if not task_file:
        # No task file, allow exit
        reset_state()
        return 0

    # Check if task is complete
    if is_task_complete(task_file):
        print("\n✅ RALPH WIGGUM: Task complete! File moved to /Done")
        print(f"   Task: {task_file.name}")
        reset_state()
        return 0

    # Check max iterations
    if check_max_iterations():
        print("\n⚠️  RALPH WIGGUM: Max iterations reached")
        print(f"   Task: {task_file.name}")
        print(f"   Moving to /Failed for manual review")

        # Move to Failed
        failed_dir = VAULT_PATH / "Failed"
        failed_dir.mkdir(exist_ok=True)
        task_file.rename(failed_dir / task_file.name)

        reset_state()
        return 0

    # Task not complete, continue working
    iteration = increment_iteration()
    print(f"\n🔄 RALPH WIGGUM: Task not complete, continuing... (iteration {iteration}/{MAX_ITERATIONS})")
    print(f"   Task: {task_file.name}")
    print(f"   Waiting for file to move to /Done")
    print()

    # Re-inject the original prompt
    original_prompt = state.get('prompt', '')
    if original_prompt:
        print(f"Continuing with task: {original_prompt}")

    # Block exit (return 1 = continue)
    return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Ralph Wiggum hook error: {e}")
        # On error, allow exit to prevent infinite loop
        sys.exit(0)
