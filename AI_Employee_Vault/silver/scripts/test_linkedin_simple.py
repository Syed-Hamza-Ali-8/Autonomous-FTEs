#!/usr/bin/env python3
"""
Simple LinkedIn posting test with better modal handling.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster

def main():
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    
    print("🔵 LinkedIn Simple Test")
    print()
    
    # Generate content
    poster = LinkedInPoster(vault_path)
    content = """🚀 Testing AI automation workflow!

This post was generated and posted automatically by my AI Employee system.

#AIAutomation #Testing"""
    
    print("📝 Post content:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    print()
    
    input("Press Enter to post to LinkedIn (browser will open)...")
    
    # Post
    result = poster.post_update(content)
    
    if result["success"]:
        print("✅ Posted successfully!")
        print(f"   Check your LinkedIn profile")
    else:
        print(f"❌ Failed: {result.get('error')}")
        print(f"   {result.get('message', '')}")
        print()
        print("💡 Check screenshot: silver/Logs/linkedin_post_failed.png")

if __name__ == "__main__":
    main()
