## Anti-pattern Catalog

### CRITICAL
- Security Vulnerability
  - SQL Injection
  - Exposed credentials
  - Sensitive data exposure

- God Class / God Object

### HIGH
- Controller with direct database access
- Poor or missing layer separation

### MEDIUM
- N+1 Query
- High Cyclomatic Complexity / Callback Hell
- Long Function

### LOW
- Readability Smells
  - Magic numbers
  - Poor naming
  - Excessive sequential conditionals