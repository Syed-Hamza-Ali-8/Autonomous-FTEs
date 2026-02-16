# Escalation Rules for Customer Success AI Agent

## Overview

This document defines when the AI agent should escalate customer inquiries to human support agents. The goal is to handle as many inquiries autonomously as possible while ensuring customers receive appropriate human attention when needed.

**Target Escalation Rate:** <25% of all tickets

---

## Automatic Escalation Triggers

### 1. Billing & Financial Issues

**ALWAYS ESCALATE:**
- Refund requests
- Disputed charges or double billing
- Payment failures requiring manual intervention
- Subscription cancellation requests (retain customer)
- Pricing inquiries for Enterprise plans
- Invoice requests for accounting purposes

**Reason:** Financial matters require human judgment, legal compliance, and customer retention efforts.

**Urgency:** High (respond within 4 hours)

**Example Triggers:**
- Keywords: "refund", "charged twice", "billing error", "cancel subscription", "enterprise pricing"
- Customer explicitly mentions money, charges, or payment issues

---

### 2. Negative Sentiment

**ESCALATE IF:**
- Sentiment score < 0.3 (on scale of 0-1)
- Customer uses profanity or aggressive language
- Customer expresses extreme frustration or anger
- Customer threatens to leave or mentions competitors
- Multiple failed resolution attempts (>2 back-and-forth exchanges)

**Reason:** Frustrated customers need empathetic human interaction to prevent churn.

**Urgency:** High (respond within 2 hours)

**Example Phrases:**
- "This is ridiculous"
- "I'm extremely frustrated"
- "I'm switching to [competitor]"
- "This is unacceptable"
- "I want to speak to a manager"
- Profanity or caps lock abuse

---

### 3. Legal or Compliance Mentions

**ALWAYS ESCALATE:**
- GDPR or data privacy requests
- Legal threats or mentions of lawyers
- Compliance or regulatory questions
- Data deletion requests (right to be forgotten)
- Security breach reports
- Terms of service disputes

**Reason:** Legal matters require specialized knowledge and documentation.

**Urgency:** Critical (respond within 1 hour)

**Example Triggers:**
- Keywords: "lawyer", "legal", "GDPR", "privacy", "delete my data", "sue", "compliance", "regulation"

---

### 4. Complex Technical Issues

**ESCALATE IF:**
- Issue requires access to backend systems or databases
- Bug affects multiple users (potential system-wide issue)
- Data loss or corruption reported
- Security vulnerability reported
- Integration issues requiring developer investigation
- API or webhook configuration problems

**Reason:** Technical issues beyond standard troubleshooting need engineering expertise.

**Urgency:** High (respond within 4 hours)

**Example Scenarios:**
- "All my tasks disappeared"
- "API returning 500 errors"
- "Data not syncing across devices"
- "Security vulnerability in [feature]"

---

### 5. Explicit Human Request

**ALWAYS ESCALATE:**
- Customer explicitly asks to speak with a human
- Customer asks for a manager or supervisor
- Customer says "I want to talk to a real person"
- Customer expresses dissatisfaction with AI assistance

**Reason:** Respect customer preference and autonomy.

**Urgency:** Normal (respond within 12 hours)

**Example Phrases:**
- "Can I speak to a human?"
- "I need to talk to someone"
- "Connect me with a real person"
- "I don't want to talk to a bot"

---

### 6. Knowledge Search Failure

**ESCALATE IF:**
- No relevant knowledge base articles found (relevance score < 0.5)
- Customer question is outside documented product scope
- Customer asks about unreleased features or roadmap
- Question requires internal company information

**Reason:** Cannot provide accurate information without knowledge base coverage.

**Urgency:** Normal (respond within 12 hours)

**Example Scenarios:**
- Questions about features not in documentation
- "When will [feature] be released?"
- "What's on your product roadmap?"
- Questions about company strategy or internal processes

---

### 7. Sales Opportunities

**ESCALATE IF:**
- Enterprise plan inquiries (>50 users)
- Custom pricing requests
- Partnership or reseller inquiries
- Large-scale deployment questions
- RFP or procurement process mentions

**Reason:** Sales opportunities require personalized attention and negotiation.

**Urgency:** High (respond within 4 hours)

**Example Triggers:**
- Keywords: "enterprise", "custom pricing", "partnership", "reseller", "procurement", "RFP"
- Mentions of large user counts (>50)

---

## Do NOT Escalate

### Handle Autonomously:

1. **Standard Feature Questions**
   - How to use documented features
   - Navigation and UI questions
   - Best practices for common workflows

2. **Simple Technical Issues**
   - Password resets
   - Login problems (with standard troubleshooting)
   - Browser cache/cookie issues
   - App reinstallation guidance

3. **Account Management**
   - Email address changes
   - Profile updates
   - Notification settings
   - Timezone changes

4. **General Product Information**
   - Feature availability by plan
   - Storage limits
   - Integration capabilities
   - Mobile app availability

5. **Positive Feedback**
   - Thank you messages
   - Feature compliments
   - General positive sentiment

---

## Escalation Process

### Step 1: Assess Escalation Need
- Check against all escalation triggers
- Calculate sentiment score
- Evaluate knowledge base search results
- Consider conversation history

### Step 2: Prepare Escalation Context
- Summarize customer issue (2-3 sentences)
- Include sentiment score
- List attempted solutions
- Provide conversation history
- Note customer details (plan, account age, previous tickets)

### Step 3: Execute Escalation
- Use `escalate_to_human` tool with appropriate reason
- Set urgency level (low, normal, high, critical)
- Notify customer of escalation
- Create ticket with "escalated" status

### Step 4: Customer Communication
**Template:**
```
I understand this requires specialized attention. I'm escalating your request to our human support team who will reach out to you within [timeframe].

Your ticket reference: [TICKET_ID]

In the meantime, is there anything else I can help you with?
```

---

## Escalation Metrics

### Track and Monitor:
- **Escalation Rate:** % of tickets escalated (target: <25%)
- **Escalation Reason Distribution:** Which triggers are most common
- **False Escalations:** Tickets that could have been handled by AI
- **Missed Escalations:** Tickets that should have been escalated but weren't
- **Time to Escalation:** How quickly escalations are identified

### Weekly Review:
- Analyze escalation patterns
- Identify opportunities to reduce escalations
- Update knowledge base to cover gaps
- Refine sentiment thresholds
- Adjust escalation rules based on outcomes

---

## Special Cases

### After-Hours Escalations
- During off-hours (6 PM - 9 AM PST), set expectations appropriately
- "Our human support team will respond when they're back online (9 AM PST)"
- For critical issues, provide emergency contact if available

### Repeat Customers
- If customer has >3 escalations in past 30 days, automatically escalate
- Indicates complex needs or dissatisfaction requiring human relationship

### VIP Customers
- Enterprise plan customers get priority escalation
- Customers with >100 users get dedicated support
- Long-term customers (>2 years) get preferential treatment

### Multi-Channel Escalations
- If customer contacts via multiple channels about same issue, escalate
- Indicates high urgency or frustration

---

## Continuous Improvement

### Monthly Review Process:
1. Analyze escalation data
2. Identify patterns in escalated tickets
3. Update knowledge base to reduce future escalations
4. Refine sentiment analysis thresholds
5. Add new escalation rules if needed
6. Remove rules that cause false positives

### Success Criteria:
- Escalation rate trending downward over time
- Customer satisfaction remains >85% for both AI and human interactions
- Reduced time to resolution for escalated tickets
- Fewer repeat escalations for same customer

---

## Emergency Escalation

**Immediate Escalation (No AI Response):**
- System outage reports affecting multiple users
- Security breach or data leak reports
- Payment processing failures
- Critical bugs causing data loss

**Process:**
1. Immediately create high-priority ticket
2. Notify on-call engineer via PagerDuty
3. Send automated acknowledgment to customer
4. Do not attempt AI resolution

---

## Notes for AI Agent

- **When in doubt, escalate.** It's better to over-escalate than under-escalate.
- **Always explain why you're escalating** to set customer expectations.
- **Provide ticket reference** so customer can track escalation.
- **Offer to help with other issues** while they wait for human response.
- **Be empathetic** when escalating due to negative sentiment.
- **Thank customers** for their patience and understanding.
