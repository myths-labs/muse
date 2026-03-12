# PR Templates and Conventions

Complete guide for generating Pull Request content based on type and context.

## 1. PR Types and Templates

### 1.1 Feature Branch → Develop (90% of cases)

**When to use**: New features, task implementations.

**Title**: `feat(<scope>): <description>`

**Template**:
```markdown
## What
- [List of implemented features/components]
- [Main functionality highlights]
- [Specific improvements references]

## Why
- [Business/operational impact]
- [Pain points resolved]
- [Expected benefits and improvements]

## Details
### Task X.Y: [Task Title]
- [Implementation detail 1]
- [Implementation detail 2]
- **Requirements**: X, Y, Z

## Checklist
- [ ] Main feature implemented
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code review ready
```

---

### 1.2 Develop → Master/Main (Release)

**When to use**: Stable releases, multiple feature aggregation.

**Title**: `release: version X.Y with [main features]`

**Template**:
```markdown
## What
This release includes:
- [Feature set 1 - Task N]
- [Feature set 2 - Task M]

## Why
[Release motivation, milestone reached, requirements completed]

## Details
### Task N: [Feature Name] (COMPLETE)
- **Task N.1**: [Description]
- **Task N.2**: [Description]
- **Requirements**: X, Y, Z

### Task M: [Feature Name] (COMPLETE)
[...]

## Testing
- Coverage: XX%
- Integration tests: pass/fail
- Performance tests: pass/fail

## Checklist
- [ ] All tasks completed
- [ ] No breaking changes (or documented)
- [ ] Migration guide prepared (if needed)
- [ ] Production deployment plan reviewed
```

---

### 1.3 Bugfix

**Title**: `fix(<scope>): <fix description>`

**Template**:
```markdown
## What
Fix for [problem description]

## Problem
[Bug description, how it manifests, impact]

## Solution
[Explanation of implemented solution]

## Testing
- [How the fix was tested]
- [Regression tests added]

## Checklist
- [ ] Bug resolved
- [ ] Regression tests added
- [ ] No side effects introduced
```

---

### 1.4 Hotfix (Master/Main)

**Title**: `hotfix(<scope>): <critical fix>`

**Template**:
```markdown
## HOTFIX

### Issue
[Description of critical production issue]

### Root Cause
[Identified cause]

### Fix
[Implemented solution]

### Impact
- Affected users: [estimate]
- Downtime: [if applicable]

### Rollback Plan
[Rollback plan if needed]

## Checklist
- [ ] Fix tested in staging
- [ ] Approval for urgent deploy
- [ ] Post-deploy monitoring planned
```

---

### 1.5 Refactoring

**Title**: `refactor(<scope>): <refactoring description>`

**Template**:
```markdown
## What
Refactoring of [component/module]

## Why
- [Motivation: performance, maintainability, technical debt]

## Changes
- [Change 1]
- [Change 2]

## Impact
- **Functional**: None (behavior unchanged)
- **Performance**: [expected improvements]
- **Maintainability**: [benefits]

## Checklist
- [ ] Functional behavior unchanged
- [ ] Existing tests passing
- [ ] New tests added (if needed)
```

---

### 1.6 Documentation

**Title**: `docs(<scope>): <description>`

**Template**:
```markdown
## What
Documentation update for [area]

## Changes
- [Document 1]: [change type]
- [Document 2]: [change type]

## Motivation
[Why this documentation is needed]
```

---

### 1.7 CI/CD and Infrastructure

**Title**: `ci(<scope>): <description>` or `chore(<scope>): <description>`

**Template**:
```markdown
## What
[Pipeline/infrastructure change]

## Changes
- [Change 1]
- [Change 2]

## Impact
- Build time: [variation]
- Deploy process: [variation]

## Testing
[How it was verified]
```

---

## 2. Title Conventions (Conventional Commits)

### 2.1 Format
```
<type>(<scope>): <description>
```

### 2.2 Types
| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code refactoring (neither fix nor feature) |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `test` | Adding/fixing tests |
| `perf` | Performance improvement |
| `chore` | Build, tools, dependencies |
| `ci` | CI/CD configuration |

### 2.3 Scope Rules
- Use **kebab-case**: `cookie-management`, `api-validation`, `auth-system`
- Derive from dominant commit scope or task name
- If multiple scopes, use the predominant one

### 2.4 Description Rules
- **Imperative present**: "add", not "added" or "adds"
- **Lowercase**: start with lowercase
- **No period**: no trailing dot
- **Max 50 characters** after the colon

### 2.5 Breaking Changes
Add exclamation mark after type/scope:
```
feat(api)!: remove deprecated endpoint
```

---

## 3. Section Guidelines

### 3.1 What Section
**Include**:
- Components/features implemented (concise list)
- Relevant technical details (caching, async, algorithms)
- Scope of changes

**Avoid**:
- Vague descriptions ("various changes")
- Excessive implementation details
- Repeating title content

### 3.2 Why Section
**Include**:
- Business/operational impact
- Problems solved (pain points)
- Measurable benefits when possible

**Avoid**:
- Technical justifications without business context
- "Because it was in the backlog"

### 3.3 Details Section
**Include**:
- Explicit mapping to Task IDs
- Completed sub-tasks
- Requirements satisfied (with IDs if available)
- Significant architectural decisions

**Recommended format**:
```markdown
### Task 3.1: Cookie File Validation
- Implement validation logic checking JSON structure
- Add detailed error messages for failure types
- **Requirements**: 8, 23
```

### 3.4 Checklist Section
**Always include**:
- [ ] Main feature implemented
- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)
- [ ] Breaking changes documented (if present)
- [ ] Performance verified (for critical features)

---

## 4. Label Mapping

### 4.1 Type → Labels
| Commit Type | Suggested Labels |
|-------------|------------------|
| `feat` | `feature`, `enhancement` |
| `fix` | `bug`, `bugfix` |
| `refactor` | `refactoring`, `tech-debt` |
| `docs` | `documentation` |
| `test` | `testing` |
| `perf` | `performance` |
| `ci` | `ci/cd`, `infrastructure` |
| `chore` | `maintenance`, `dependencies` |

### 4.2 Contextual Labels
- `breaking-change` - introduces breaking changes
- `security` - security-related
- `urgent` / `priority:high` - for hotfixes
- `needs-review` - complex PRs
- `WIP` - work in progress (not ready for merge)

---

## 5. Generation Rules

### 5.1 Input Analysis
1. **Read commits** and identify:
   - Predominant type (feat > fix > refactor)
   - Most frequent scope
   - Referenced Task IDs
2. **Verify task completion** if documentation exists
3. **Identify breaking changes** from commits with exclamation mark or `BREAKING CHANGE`

### 5.2 Output Construction
1. **Title**: Generate following Conventional Commits
2. **Body**: Use appropriate template for the type
3. **Labels**: Suggest based on commit types
4. **Checklist**: Populate based on what was done

### 5.3 Validations
- Title <= 72 characters total
- Description per section <= 500 words
- At least 3 items in checklist
- Task IDs present if documentation available

---

## 6. Complete Examples

### Example 1: Feature PR
**Input**: Branch `feature/auth-system` with 12 feat/fix commits for Task 2

**Output**:
```
Title: feat(auth): implement JWT authentication system

## What
- JWT token generation and validation with configurable expiration
- User login/logout REST endpoints with proper status codes
- Role-based access control middleware
- Secure password handling with bcrypt

## Why
- Enable secure user authentication for the application
- Provide granular access control for different user types
- Meet security requirements for production deployment

## Details
### Task 2.1: JWT Token Generation
- Industry-standard JWT implementation
- Configurable token expiration (default: 24h)
- **Requirements**: 5, 6, 7

### Task 2.2: Login/Logout Endpoints
- RESTful API with proper HTTP status codes
- Session management with Redis
- **Requirements**: 8, 9

### Task 2.3: Role-Based Access Control
- User roles: admin, user, guest
- Permission middleware for route protection
- **Requirements**: 10, 11

## Checklist
- [x] JWT system implemented
- [x] All endpoints tested
- [x] RBAC middleware working
- [x] 95% test coverage
- [x] Documentation updated

Labels: feature, security
```

### Example 2: Bugfix PR
**Input**: Branch `fix/validation-error` with 3 fix commits

**Output**:
```
Title: fix(validation): correct error handling in form submission

## What
Fix for error handling during user form validation

## Problem
Users received a generic 500 error instead of specific validation messages when submitting forms with invalid data.

## Solution
- Added specific try-catch in validation middleware
- Implemented error formatter for user-friendly messages
- Corrected status code from 500 to 422 for validation errors

## Testing
- Unit test for each validation error type
- Integration test for form submission flow
- Verified behavior with edge case inputs

## Checklist
- [x] Bug resolved
- [x] Regression tests added
- [x] Error messages verified with UX team

Labels: bug, bugfix
```

---

## 7. Anti-Patterns to Avoid

- **Vague titles**: "fix stuff", "updates", "changes"
- **Empty descriptions**: PR without body or with only title
- **Generic checklists**: "done", "tested" without specifics
- **Mixed concerns**: Feature + bugfix + refactor in same PR
- **Unreferenced tasks**: Changes without link to task/issue
- **Hidden breaking changes**: Not documenting API/behavior changes

---

## 8. Generation Workflow

```
1. IDENTIFY TYPE
   |-- Analyze branch name (feature/, fix/, hotfix/, etc.)
   |-- Analyze predominant commit types

2. GATHER INFORMATION
   |-- List commits with type and scope
   |-- Referenced Task IDs
   |-- Breaking changes present

3. GENERATE TITLE
   |-- Choose appropriate type
   |-- Determine scope
   |-- Write description (<=50 chars)

4. BUILD BODY
   |-- Select correct template
   |-- Populate What/Why/Details sections
   |-- Generate checklist

5. SUGGEST LABELS
   |-- Map from commit types + context

6. PRESENT TO USER
   |-- Request confirmation before creating
```
