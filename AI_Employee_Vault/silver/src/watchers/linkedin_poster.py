"""
LinkedIn poster for automated business content posting.

This module implements LinkedIn posting using Playwright browser automation.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from ..utils import get_logger

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class LinkedInPoster:
    """
    Poster for LinkedIn using Playwright browser automation.

    Posts business content to LinkedIn to generate sales leads.
    """

    def __init__(self, vault_path: str):
        """
        Initialize LinkedIn poster.

        Args:
            vault_path: Path to the Obsidian vault root

        Raises:
            ImportError: If Playwright not installed
            ValueError: If LinkedIn session not configured
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        self.vault_path = Path(vault_path)
        self.logger = get_logger("linkedin_poster")

        # Load environment variables
        load_dotenv(self.vault_path / "silver" / "config" / ".env")

        # LinkedIn session path
        self.session_path = os.getenv(
            "LINKEDIN_SESSION_PATH",
            str(self.vault_path / "silver" / "config" / "linkedin_session")
        )

        self.logger.info("LinkedIn poster initialized")

    def post_update(self, content: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an update to LinkedIn.

        Args:
            content: Text content to post
            image_path: Optional path to image to attach

        Returns:
            Dict with success status and post details
        """
        self.logger.info("Posting to LinkedIn...")

        try:
            with sync_playwright() as p:
                # Launch browser with persistent session
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,  # Run in background (no visible browser)
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.new_page()

                # Navigate to LinkedIn feed
                page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

                # Check if logged in
                if "login" in page.url.lower() or "authwall" in page.url.lower():
                    self.logger.error("LinkedIn session expired. Please re-login.")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Session expired",
                        "message": "Run: python silver/scripts/setup_linkedin.py"
                    }

                # Wait for page to fully load
                page.wait_for_timeout(3000)  # Simple 3 second wait

                # Click "Start a post" button
                # Use text-based selector (most reliable, verified working)
                page.click('button:has-text("Start a post")', timeout=15000)

                # Wait for editor to appear
                page.wait_for_selector('[role="textbox"]', timeout=10000)

                # Type content
                editor = page.locator('[role="textbox"]').first
                editor.click()
                editor.fill(content)

                # Wait for content to be processed
                self.logger.info("Waiting for content to be processed...")
                page.wait_for_timeout(2000)

                # STEP 1: Click "Done" button if it exists (confirms content)
                self.logger.info("Looking for 'Done' button...")
                done_selectors = [
                    'button:has-text("Done")',
                    '[role="dialog"] button:has-text("Done")',
                    'button[aria-label*="Done"]',
                ]

                done_clicked = False
                for selector in done_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first
                            if not button.is_disabled():
                                button.click(timeout=5000)
                                self.logger.info(f"Clicked 'Done' button using: {selector}")
                                done_clicked = True
                                break
                    except Exception as e:
                        self.logger.debug(f"Done selector {selector} failed: {e}")
                        continue

                if done_clicked:
                    # Wait for preview/next step to appear
                    self.logger.info("Waiting for next step after 'Done'...")
                    page.wait_for_timeout(2000)
                else:
                    self.logger.info("No 'Done' button found - proceeding to 'Post'")

                # STEP 2: Click "Post" button to actually submit
                self.logger.info("Looking for 'Post' button to submit...")

                # Target the actual submit button
                post_button_selectors = [
                    'button.share-actions__primary-action',                    # Primary action button
                    '[role="dialog"] button.share-actions__primary-action',   # More specific
                    'button:has-text("Post"):not([disabled])',                 # Enabled Post button
                ]

                post_clicked = False
                for selector in post_button_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first

                            # Verify button is not disabled
                            if not button.is_disabled():
                                # Wait for button to be visible and ready
                                button.wait_for(state="visible", timeout=5000)

                                # Click the button
                                button.click(timeout=5000)
                                self.logger.info(f"Clicked 'Post' button using: {selector}")
                                post_clicked = True
                                break
                    except Exception as e:
                        self.logger.debug(f"Post selector {selector} failed: {e}")
                        continue

                if not post_clicked:
                    self.logger.error("Could not find or click 'Post' button")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Post button not found",
                        "message": "Could not find or click the Post button"
                    }

                # CRITICAL: Verify the post was actually submitted
                self.logger.info("Verifying post submission...")
                page.wait_for_timeout(3000)

                # Check if modal closed (indicates successful post)
                modal_count = page.locator('[role="dialog"]').count()

                if modal_count > 0:
                    # Modal might still be processing - wait a bit more
                    self.logger.info("Modal still open, waiting for processing...")
                    page.wait_for_timeout(3000)
                    modal_count = page.locator('[role="dialog"]').count()

                    if modal_count > 0:
                        # Modal still open - post did NOT submit
                        self.logger.error("Modal still open after clicking - post did NOT submit")
                        browser.close()
                        return {
                            "success": False,
                            "error": "Post not submitted",
                            "message": "Modal did not close - post failed to submit"
                        }

                self.logger.info("Modal closed - post submitted successfully")

                # Additional wait to ensure post is processed
                page.wait_for_timeout(2000)

                browser.close()

                self.logger.info("✅ Successfully posted to LinkedIn")
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(content),
                    "has_image": image_path is not None
                }

        except PlaywrightTimeout as e:
            self.logger.error(f"Timeout while posting: {e}")
            return {
                "success": False,
                "error": "Timeout",
                "message": str(e)
            }
        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }

    def generate_business_post(self, topic: str = "business update") -> str:
        """
        Generate business content for LinkedIn post.

        Args:
            topic: Topic for the post

        Returns:
            Generated post content
        """
        # Simple template-based generation
        # In production, this would use Claude API for better content
        templates = [
            f"🚀 Excited to share our latest progress in {topic}!\n\nWe're building innovative solutions that help businesses automate their workflows and increase productivity.\n\nInterested in learning more? Let's connect!\n\n#Business #Automation #Innovation",

            f"💡 Key insight from this week: {topic}\n\nAutomation isn't about replacing humans—it's about empowering them to focus on what matters most.\n\nWhat's your take on AI-powered business automation?\n\n#AI #BusinessGrowth #Productivity",

            f"📊 Quick update on our {topic} initiative:\n\n✅ Streamlined communication workflows\n✅ Reduced manual tasks by 70%\n✅ Improved response times\n\nReady to transform your business operations? DM me to learn more!\n\n#Automation #Efficiency #Sales"
        ]

        import random
        return random.choice(templates)

    def schedule_post(self, content: str, schedule_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Schedule a post for later (stores in vault for scheduler to pick up).

        Args:
            content: Post content
            schedule_time: When to post (None = post now)

        Returns:
            Dict with scheduling status
        """
        if schedule_time is None:
            # Post immediately
            return self.post_update(content)

        # Store in scheduled posts folder
        scheduled_dir = self.vault_path / "silver" / "scheduled_posts"
        scheduled_dir.mkdir(exist_ok=True)

        post_file = scheduled_dir / f"linkedin_{schedule_time.strftime('%Y%m%d_%H%M%S')}.md"

        post_content = f"""---
type: linkedin_post
scheduled_time: {schedule_time.isoformat()}
status: pending
---

{content}
"""

        post_file.write_text(post_content)

        self.logger.info(f"Post scheduled for {schedule_time}")
        return {
            "success": True,
            "scheduled_time": schedule_time.isoformat(),
            "file_path": str(post_file)
        }


def main():
    """Test LinkedIn poster."""
    import sys

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    poster = LinkedInPoster(vault_path)

    # Generate test content
    content = poster.generate_business_post("AI automation")

    print("Generated content:")
    print("-" * 50)
    print(content)
    print("-" * 50)

    # Ask for confirmation
    response = input("\nPost this to LinkedIn? (yes/no): ")

    if response.lower() == "yes":
        result = poster.post_update(content)

        if result["success"]:
            print("✅ Successfully posted to LinkedIn!")
        else:
            print(f"❌ Failed to post: {result.get('error')}")
            print(f"   {result.get('message')}")
    else:
        print("Post cancelled.")


if __name__ == "__main__":
    main()
