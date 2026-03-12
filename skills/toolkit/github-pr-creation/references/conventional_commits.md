# Conventional Commits Reference

This guide describes the Conventional Commits standard used in the project.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type (required)

The main types are:

- **feat**: A new feature
- **fix**: A bug fix
- **refactor**: Code refactoring (neither fix nor feature)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, whitespace, etc.)
- **test**: Adding or fixing tests
- **perf**: Performance improvement
- **chore**: Build process or auxiliary tool changes
- **ci**: CI/CD files and scripts changes

### Scope (optional)

The scope provides additional context. Use kebab-case:

- `cookie-management`
- `api-validation`
- `auth-system`
- `data-processing`

### Description

- Use imperative present tense: "add" not "added" or "adds"
- Don't capitalize the first letter
- No period (.) at the end
- Max 50 characters after the colon

### Examples

```
feat(cookie-management): add TTL caching for validation
fix(api): correct endpoint path for user authentication
refactor(data): optimize query performance with indexing
docs(readme): update installation instructions
test(auth): add unit tests for token validation
```

## Breaking Changes

If a change introduces breaking changes, add an exclamation mark after type/scope or BREAKING CHANGE in the footer:

```
feat(api)!: remove deprecated endpoint

BREAKING CHANGE: /api/v1/old-endpoint has been removed. Use /api/v2/new-endpoint instead.
```

## Task References

Always include task references in the commit message:

```
feat(auth): implement task 2.1 - user login with JWT
fix(api): resolve task 3.2 - validation error handling
```

## Commit Body Best Practices

When needed, add details in the body:

- Explain the "why" not the "what" (the diff shows the "what")
- Reference issue or task IDs
- Mention breaking changes
- Describe side effects or consequences

Complete example:

```
feat(api): implement rate limiting middleware

Add rate limiting to prevent API abuse and ensure fair usage.
Implementation uses redis for distributed rate limit tracking.

Task: 4.2
Requirements: 45, 46A
Related: Task 4.1

Rate limits:
- Authenticated users: 1000 req/hour
- Anonymous users: 100 req/hour
```
