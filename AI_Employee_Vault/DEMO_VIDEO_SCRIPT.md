# Demo Video Script - AI Employee Vault (Gold Tier)

**Duration**: 10-12 minutes
**Audience**: Hackathon judges
**Goal**: Demonstrate autonomous AI Employee with HITL approval workflow

---

## 🎬 INTRO (1 minute)

**[Screen: Project folder structure]**

> "Hi! I'm presenting my AI Employee Vault - a Gold Tier autonomous business partner built with Claude Code, Obsidian, and multiple integrations."
>
> "This isn't just a chatbot - it's a complete autonomous system that monitors communications, manages finances, handles social media, and generates executive reports - all with human-in-the-loop approval."
>
> "Let me show you how it works across three tiers: Bronze, Silver, and Gold."

**[Show folder structure: bronze/, silver/, gold/]**

---

## 📧 BRONZE TIER: Foundation (1 minute)

**[Screen: bronze/ folder]**

> "Bronze Tier is the foundation - it monitors Gmail and processes files."

**[Open: bronze/scripts/gmail_watcher.py]**

> "The Gmail watcher connects via Google API, monitors my inbox, and creates action files in Obsidian."

**[Screen: Needs_Action/ folder with email files]**

> "Here you can see email files automatically created from my inbox. Each file contains the email content and suggested actions."

**Key Points**:
- Gmail API integration ✅
- File system monitoring ✅
- Obsidian vault integration ✅

---

## 🔵 SILVER TIER: Functional Assistant (2 minutes)

**[Screen: silver/ folder]**

> "Silver Tier adds LinkedIn, WhatsApp, and the human-in-the-loop approval workflow."

### LinkedIn Posting Demo

**[Screen: Pending_Approval/ folder]**

> "Here's an approval request for a LinkedIn post. The system generated this content and is asking for my approval."

**[Open: approval_*_post_linkedin.md]**

> "I can review the content in Obsidian. If I approve, I simply drag it to the Approved folder."

**[Drag file to Approved/]**

**[Screen: Terminal showing silver daemon]**

> "The daemon detects the approval and posts to LinkedIn automatically."

**[Screen: LinkedIn profile showing the post]**

> "And here's the post on LinkedIn - posted within seconds of my approval."

**Key Points**:
- LinkedIn automation with Playwright ✅
- WhatsApp messaging ✅
- Human-in-the-loop approval ✅
- Daemon runs 24/7 with cron ✅

---

## 🏆 GOLD TIER: Autonomous Employee (5 minutes)

**[Screen: gold/ folder]**

> "Gold Tier is where it becomes a true autonomous business partner. It integrates Odoo for accounting, manages social media across 3 platforms, and generates weekly CEO briefings."

### 1. Odoo Integration (1.5 minutes)

**[Screen: Docker containers]**

```bash
docker ps | grep odoo
```

> "I'm running Odoo Community Edition 19 in Docker - a full ERP system for financial management."

**[Screen: gold/mcp/odoo-mcp-python/]**

> "I built a custom MCP server with 7 tools that connect to Odoo via JSON-RPC APIs."

**[Open: gold/mcp/odoo-mcp-python/server.py]**

> "The MCP server provides tools for financial summaries, invoices, expenses, revenue tracking, and customer management."

**[Screen: Odoo web interface at localhost:8069]**

> "Here's Odoo running with the Accounting module. The system can query financial data, track invoices, and monitor expenses."

**Key Points**:
- Odoo Community Edition 19 ✅
- Custom MCP server ✅
- JSON-RPC API integration ✅
- 7 financial management tools ✅

### 2. Social Media Integration (2 minutes)

**[Screen: gold/scripts/social_media_daemon.py]**

> "For social media, I implemented the same HITL workflow as LinkedIn, but for Facebook, Instagram, and Twitter."

**[Terminal: Start daemon]**

```bash
python gold/scripts/social_media_daemon.py
```

> "The daemon watches the Approved folder for social media posts."

**[Screen: Pending_Approval/ folder]**

> "Here are three approval requests - one for each platform."

**[Open: approval_*_post_facebook.md]**

> "Let me review this Facebook post about our Gold Tier completion."

**[Drag to Approved/]**

**[Screen: Daemon terminal]**

> "The daemon detects the approval, posts to Facebook via API, and moves the file to Done."

**[Show terminal output]**

```
📝 APPROVED: approval_20260210_post_facebook.md
   Platform: FACEBOOK
🚀 Posting to FACEBOOK...
   ✅ Posted successfully!
   📁 Moved to Done/
```

**[Screen: Done/ folder]**

> "And the file is now in Done - the complete workflow took less than 2 seconds."

**Key Points**:
- Facebook integration ✅
- Instagram integration ✅
- Twitter integration ✅
- Same HITL workflow as Silver ✅
- Automatic posting within seconds ✅

### 3. CEO Briefing (1.5 minutes)

**[Screen: gold/src/intelligence/ceo_briefing.py]**

> "The CEO Briefing generator combines data from Odoo and social media to create weekly executive reports."

**[Terminal: Generate briefing]**

```bash
python gold/src/intelligence/ceo_briefing.py
```

**[Screen: Reports/CEO_Briefings/ceo_briefing_*.md]**

> "Here's the generated briefing. It shows financial performance, social media analytics, outstanding invoices, and proactive recommendations."

**[Scroll through briefing]**

> "It tells me:
> - Revenue: $12,450 with 42% profit margin
> - Social media: 47 posts with 5.18% engagement
> - Outstanding invoices: $4,500 - follow up with clients
> - Strong social engagement exceeding industry average"

**Key Points**:
- Combines financial + social data ✅
- Weekly automated generation ✅
- Proactive insights and recommendations ✅
- Action items from vault ✅

---

## 🛡️ PRODUCTION-READY FEATURES (1 minute)

**[Screen: gold/src/core/]**

> "The system is production-ready with error recovery and comprehensive logging."

**[Open: gold/src/core/error_recovery.py]**

> "Error recovery with exponential backoff ensures the system handles API failures gracefully."

**[Open: gold/src/core/audit_logger.py]**

> "All actions are logged with timestamps, metadata, and 90-day retention."

**[Screen: Logs/ folder]**

> "Every action is tracked - from email monitoring to social media posts to CEO briefing generation."

**Key Points**:
- Error recovery with retry logic ✅
- Exponential backoff ✅
- Comprehensive audit logging ✅
- Graceful degradation ✅

---

## 📊 ARCHITECTURE OVERVIEW (1 minute)

**[Screen: Architecture diagram from README]**

> "The architecture follows a clear pattern across all tiers:"

```
PERCEPTION → OBSIDIAN → APPROVAL → EXECUTION
```

> "Watchers monitor communications and create action files in Obsidian. I review and approve in my Obsidian vault. The system executes approved actions automatically."

> "This human-in-the-loop pattern ensures I maintain control while the system handles the heavy lifting."

**Key Points**:
- Modular architecture ✅
- Clear separation of concerns ✅
- Human-in-the-loop at every step ✅
- Scalable design ✅

---

## 🎯 HACKATHON REQUIREMENTS (30 seconds)

**[Screen: README.md requirements checklist]**

> "Let me show you the requirements checklist:"

**[Scroll through checklist]**

> "11 out of 12 requirements fully met - 91.7% completion:
> - All Silver requirements ✅
> - Odoo Community + MCP ✅
> - Facebook, Instagram, Twitter ✅
> - CEO Briefing ✅
> - Error recovery & logging ✅
> - Comprehensive documentation ✅"

---

## 🎬 CLOSING (30 seconds)

**[Screen: Project overview]**

> "To summarize: I built a complete autonomous AI Employee that:
> - Monitors Gmail, WhatsApp, and LinkedIn
> - Manages finances with Odoo
> - Posts to Facebook, Instagram, and Twitter
> - Generates weekly CEO briefings
> - All with human-in-the-loop approval"

> "The system runs 24/7 with automatic restarts, comprehensive logging, and production-ready error handling."

> "This is what an autonomous business partner looks like. Thank you!"

**[Screen: GitHub repository URL]**

---

## 📝 RECORDING TIPS

### Before Recording:
1. ✅ Close unnecessary applications
2. ✅ Clear browser history/cache
3. ✅ Prepare all terminals and windows
4. ✅ Test screen recording software
5. ✅ Have approval files ready in Pending_Approval/
6. ✅ Start daemons before recording
7. ✅ Practice the flow 1-2 times

### During Recording:
1. **Speak clearly and at moderate pace**
2. **Pause between sections** (easier to edit)
3. **Show, don't just tell** (demonstrate features)
4. **Keep cursor movements smooth**
5. **Zoom in on important code sections**
6. **Use terminal with large font** (readable in video)

### Screen Layout:
- **Left**: Terminal/Code editor
- **Right**: Obsidian vault
- **Bottom**: Browser (for LinkedIn, Odoo)

### Recording Software Options:
- **OBS Studio** (free, professional)
- **Loom** (easy, cloud-based)
- **QuickTime** (Mac)
- **Windows Game Bar** (Windows)

---

## ⏱️ TIMING BREAKDOWN

| Section | Duration | Key Points |
|---------|----------|------------|
| Intro | 1:00 | Project overview |
| Bronze Tier | 1:00 | Gmail, file monitoring |
| Silver Tier | 2:00 | LinkedIn, WhatsApp, HITL |
| Gold: Odoo | 1:30 | MCP server, JSON-RPC |
| Gold: Social Media | 2:00 | Facebook, Instagram, Twitter |
| Gold: CEO Briefing | 1:30 | Weekly reports |
| Production Features | 1:00 | Error recovery, logging |
| Architecture | 1:00 | System design |
| Requirements | 0:30 | Checklist |
| Closing | 0:30 | Summary |
| **TOTAL** | **12:00** | |

---

## 🎥 ALTERNATIVE: QUICK DEMO (5 minutes)

If you need a shorter version:

1. **Intro** (30s): Project overview
2. **HITL Workflow Demo** (2m): Show approval process for LinkedIn and Facebook
3. **CEO Briefing** (1m): Show generated report
4. **Architecture** (1m): Explain the pattern
5. **Closing** (30s): Requirements and summary

---

## 📋 POST-RECORDING CHECKLIST

After recording:
- [ ] Review video for audio quality
- [ ] Check screen visibility (text readable?)
- [ ] Add title slide (optional)
- [ ] Add captions/subtitles (optional)
- [ ] Upload to YouTube/Loom
- [ ] Set video to "Unlisted" or "Public"
- [ ] Copy video URL for submission form
- [ ] Test video link works

---

**Good luck with your demo! 🚀**

*Remember: Judges care about technical capability and working demos, not perfect production quality. Show your system working and explain your architecture clearly.*
