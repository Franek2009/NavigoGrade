# Changelog

All notable changes to NavigoGrade are documented in this file.

## [0.3.0-alpha.1]

First public alpha release.

- Added a Polish-language terminal interface with compact and guided input.
- Added final-grade eligibility calculations for grades 2 through 6.
- Added recommendations showing the level-points needed for a target grade.
- Added combined planning for acquiring competencies and upgrading existing
  competency levels.
- Added validation for competency counts, relationships, and target grades.
- Added automated coverage for grading boundaries, validation, CLI behavior,
  recommendation ranking, and combined-plan optimization.
- Corrected the domain model so level 0 means evaluated but not acquired, and
  current percentage and average calculations use evaluated competencies.
- Removed attempted-competency input and distinguished existing level-0,
  existing acquired, and future competency actions in recommendations.
