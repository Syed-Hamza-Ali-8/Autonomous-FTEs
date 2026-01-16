# LinkedIn Post Template

This template defines the structure for LinkedIn business posts.

## Basic Post Structure

```markdown
[HOOK] (1 line - attention grabber)

[BODY] (2-3 sentences - value delivery)

[CALL_TO_ACTION] (1 line - engagement prompt)

[HASHTAGS] (3-5 relevant tags)
```

## Template Variables

### Hook Variables
- `{{EMOJI}}` - Relevant emoji (🚀, 💡, 📊, etc.)
- `{{OPENING}}` - Opening phrase
- `{{TOPIC}}` - Main topic

### Body Variables
- `{{VALUE_PROP}}` - Value proposition
- `{{DETAILS}}` - Supporting details
- `{{BENEFIT}}` - Key benefit

### CTA Variables
- `{{ACTION}}` - Desired action
- `{{ENGAGEMENT}}` - Engagement prompt

### Hashtag Variables
- `{{HASHTAG_1}}` - Primary hashtag
- `{{HASHTAG_2}}` - Secondary hashtag
- `{{HASHTAG_3}}` - Tertiary hashtag

## Template Examples

### Template A: Success Story

```
{{EMOJI}} Quick update on our {{TOPIC}} initiative:

✅ {{ACHIEVEMENT_1}}
✅ {{ACHIEVEMENT_2}}
✅ {{ACHIEVEMENT_3}}

Ready to transform your {{AREA}}? {{CTA}}

{{HASHTAGS}}
```

**Example**:
```
📊 Quick update on our workflow optimization initiative:

✅ Streamlined communication workflows
✅ Reduced manual tasks by 70%
✅ Improved response times

Ready to transform your business operations? DM me to learn more!

#Automation #Efficiency #Sales
```

### Template B: Insight Sharing

```
{{EMOJI}} Key insight from this week: {{TOPIC}}

{{INSIGHT_DESCRIPTION}}

{{QUESTION}}

{{HASHTAGS}}
```

**Example**:
```
💡 Key insight from this week: business productivity

The most productive teams aren't working harder—they're
working smarter with the right automation tools.

What's your productivity secret?

#Productivity #BusinessGrowth #Efficiency
```

### Template C: Announcement

```
{{EMOJI}} Excited to share {{ANNOUNCEMENT}}!

{{DESCRIPTION}}

{{CTA}}

{{HASHTAGS}}
```

**Example**:
```
🚀 Excited to share our latest progress in AI automation!

We're building innovative solutions that help businesses
automate their workflows and increase productivity.

Interested in learning more? Let's connect!

#Business #Automation #Innovation
```

### Template D: Question/Engagement

```
{{EMOJI}} Question for the community:

{{QUESTION}}

{{CONTEXT}}

Share your experience in the comments!

{{HASHTAGS}}
```

**Example**:
```
🤔 Question for the community:

What's your biggest challenge with workflow automation?

We're researching common pain points to build better solutions.

Share your experience in the comments!

#Automation #Business #Productivity
```

## Character Limits

- **Optimal length**: 150-300 characters
- **Maximum length**: 3,000 characters
- **Hashtags**: 3-5 tags
- **Emojis**: 1-2 maximum

## Usage in Code

### Python Implementation

```python
def generate_post_from_template(template_name, variables):
    """Generate post from template."""
    templates = {
        "success_story": """
{{EMOJI}} Quick update on our {{TOPIC}} initiative:

✅ {{ACHIEVEMENT_1}}
✅ {{ACHIEVEMENT_2}}
✅ {{ACHIEVEMENT_3}}

Ready to transform your {{AREA}}? {{CTA}}

{{HASHTAGS}}
        """,

        "insight": """
{{EMOJI}} Key insight from this week: {{TOPIC}}

{{INSIGHT}}

{{QUESTION}}

{{HASHTAGS}}
        """,

        "announcement": """
{{EMOJI}} Excited to share {{ANNOUNCEMENT}}!

{{DESCRIPTION}}

{{CTA}}

{{HASHTAGS}}
        """
    }

    template = templates.get(template_name)

    # Replace variables
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", value)

    return template.strip()
```

### Example Usage

```python
# Success story post
post = generate_post_from_template("success_story", {
    "EMOJI": "📊",
    "TOPIC": "AI automation",
    "ACHIEVEMENT_1": "Streamlined workflows",
    "ACHIEVEMENT_2": "Reduced manual tasks by 70%",
    "ACHIEVEMENT_3": "Improved response times",
    "AREA": "business operations",
    "CTA": "DM me to learn more!",
    "HASHTAGS": "#Automation #Efficiency #Sales"
})

print(post)
```

## Template Selection Logic

```python
def select_template(topic, post_count):
    """Select template based on topic and rotation."""
    templates = ["success_story", "insight", "announcement", "question"]

    # Rotate through templates
    template_index = post_count % len(templates)

    return templates[template_index]
```

## Customization

### Adding New Templates

1. Define template structure
2. Identify required variables
3. Add to templates dictionary
4. Test with sample data
5. Document in this file

### Template Best Practices

- ✅ Keep templates flexible
- ✅ Use clear variable names
- ✅ Provide example values
- ✅ Test with real content
- ✅ Maintain consistent structure

## Validation

### Pre-Post Checklist

- [ ] All variables replaced
- [ ] Character count within limits
- [ ] 3-5 hashtags included
- [ ] CTA present
- [ ] Professional tone
- [ ] No spelling errors

### Validation Function

```python
def validate_post(content):
    """Validate post before publishing."""
    errors = []

    # Check length
    if len(content) < 50:
        errors.append("Post too short (min 50 chars)")
    if len(content) > 3000:
        errors.append("Post too long (max 3000 chars)")

    # Check hashtags
    hashtag_count = content.count('#')
    if hashtag_count < 3:
        errors.append("Too few hashtags (min 3)")
    if hashtag_count > 5:
        errors.append("Too many hashtags (max 5)")

    # Check for unreplaced variables
    if "{{" in content or "}}" in content:
        errors.append("Unreplaced template variables found")

    return len(errors) == 0, errors
```

## Summary

**Template structure**:
```
Hook (1 line) → Body (2-3 sentences) → CTA (1 line) → Hashtags (3-5)
```

**Key principles**:
1. Start with attention-grabbing hook
2. Deliver value in body
3. Include clear call-to-action
4. Use 3-5 relevant hashtags
5. Keep within character limits

**Usage**:
1. Select appropriate template
2. Fill in variables
3. Validate content
4. Post to LinkedIn
