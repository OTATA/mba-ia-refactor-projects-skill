### Deprecated API / Dependency Usage

When checking for deprecated APIs:

1. Inspect local code, compiler warnings, annotations, imports and dependency metadata.
2. If deprecation status is not explicit locally, consult the official documentation for the exact framework/library version used by the project.
3. Prefer primary sources:
   - official documentation
   - official migration guides
   - release notes / changelogs
4. Do not classify an API as deprecated based only on blog posts or memory.
5. Report:
   - deprecated API
   - current project version
   - replacement API
   - removal version, if documented
   - source used for verification