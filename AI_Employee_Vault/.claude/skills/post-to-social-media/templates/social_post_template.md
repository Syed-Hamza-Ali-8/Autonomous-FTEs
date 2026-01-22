# Social Post Template

Use this template to create social media posts for approval.

## Template Structure

```markdown
---
id: social_post_YYYYMMDD_HHMMSS_xxxxx
type: social_media_post
status: pending_approval
created_at: YYYY-MM-DDTHH:MM:SSZ
timeout_at: YYYY-MM-DDTHH:MM:SSZ
platforms:
  - facebook
  - instagram
  - twitter
image_path: null  # Optional: path to image file
---

# Social Media Post Draft

**Status**: ⏳ Pending Approval
**Created**: [Human-readable timestamp]
**Platforms**: [Comma-separated list]

## Content

[Your post content here]

[Call to action]

#Hashtag1 #Hashtag2 #Hashtag3

## Platform-Specific Previews

### Facebook
[Full content - Facebook has 63,206 character limit]

### Instagram
[Full content - Instagram has 2,200 character limit]
[Hashtags optimized - max 30 hashtags]

### Twitter
[Truncated to 280 characters if needed]
[Hashtags count toward character limit]

## Platform Details

- **Facebook**: [X] / 63,206 characters
- **Instagram**: [X] / 2,200 characters ([Y] hashtags)
- **Twitter**: [X] / 280 characters

## Instructions

**To Approve**:
1. Review content above
2. Edit if needed (changes apply to all platforms)
3. Change `status: pending_approval` to `status: approved`
4. Save file
5. Post executes automatically within 1 minute

**To Reject**:
1. Change `status: pending_approval` to `status: rejected`
2. Add `rejection_reason: "Your reason"` to frontmatter
3. Save file

**To Edit**:
- Edit the content section directly
- Platform-specific optimizations will be reapplied
- Save and approve when ready

## Timeout

If no response within 24 hours, this draft will expire.
```

## Content Guidelines

### Opening Hook
- Start with emoji or attention-grabbing statement
- Examples: 🚀, 💡, 🎉, ⚡, 🔥

### Body (2-3 sentences)
- Focus on value proposition
- Use concrete numbers when possible
- Keep it conversational and authentic

### Call to Action
- Ask a question
- Invite engagement (comment, DM, share)
- Provide next steps

### Hashtags
- 3-5 hashtags for Facebook/Twitter
- Up to 30 for Instagram (but 5-10 recommended)
- Mix popular and niche hashtags
- Relevant to content and audience

## Platform-Specific Tips

### Facebook
- Longer content performs well
- Questions drive engagement
- Video/images boost reach
- Best times: 1-4 PM weekdays

### Instagram
- Visual content is king
- Hashtags are critical
- First 125 characters show in feed
- Best times: 11 AM - 1 PM weekdays

### Twitter
- Brevity is key (280 chars)
- Threads for longer content
- Hashtags: 1-2 max
- Best times: 8-10 AM, 6-9 PM

## Example Content Templates

### Product Launch
```
🚀 [Product Name] is here!

[1-2 sentences about what it does and why it matters]

[Call to action: Try it, learn more, etc.]

#ProductLaunch #Innovation #[Industry]
```

### Customer Success Story
```
💡 How [Customer Name] achieved [Result]

[2-3 sentences about their challenge and solution]

Want similar results? [Call to action]

#CustomerSuccess #CaseStudy #[Industry]
```

### Industry Insight
```
📊 Did you know? [Interesting statistic]

[2-3 sentences expanding on the insight]

What's your experience? Share below!

#IndustryInsights #[Topic] #Business
```

### Behind the Scenes
```
👀 Behind the scenes at [Company Name]

[2-3 sentences about your process, team, or culture]

Follow for more insights!

#BehindTheScenes #CompanyCulture #[Industry]
```

## Variables to Replace

- `YYYYMMDD_HHMMSS`: Current date and time
- `xxxxx`: Random 5-character ID
- `[Your post content here]`: Actual post content
- `[Human-readable timestamp]`: e.g., "2026-01-19 2:30 PM"
- `[Comma-separated list]`: e.g., "Facebook, Instagram, Twitter"
- `[X]`: Character count
- `[Y]`: Hashtag count

## Validation Checklist

Before approving, verify:
- [ ] Content is appropriate for all selected platforms
- [ ] No typos or grammatical errors
- [ ] Hashtags are relevant and properly formatted
- [ ] Character limits respected for each platform
- [ ] Call to action is clear
- [ ] Tone matches brand voice
- [ ] No sensitive or controversial content
- [ ] Links work (if included)
- [ ] Image is appropriate (if included)
