#!/usr/bin/env python3
"""
WhatsApp Web setup script.

This script guides the user through setting up WhatsApp Web session
by scanning a QR code with their mobile device.
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def setup_whatsapp_session(vault_path: str) -> None:
    """
    Set up WhatsApp Web session through QR code scanning.

    Args:
        vault_path: Path to the vault root directory
    """
    print("=" * 60)
    print("WhatsApp Web Setup")
    print("=" * 60)
    print()

    # Get session path
    session_path = Path(vault_path) / "silver" / "config" / "whatsapp_session"

    print("📋 Prerequisites:")
    print("   1. WhatsApp installed on your mobile device")
    print("   2. Mobile device connected to internet")
    print()
    print("📱 Setup process:")
    print("   1. A browser window will open with WhatsApp Web")
    print("   2. Scan the QR code with your mobile device")
    print("   3. Open WhatsApp on your phone")
    print("   4. Tap Menu (⋮) → Linked Devices → Link a Device")
    print("   5. Point your phone at the QR code on screen")
    print()

    input("Press Enter to continue...")
    print()

    try:
        with sync_playwright() as p:
            print("🌐 Launching browser...")

            # Launch browser with persistent context
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_path),
                headless=False,  # Show browser for QR code scanning
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            print("📱 Opening WhatsApp Web...")
            page.goto('https://web.whatsapp.com', timeout=60000)

            print()
            print("🔍 Waiting for QR code...")
            print("   Please scan the QR code with your mobile device")
            print()

            # Wait for QR code to appear
            try:
                page.wait_for_selector(
                    'canvas[aria-label="Scan this QR code to link a device!"]',
                    timeout=30000
                )
                print("✅ QR code displayed")
                print()
            except PlaywrightTimeout:
                print("⚠️  QR code not found - you may already be logged in")
                print()

            # Wait for login success
            print("⏳ Waiting for login...")
            print("   This may take a minute...")
            print()

            try:
                page.wait_for_selector(
                    'div[data-testid="default-user"]',
                    timeout=120000  # 2 minutes
                )

                print()
                print("✅ Login successful!")
                print("   Session saved to:", session_path)
                print()

                # Keep browser open for a moment to ensure session is saved
                print("💾 Saving session...")
                page.wait_for_timeout(3000)

                browser.close()

                print()
                print("✅ WhatsApp Web setup complete!")
                print()
                print("Next steps:")
                print("   1. Test the connection: python silver/scripts/test_watchers.sh whatsapp")
                print("   2. Start the watcher: python -m silver.src.watchers.whatsapp_watcher")
                print()
                print("Note: The session will remain active until you log out from")
                print("      WhatsApp Web or unlink the device from your phone.")
                print()

            except PlaywrightTimeout:
                print()
                print("❌ Login timeout - QR code was not scanned in time")
                print()
                print("Please try again:")
                print("   python silver/scripts/setup_whatsapp.py")
                print()
                browser.close()
                sys.exit(1)

    except Exception as e:
        print()
        print(f"❌ Setup failed: {e}")
        print()
        print("Troubleshooting:")
        print("   1. Make sure Playwright is installed:")
        print("      pip install playwright")
        print("      playwright install chromium")
        print()
        print("   2. Check if port 3000 is available")
        print()
        print("   3. Try running with --no-sandbox:")
        print("      This script already uses --no-sandbox flag")
        print()
        sys.exit(1)


def main():
    """Main entry point."""
    # Get vault path from environment or use default
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )

    setup_whatsapp_session(vault_path)


if __name__ == "__main__":
    main()
