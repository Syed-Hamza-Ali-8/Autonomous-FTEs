# Create Plans Skill

**Skill ID**: create-plans
**Version**: 1.0.0
**User Story**: US4 - Intelligent Planning and Reasoning
**Priority**: P2

## Purpose

Generate structured Plan.md files for complex tasks using Claude's reasoning capabilities. This skill implements the **Reasoning** phase of the Perception → Reasoning → Action architecture, breaking down complex tasks into actionable steps with dependencies, risks, and success criteria.

## Capabilities

- **Task Analysis**: Analyze complex tasks and identify sub-tasks
- **Dependency Mapping**: Identify dependencies between tasks
- **Risk Assessment**: Identify potential risks and mitigation strategies
- **Success Criteria**: Define measurable success criteria
- **Plan Generation**: Create structured Plan.md files in Plans/ folder
- **Plan Tracking**: Track plan execution status and progress

## Architecture

### Core Components

1. **PlanGenerator** (`silver/src/planning/plan_generator.py`)
   - `generate_plan(task_description, context)` → plan_id
   - `analyze_complexity(task_description)` → complexity_score
   - `create_plan_file(plan_data)` → file_path

2. **TaskAnalyzer** (`silver/src/planning/task_analyzer.py`)
   - `break_down_task(task_description)` → List[SubTask]
   - `identify_dependencies(subtasks)` → DependencyGraph
   - `estimate_effort(subtask)` → effort_estimate

3. **PlanTracker** (`silver/src/planning/plan_tracker.py`)
   - `track_progress(plan_id)` → progress_percentage
   - `update_task_status(plan_id, task_id, status)` → success
   - `get_next_tasks(plan_id)` → List[Task]

### Planning Workflow

```
1. Task Received → Analyze Complexity → Simple or Complex?
                                      → Simple: Execute directly
                                      → Complex: Generate plan

2. Generate Plan → Break down into subtasks
                → Identify dependencies
                → Assess risks
                → Define success criteria
                → Create Plan.md file

3. Plan Created → Save to Plans/ folder
               → Notify user
               → Track execution status
```

## Configuration

### Plan Template (`silver/config/plan_template.md`)

```markdown
---
id: plan_{{TIMESTAMP}}_{{HASH}}
title: "{{PLAN_TITLE}}"
status: draft
created_at: {{CREATED_AT}}
complexity: {{COMPLEXITY}}
estimated_effort: {{EFFORT}}
---

# Plan: {{PLAN_TITLE}}

## Objective

{{OBJECTIVE_DESCRIPTION}}

## Context

{{CONTEXT_INFORMATION}}

## Steps

1. **{{STEP_1_TITLE}}**
   - Description: {{STEP_1_DESCRIPTION}}
   - Dependencies: {{STEP_1_DEPENDENCIES}}
   - Estimated effort: {{STEP_1_EFFORT}}
   - Success criteria: {{STEP_1_SUCCESS}}

2. **{{STEP_2_TITLE}}**
   - Description: {{STEP_2_DESCRIPTION}}
   - Dependencies: {{STEP_2_DEPENDENCIES}}
   - Estimated effort: {{STEP_2_EFFORT}}
   - Success criteria: {{STEP_2_SUCCESS}}

## Dependencies

- {{DEPENDENCY_1}}
- {{DEPENDENCY_2}}

## Risks

- **{{RISK_1_TITLE}}**: {{RISK_1_DESCRIPTION}}
  - Mitigation: {{RISK_1_MITIGATION}}
  - Probability: {{RISK_1_PROBABILITY}}
  - Impact: {{RISK_1_IMPACT}}

## Success Criteria

- [ ] {{SUCCESS_CRITERION_1}}
- [ ] {{SUCCESS_CRITERION_2}}

## Progress

- **Status**: {{STATUS}}
- **Completed Steps**: {{COMPLETED_STEPS}}/{{TOTAL_STEPS}}
- **Last Updated**: {{LAST_UPDATED}}
```

## Usage

### Generate Plan for Complex Task

```python
from silver.src.planning.plan_generator import PlanGenerator

generator = PlanGenerator(vault_path="/path/to/vault")

# Generate plan
plan_id = generator.generate_plan(
    task_description="Implement user authentication system with OAuth2",
    context={
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "requirements": ["OAuth2", "JWT tokens", "Role-based access"],
        "constraints": ["Must be production-ready", "Security first"]
    }
)

print(f"Plan created: Plans/{plan_id}.md")
```

### Track Plan Progress

```python
from silver.src.planning.plan_tracker import PlanTracker

tracker = PlanTracker(vault_path="/path/to/vault")

# Get current progress
progress = tracker.track_progress(plan_id)
print(f"Progress: {progress['completed']}/{progress['total']} steps")

# Update task status
tracker.update_task_status(
    plan_id=plan_id,
    task_id="step_1",
    status="completed"
)

# Get next tasks to work on
next_tasks = tracker.get_next_tasks(plan_id)
for task in next_tasks:
    print(f"Next: {task['title']}")
```

## Output Format

### Plan File Structure

Created in `Plans/` folder:

```markdown
---
id: plan_20260113_103045_abc123
title: "Implement User Authentication System"
status: in_progress
created_at: 2026-01-13T10:30:45Z
updated_at: 2026-01-13T14:22:10Z
complexity: high
estimated_effort: 3_days
actual_effort: null
---

# Plan: Implement User Authentication System

## Objective

Implement a secure user authentication system with OAuth2 support, JWT tokens, and role-based access control for the web application.

## Context

- **Tech Stack**: Python 3.13, FastAPI, PostgreSQL, Redis
- **Requirements**: OAuth2, JWT tokens, RBAC, password hashing
- **Constraints**: Production-ready, security-first approach
- **Timeline**: 3 days estimated

## Steps

### 1. Database Schema Design

- **Description**: Design user, role, and permission tables with proper relationships
- **Dependencies**: None (can start immediately)
- **Estimated Effort**: 2 hours
- **Status**: ✅ Completed
- **Success Criteria**:
  - [ ] User table with email, password_hash, created_at
  - [ ] Role table with name, permissions
  - [ ] user_roles junction table
  - [ ] Database migration scripts created

### 2. Password Hashing Implementation

- **Description**: Implement secure password hashing using bcrypt
- **Dependencies**: Step 1 (database schema)
- **Estimated Effort**: 1 hour
- **Status**: ✅ Completed
- **Success Criteria**:
  - [ ] Bcrypt integration with salt rounds = 12
  - [ ] Password validation function
  - [ ] Unit tests for hashing/validation

### 3. JWT Token Generation

- **Description**: Implement JWT token generation and validation
- **Dependencies**: Step 2 (password hashing)
- **Estimated Effort**: 2 hours
- **Status**: 🔄 In Progress
- **Success Criteria**:
  - [ ] JWT token generation with user claims
  - [ ] Token expiration (15 minutes for access, 7 days for refresh)
  - [ ] Token validation middleware
  - [ ] Unit tests for token operations

### 4. OAuth2 Integration

- **Description**: Integrate OAuth2 providers (Google, GitHub)
- **Dependencies**: Step 3 (JWT tokens)
- **Estimated Effort**: 4 hours
- **Status**: ⏳ Pending
- **Success Criteria**:
  - [ ] Google OAuth2 integration
  - [ ] GitHub OAuth2 integration
  - [ ] User account linking
  - [ ] Integration tests

### 5. Role-Based Access Control

- **Description**: Implement RBAC with decorators and middleware
- **Dependencies**: Step 3 (JWT tokens)
- **Estimated Effort**: 3 hours
- **Status**: ⏳ Pending
- **Success Criteria**:
  - [ ] Role decorator (@require_role)
  - [ ] Permission checking middleware
  - [ ] Admin, user, guest roles defined
  - [ ] Unit tests for RBAC

### 6. API Endpoints

- **Description**: Create authentication API endpoints
- **Dependencies**: Steps 3, 4, 5
- **Estimated Effort**: 3 hours
- **Status**: ⏳ Pending
- **Success Criteria**:
  - [ ] POST /auth/register
  - [ ] POST /auth/login
  - [ ] POST /auth/refresh
  - [ ] POST /auth/logout
  - [ ] GET /auth/me
  - [ ] Integration tests for all endpoints

### 7. Security Hardening

- **Description**: Implement security best practices
- **Dependencies**: Step 6 (API endpoints)
- **Estimated Effort**: 2 hours
- **Status**: ⏳ Pending
- **Success Criteria**:
  - [ ] Rate limiting on auth endpoints
  - [ ] CORS configuration
  - [ ] HTTPS enforcement
  - [ ] Security headers (CSP, HSTS)
  - [ ] Input validation and sanitization

## Dependencies

```
Step 1 (Database) → Step 2 (Password Hashing) → Step 3 (JWT Tokens) → Step 4 (OAuth2)
                                                                      → Step 5 (RBAC)
                                                                      → Step 6 (API Endpoints) → Step 7 (Security)
```

## Risks

### 1. OAuth2 Provider Rate Limits

- **Description**: Google/GitHub may rate limit OAuth2 requests during testing
- **Mitigation**: Use mock OAuth2 server for development, implement caching
- **Probability**: Medium
- **Impact**: Low (development only)

### 2. JWT Token Security

- **Description**: Improper JWT implementation could lead to security vulnerabilities
- **Mitigation**: Use well-tested library (PyJWT), follow OWASP guidelines, security audit
- **Probability**: Low
- **Impact**: Critical

### 3. Database Migration Issues

- **Description**: Schema changes may cause data loss or migration failures
- **Mitigation**: Test migrations on staging, backup production data, rollback plan
- **Probability**: Low
- **Impact**: High

## Success Criteria

- [ ] All 7 steps completed and tested
- [ ] 90%+ test coverage for authentication code
- [ ] Security audit passed (no critical vulnerabilities)
- [ ] OAuth2 integration working for Google and GitHub
- [ ] RBAC working correctly for all roles
- [ ] API endpoints documented in OpenAPI spec
- [ ] Production deployment successful

## Progress

- **Status**: In Progress (Step 3 of 7)
- **Completed Steps**: 2/7 (29%)
- **Estimated Remaining**: 13 hours
- **Last Updated**: 2026-01-13 14:22:10
- **Next Actions**: Complete JWT token generation (Step 3)
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

### System Requirements

- Python 3.13+
- Access to Obsidian vault

## Setup Instructions

### 1. Create Plans Folder

```bash
# Create Plans folder in vault root
mkdir -p Plans

# Verify folder exists
ls -la | grep Plans
```

### 2. Configure Plan Template

```bash
# Copy plan template
cp silver/config/plan_template.md Plans/.template.md

# Customize template if needed
nano Plans/.template.md
```

### 3. Test Plan Generation

```bash
# Test plan generation
python silver/scripts/test_planning.py --task "Implement feature X"

# Check Plans/ folder for generated plan
ls -la Plans/
```

## Error Handling

### Invalid Task Description

- **Error**: Task description too vague or empty
- **Action**: Prompt user for more details, suggest clarifying questions

### Template Not Found

- **Error**: Plan template file missing
- **Action**: Use default template, log warning

### File System Errors

- **Error**: Cannot write to Plans/ folder
- **Action**: Check permissions, create folder if missing, notify user

## Performance

- **Plan Generation**: ~2-5 seconds for typical tasks
- **Memory**: ~30MB per plan generation
- **CPU**: Minimal (<5% on modern systems)
- **Disk**: ~5-20KB per plan file

## Testing

### Unit Tests

```bash
pytest silver/tests/unit/test_plan_generator.py
pytest silver/tests/unit/test_task_analyzer.py
pytest silver/tests/unit/test_plan_tracker.py
```

### Integration Tests

```bash
pytest silver/tests/integration/test_planning.py
```

### Manual Testing

1. Generate plan for complex task:
   ```bash
   python silver/scripts/test_planning.py --task "Build REST API"
   ```

2. Verify plan file created in Plans/ folder

3. Check plan structure (YAML frontmatter, sections, steps)

4. Update task status manually in plan file

5. Track progress:
   ```bash
   python silver/scripts/test_planning.py --track plan_id
   ```

## Success Criteria

- ✅ Plans generated for complex tasks (3+ steps)
- ✅ Plan structure follows template format
- ✅ Dependencies correctly identified
- ✅ Risks assessed with mitigation strategies
- ✅ Success criteria defined and measurable
- ✅ Progress tracking works correctly

## Related Skills

- **monitor-communications**: May trigger plan creation for complex requests
- **manage-approvals**: Plans may include actions requiring approval
- **execute-actions**: Plans guide action execution

## References

- See `references/planning_guidelines.md` for detailed planning methodology
- See `references/complexity_assessment.md` for complexity scoring

## Examples

- See `examples/sample_plan.md` for complete plan example
- See `examples/simple_task.md` for task that doesn't need a plan
- See `examples/complex_task.md` for task requiring detailed planning

## Changelog

- **1.0.0** (2026-01-13): Initial implementation for Silver tier
