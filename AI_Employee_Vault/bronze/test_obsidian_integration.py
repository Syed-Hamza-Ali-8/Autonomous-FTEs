#!/usr/bin/env python3
"""
Test Obsidian Local REST API integration.

This script tests the connection and demonstrates graph view features.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from utils.obsidian_api import ObsidianAPI, create_wikilink, create_tag

def main():
    vault_path = Path.cwd()
    
    print("=" * 70)
    print("Obsidian Local REST API Integration Test")
    print("=" * 70)
    print()
    
    # Test 1: Initialize API
    print("Test 1: Initialize Obsidian API")
    print("-" * 70)
    api = ObsidianAPI(vault_path)
    print(f"  API Enabled: {api.enabled}")
    
    if not api.enabled:
        print("  ⚠️  API not configured")
        print()
        print("To enable Obsidian integration:")
        print("  1. Install 'Local REST API' plugin in Obsidian")
        print("  2. Copy API key from plugin settings")
        print("  3. Create .env file with: OBSIDIAN_API_KEY=your_key_here")
        print()
        print("The system will work without API, but with limited graph connections.")
        print()
        return
    
    print(f"  API URL: {api.api_url}")
    print(f"  Vault Name: {api.vault_name}")
    print()
    
    # Test 2: Check API availability
    print("Test 2: Check API Availability")
    print("-" * 70)
    is_available = api.is_available()
    
    if is_available:
        print("  ✅ SUCCESS! Obsidian API is reachable")
    else:
        print("  ❌ FAILED: Cannot reach Obsidian API")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Obsidian is running")
        print("  2. Open the bronze/ folder as a vault in Obsidian")
        print("  3. Enable 'Local REST API' plugin in Obsidian settings")
        print("  4. Check that API key in .env matches plugin settings")
        print()
        return
    
    print()
    
    # Test 3: Wikilink and Tag Creation
    print("Test 3: Wikilink and Tag Creation")
    print("-" * 70)
    
    # Test wikilinks
    link1 = create_wikilink("Dashboard")
    link2 = create_wikilink("test_file", "Test File")
    link3 = create_wikilink("Done/report", "Q4 Report")
    
    print(f"  Basic wikilink: {link1}")
    print(f"  With display text: {link2}")
    print(f"  With path: {link3}")
    
    # Test tags
    tag1 = create_tag("text")
    tag2 = create_tag("processed")
    tag3 = create_tag("#meeting")  # Should handle # prefix
    
    print(f"  Basic tag: {tag1}")
    print(f"  Status tag: {tag2}")
    print(f"  With # prefix: {tag3}")
    print()
    
    # Test 4: Get Active File
    print("Test 4: Get Active File in Obsidian")
    print("-" * 70)
    active_file = api.get_active_file()
    
    if active_file:
        print(f"  ✅ Active file: {active_file}")
    else:
        print("  ℹ️  No file currently active in Obsidian")
    print()
    
    # Test 5: Search Vault
    print("Test 5: Search Vault")
    print("-" * 70)
    results = api.search("Dashboard")
    
    if results:
        print(f"  ✅ Found {len(results)} result(s) for 'Dashboard'")
        for result in results[:3]:  # Show first 3
            print(f"    - {result.get('filename', 'Unknown')}")
    else:
        print("  ℹ️  No results found (vault might be empty)")
    print()
    
    # Summary
    print("=" * 70)
    print("✅ Obsidian Integration Test Complete")
    print("=" * 70)
    print()
    print("What This Enables:")
    print("  ✅ Real-time updates in Obsidian")
    print("  ✅ Automatic wikilinks for graph view")
    print("  ✅ Smart tagging by file type and status")
    print("  ✅ Rich connections between files")
    print()
    print("Next Steps:")
    print("  1. Process some files: .venv/bin/python3 test_manual_processing.py")
    print("  2. Run Agent Skill: .venv/bin/python3 .claude/skills/process-files/skill.py .")
    print("  3. Open Obsidian and press Ctrl+G to view the graph")
    print("  4. Explore connections between files!")
    print()
    print("Graph View Tips:")
    print("  - Exclude folders: src/, .claude/, tests/, .venv/")
    print("  - Filter by tags: #processed, #text, #meeting")
    print("  - Adjust forces: Repel=150, Link distance=100")
    print("  - Color by folder for visual organization")
    print()

if __name__ == "__main__":
    main()
