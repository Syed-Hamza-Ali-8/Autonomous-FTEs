# Complexity Assessment

## Overview

This document provides a systematic approach to assessing task complexity to determine whether a plan is needed.

## Complexity Factors

### 1. Number of Steps

**Weight**: 10 points per step

- **1-2 steps**: Simple task (10-20 points)
- **3-5 steps**: Moderate task (30-50 points)
- **6-10 steps**: Complex task (60-100 points)
- **10+ steps**: Very complex task (100+ points)

### 2. Dependencies

**Weight**: 5 points per dependency

- **No dependencies**: Can start immediately (0 points)
- **1-2 dependencies**: Some coordination needed (5-10 points)
- **3-5 dependencies**: Significant coordination (15-25 points)
- **5+ dependencies**: High coordination overhead (25+ points)

### 3. Risks

**Weight**: 3 points per risk

- **No risks**: Straightforward execution (0 points)
- **1-2 risks**: Some uncertainty (3-6 points)
- **3-5 risks**: Moderate uncertainty (9-15 points)
- **5+ risks**: High uncertainty (15+ points)

### 4. External Dependencies

**Weight**: 10 points per external dependency

- **No external deps**: Self-contained (0 points)
- **1-2 external deps**: Some external coordination (10-20 points)
- **3+ external deps**: High external coordination (30+ points)

### 5. Technical Complexity

**Weight**: Variable (0-50 points)

- **Routine work**: Known patterns, well-understood (0-10 points)
- **Moderate complexity**: Some new concepts (10-25 points)
- **High complexity**: Novel approach, research needed (25-50 points)

### 6. Reversibility

**Weight**: Variable (0-20 points)

- **Fully reversible**: Can undo easily (0 points)
- **Partially reversible**: Some cleanup needed (5-10 points)
- **Irreversible**: Cannot undo (10-20 points)

## Complexity Score Calculation

```python
def calculate_complexity_score(task):
    score = 0

    # Number of steps
    score += task.num_steps * 10

    # Dependencies
    score += task.num_dependencies * 5

    # Risks
    score += task.num_risks * 3

    # External dependencies
    score += task.num_external_deps * 10

    # Technical complexity
    if task.technical_complexity == "routine":
        score += 5
    elif task.technical_complexity == "moderate":
        score += 20
    elif task.technical_complexity == "high":
        score += 40

    # Reversibility
    if task.reversibility == "none":
        score += 20
    elif task.reversibility == "partial":
        score += 10

    return score
```

## Complexity Levels

### Level 1: Simple (0-30 points)

**Characteristics**:
- 1-2 steps
- No dependencies
- No significant risks
- Routine work
- Fully reversible

**Examples**:
- Fix typo in documentation
- Update configuration value
- Run existing test suite
- Read file and extract data

**Recommendation**: No plan needed, execute directly

### Level 2: Moderate (31-70 points)

**Characteristics**:
- 3-5 steps
- 1-2 dependencies
- 1-2 minor risks
- Some new concepts
- Mostly reversible

**Examples**:
- Add new API endpoint
- Implement email notifications
- Create database migration
- Add unit tests for module

**Recommendation**: Simple plan recommended (1-2 paragraphs)

### Level 3: Complex (71-150 points)

**Characteristics**:
- 6-10 steps
- 3-5 dependencies
- 3-5 moderate risks
- Novel approach needed
- Partially reversible

**Examples**:
- Implement authentication system
- Migrate to new database
- Integrate third-party API
- Refactor major component

**Recommendation**: Detailed plan required (full template)

### Level 4: Very Complex (151+ points)

**Characteristics**:
- 10+ steps
- 5+ dependencies
- 5+ significant risks
- High technical complexity
- Irreversible or high-impact

**Examples**:
- Build new microservice
- Implement distributed system
- Major architecture refactor
- Production data migration

**Recommendation**: Comprehensive plan + risk analysis + review

## Assessment Examples

### Example 1: Fix Typo

```python
task = {
    "num_steps": 1,
    "num_dependencies": 0,
    "num_risks": 0,
    "num_external_deps": 0,
    "technical_complexity": "routine",
    "reversibility": "full"
}

score = 1*10 + 0*5 + 0*3 + 0*10 + 5 + 0 = 15
level = "Simple"
recommendation = "No plan needed"
```

### Example 2: Add Email Notifications

```python
task = {
    "num_steps": 4,  # Template, SMTP, Triggers, Testing
    "num_dependencies": 1,  # Needs SMTP credentials
    "num_risks": 2,  # Email delivery, spam filters
    "num_external_deps": 1,  # SMTP server
    "technical_complexity": "moderate",
    "reversibility": "full"
}

score = 4*10 + 1*5 + 2*3 + 1*10 + 20 + 0 = 81
level = "Complex"
recommendation = "Detailed plan required"
```

### Example 3: Implement Authentication

```python
task = {
    "num_steps": 7,  # DB, Hashing, JWT, OAuth2, RBAC, API, Security
    "num_dependencies": 4,  # DB → Hashing → JWT → OAuth2/RBAC
    "num_risks": 3,  # Security, OAuth rate limits, migrations
    "num_external_deps": 2,  # Google OAuth, GitHub OAuth
    "technical_complexity": "high",
    "reversibility": "partial"
}

score = 7*10 + 4*5 + 3*3 + 2*10 + 40 + 10 = 149
level = "Complex (near Very Complex)"
recommendation = "Comprehensive plan + security review"
```

## Decision Tree

```
Task Received
    ↓
Calculate Complexity Score
    ↓
Score < 30? → Yes → Execute directly (no plan)
    ↓ No
Score < 70? → Yes → Create simple plan (1-2 paragraphs)
    ↓ No
Score < 150? → Yes → Create detailed plan (full template)
    ↓ No
Score ≥ 150? → Yes → Create comprehensive plan + risk analysis + review
```

## Adjustments

### Increase Complexity If:

- User is unfamiliar with domain (+20 points)
- Production system affected (+20 points)
- Multiple teams involved (+15 points)
- Tight deadline (+10 points)
- Regulatory compliance required (+15 points)

### Decrease Complexity If:

- Similar task done before (-10 points)
- Good documentation available (-10 points)
- Automated testing in place (-5 points)
- Rollback mechanism exists (-10 points)

## Validation

After calculating complexity score, validate with these questions:

1. **Can this be done in one sitting?** (If yes, probably simple)
2. **Do I need to coordinate with others?** (If yes, increase complexity)
3. **What's the worst that could happen?** (If severe, increase complexity)
4. **Have I done this before?** (If yes, decrease complexity)
5. **Is there a clear path forward?** (If no, increase complexity)

## Best Practices

1. **When in doubt, create a plan**: Better to over-plan than under-plan
2. **Reassess during execution**: Complexity may change as you learn more
3. **Document assumptions**: Complexity depends on context
4. **Learn from experience**: Track actual vs estimated complexity
5. **Adjust thresholds**: Tune scoring based on your experience

## References

- [Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Cognitive Complexity](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)
- [Estimation Techniques](https://en.wikipedia.org/wiki/Estimation_(project_management))
