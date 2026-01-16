# Planning Guidelines

## Overview

This document provides comprehensive guidelines for creating effective plans using the create-plans skill.

## When to Create a Plan

### Create a Plan When:

1. **Task has 3+ distinct steps**
   - Example: "Implement user authentication" → Database, API, UI, Testing

2. **Task has dependencies**
   - Example: "Deploy application" → Build → Test → Deploy → Monitor

3. **Task has significant risks**
   - Example: "Migrate database" → Data loss risk, downtime risk

4. **Task requires coordination**
   - Example: "Launch new feature" → Multiple teams, external dependencies

5. **Task is unclear or ambiguous**
   - Example: "Improve performance" → Need to identify bottlenecks first

### Don't Create a Plan When:

1. **Task is simple and straightforward**
   - Example: "Fix typo in README" → Just do it

2. **Task is already well-defined**
   - Example: "Run tests" → Single command, no planning needed

3. **Task is exploratory**
   - Example: "Research options" → Exploration first, plan later

## Plan Structure

### Essential Sections

1. **Objective**: Clear, measurable goal
2. **Context**: Background information, constraints, requirements
3. **Steps**: Ordered list of tasks with dependencies
4. **Risks**: Potential issues and mitigation strategies
5. **Success Criteria**: Measurable outcomes

### Optional Sections

- **Timeline**: Estimated dates (if time-sensitive)
- **Resources**: Required tools, people, budget
- **Alternatives**: Other approaches considered
- **Rollback Plan**: How to undo if things go wrong

## Step Definition

Each step should include:

```markdown
### N. Step Title

- **Description**: What needs to be done (1-2 sentences)
- **Dependencies**: What must be complete first
- **Estimated Effort**: Time estimate (hours/days)
- **Status**: ⏳ Pending | 🔄 In Progress | ✅ Completed | ❌ Blocked
- **Success Criteria**: Measurable outcomes (checkboxes)
```

### Good Step Examples

✅ **Good**: "Implement JWT token generation with 15-minute expiration and refresh token support"
- Clear, specific, measurable

✅ **Good**: "Design database schema with user, role, and permission tables including foreign keys"
- Concrete deliverable, clear scope

❌ **Bad**: "Work on authentication"
- Too vague, no clear outcome

❌ **Bad**: "Make it better"
- Not measurable, unclear

## Dependency Mapping

### Dependency Types

1. **Sequential**: Step B requires Step A to be complete
   ```
   Step A → Step B → Step C
   ```

2. **Parallel**: Steps can run simultaneously
   ```
   Step A → Step C
   Step B → Step C
   ```

3. **Conditional**: Step depends on outcome of previous step
   ```
   Step A → Decision → Step B (if yes)
                    → Step C (if no)
   ```

### Dependency Graph Format

```
Step 1 (Database) → Step 2 (API) → Step 4 (Integration)
                 → Step 3 (UI)  → Step 4 (Integration)
```

## Risk Assessment

### Risk Template

```markdown
### Risk Title

- **Description**: What could go wrong
- **Mitigation**: How to prevent or minimize
- **Probability**: Low | Medium | High
- **Impact**: Low | Medium | High | Critical
```

### Common Risks

1. **Technical Risks**
   - Dependency conflicts
   - Performance issues
   - Security vulnerabilities
   - Integration failures

2. **Process Risks**
   - Scope creep
   - Timeline delays
   - Resource unavailability
   - Communication breakdowns

3. **External Risks**
   - Third-party API changes
   - Service outages
   - Regulatory changes
   - Market shifts

## Success Criteria

### SMART Criteria

- **Specific**: Clearly defined outcome
- **Measurable**: Can verify completion
- **Achievable**: Realistic given constraints
- **Relevant**: Aligned with objective
- **Time-bound**: Has deadline (if applicable)

### Good Success Criteria Examples

✅ "All 7 steps completed and tested"
✅ "90%+ test coverage for authentication code"
✅ "API response time < 200ms for 95th percentile"
✅ "Zero critical security vulnerabilities in audit"

❌ "Code is good quality" (not measurable)
❌ "Users are happy" (too vague)
❌ "Everything works" (not specific)

## Complexity Assessment

### Complexity Scoring

Calculate complexity score based on:

```python
complexity_score = (
    num_steps * 10 +
    num_dependencies * 5 +
    num_risks * 3 +
    external_dependencies * 10
)
```

### Complexity Levels

- **0-30**: Low (simple task, 1-2 steps)
- **31-70**: Medium (moderate task, 3-5 steps)
- **71-150**: High (complex task, 6-10 steps)
- **151+**: Very High (major project, 10+ steps)

## Effort Estimation

### Estimation Guidelines

- **1 hour**: Simple implementation, no dependencies
- **2-4 hours**: Moderate implementation, some research needed
- **1 day**: Complex implementation, multiple components
- **2-3 days**: Major feature, integration required
- **1 week+**: Large project, multiple phases

### Estimation Factors

Consider:
- Implementation time
- Testing time
- Documentation time
- Review/approval time
- Buffer for unknowns (20-30%)

## Progress Tracking

### Status Values

- **draft**: Plan created, not started
- **in_progress**: Work has begun
- **blocked**: Cannot proceed (dependency or issue)
- **completed**: All steps done, success criteria met
- **cancelled**: Plan abandoned

### Updating Progress

Update plan file regularly:
1. Change step status as work progresses
2. Update `updated_at` timestamp
3. Update `completed_steps` count
4. Add notes on blockers or issues
5. Adjust estimates if needed

## Best Practices

1. **Start with objective**: Know what success looks like
2. **Break down into small steps**: Each step should be 1-4 hours
3. **Identify dependencies early**: Avoid blockers later
4. **Be realistic about risks**: Better to over-prepare
5. **Make success criteria measurable**: Can't manage what you can't measure
6. **Update regularly**: Plans are living documents
7. **Review and reflect**: Learn from completed plans

## Anti-Patterns

❌ **Too detailed**: Plan becomes outdated quickly
❌ **Too vague**: Plan doesn't provide guidance
❌ **No dependencies**: Leads to blockers and delays
❌ **No risks**: Surprises derail execution
❌ **No success criteria**: Don't know when done
❌ **Never updated**: Plan becomes irrelevant

## Examples

### Simple Task (No Plan Needed)

**Task**: "Fix typo in README.md"
**Action**: Just fix it, no plan needed

### Medium Task (Plan Recommended)

**Task**: "Add email notifications for new messages"
**Plan**:
1. Design email template
2. Implement email sending via SMTP
3. Add notification triggers
4. Test with real emails
5. Deploy and monitor

### Complex Task (Plan Required)

**Task**: "Implement user authentication system"
**Plan**: See `examples/sample_plan.md` for full example

## References

- [SMART Criteria](https://en.wikipedia.org/wiki/SMART_criteria)
- [Risk Management](https://en.wikipedia.org/wiki/Risk_management)
- [Project Planning](https://en.wikipedia.org/wiki/Project_planning)
