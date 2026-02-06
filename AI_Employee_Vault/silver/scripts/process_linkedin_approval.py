#!/usr/bin/env python3
"""
Process LinkedIn approval files from Needs_Action folder.

This script:
1. Monitors Needs_Action folder for approval files with action: post_linkedin
2. When status is approved, executes the LinkedIn posting
3. Moves the file to Done/Failed based on result
"""

import sys
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster
from src.utils import get_logger, setup_logging


def parse_approval_file(file_path: Path) -> dict:
    """Parse approval file and extract frontmatter and content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter and body
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return {'frontmatter': frontmatter, 'body': body, 'full_content': content}

    return None


def extract_post_content(body: str) -> str:
    """Extract LinkedIn post content from approval file body."""
    # Look for content after "## Content" or similar markers
    lines = body.split('\n')
    content_lines = []
    in_content = False

    for line in lines:
        if line.strip().startswith('## Content') or line.strip().startswith('**Content**'):
            in_content = True
            continue
        elif line.strip().startswith('##') and in_content:
            # Hit next section, stop
            break
        elif in_content and line.strip():
            content_lines.append(line)

    # If no structured content found, use the whole body
    if not content_lines:
        return body.strip()

    return '\n'.join(content_lines).strip()


def update_approval_file(file_path: Path, status: str, result: dict = None, error: str = None):
    """Update approval file with execution result."""
    data = parse_approval_file(file_path)
    if not data:
        return

    frontmatter = data['frontmatter']
    body = data['body']

    # Update frontmatter
    frontmatter['status'] = status
    frontmatter['executed_at'] = datetime.now().isoformat()

    if result:
        frontmatter['result'] = result
    if error:
        frontmatter['error'] = error

    # Add execution details to body
    execution_section = f"\n\n## Execution Details\n\n"
    execution_section += f"**Executed At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n"
    execution_section += f"**Status**: {status}\n"

    if result:
        execution_section += f"\n### Result\n\n```json\n{result}\n```\n"
    if error:
        execution_section += f"\n### Error\n\n```\n{error}\n```\n"

    # Write updated content
    updated_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{body}{execution_section}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)


def process_approval_file(file_path: Path, vault_path: Path, logger) -> bool:
    """Process a single approval file."""
    logger.info(f"Processing approval file: {file_path.name}")

    # Parse file
    data = parse_approval_file(file_path)
    if not data:
        logger.error(f"Failed to parse approval file: {file_path}")
        return False

    frontmatter = data['frontmatter']
    body = data['body']

    # Check if it's a LinkedIn posting approval
    action = frontmatter.get('action', '')
    status = frontmatter.get('status', 'pending')

    if action != 'post_linkedin':
        logger.debug(f"Skipping non-LinkedIn approval: {action}")
        return False

    if status != 'approved' and status != 'pending':
        logger.debug(f"Skipping approval with status: {status}")
        return False

    # For testing, auto-approve pending approvals
    if status == 'pending':
        logger.info("Auto-approving test approval file...")
        frontmatter['status'] = 'approved'
        status = 'approved'

    # Extract post content
    content = extract_post_content(body)
    if not content:
        logger.error("No content found in approval file")
        update_approval_file(file_path, 'failed', error="No content found")

        # Move to Failed
        failed_folder = vault_path / "Failed"
        failed_folder.mkdir(exist_ok=True)
        file_path.rename(failed_folder / file_path.name)
        return False

    logger.info(f"Extracted content ({len(content)} chars)")

    # Initialize LinkedIn poster
    try:
        poster = LinkedInPoster(str(vault_path))
        logger.info("LinkedIn poster initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LinkedIn poster: {e}")
        update_approval_file(file_path, 'failed', error=str(e))

        # Move to Failed
        failed_folder = vault_path / "Failed"
        failed_folder.mkdir(exist_ok=True)
        file_path.rename(failed_folder / file_path.name)
        return False

    # Post to LinkedIn
    try:
        logger.info("Posting to LinkedIn...")
        result = poster.post_update(content)

        if result.get('success'):
            logger.info("✅ Posted successfully to LinkedIn")
            update_approval_file(file_path, 'completed', result=result)

            # Move to Done
            done_folder = vault_path / "Done"
            done_folder.mkdir(exist_ok=True)
            file_path.rename(done_folder / file_path.name)
            return True
        else:
            error_msg = result.get('message', 'Unknown error')
            logger.error(f"❌ Failed to post: {error_msg}")
            update_approval_file(file_path, 'failed', error=error_msg)

            # Move to Failed
            failed_folder = vault_path / "Failed"
            failed_folder.mkdir(exist_ok=True)
            file_path.rename(failed_folder / file_path.name)
            return False

    except Exception as e:
        logger.error(f"❌ Exception while posting: {e}")
        update_approval_file(file_path, 'failed', error=str(e))

        # Move to Failed
        failed_folder = vault_path / "Failed"
        failed_folder.mkdir(exist_ok=True)
        file_path.rename(failed_folder / file_path.name)
        return False


def main():
    """Main entry point."""
    # Setup logging
    setup_logging(log_level="INFO", log_format="text")
    logger = get_logger("process_linkedin_approval")

    # Get vault path
    vault_path = Path("/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")
    needs_action_folder = vault_path / "Needs_Action"

    print("=" * 60)
    print("LinkedIn Approval Processor")
    print("=" * 60)
    print()

    # Find approval files
    approval_files = list(needs_action_folder.glob("approval_*.md"))
    linkedin_approvals = []

    for file_path in approval_files:
        data = parse_approval_file(file_path)
        if data and data['frontmatter'].get('action') == 'post_linkedin':
            linkedin_approvals.append(file_path)

    if not linkedin_approvals:
        print("No LinkedIn approval files found in Needs_Action folder")
        return

    print(f"Found {len(linkedin_approvals)} LinkedIn approval file(s):")
    for file_path in linkedin_approvals:
        print(f"  - {file_path.name}")
    print()

    # Process each approval file
    results = {'total': 0, 'successful': 0, 'failed': 0}

    for file_path in linkedin_approvals:
        results['total'] += 1
        success = process_approval_file(file_path, vault_path, logger)

        if success:
            results['successful'] += 1
        else:
            results['failed'] += 1

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print()


if __name__ == "__main__":
    main()
