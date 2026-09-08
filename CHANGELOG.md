# Changelog

All notable changes to NavigoGrade are documented in this file.

## [0.5.0-beta.1]

Packaging and continuous-integration beta candidate.

- Added modern `pyproject.toml` packaging metadata for Python 3.10 and newer.
- Added `navigograde` and `navigograde-gui` installed console commands.
- Added a minimal GitHub Actions test matrix for supported Python versions.
- Documented local installation and installed CLI and GUI usage.
- Kept grading, planning, domain, and GUI behavior unchanged.

## [0.4.0-beta.1]

Polished beta candidate.

- Reorganized GUI results into clear sections for the current state, target,
  reaching and maintaining the target, and the next grade.
- Added concise visual success and failure indicators and improved GUI spacing
  and hierarchy.
- Clarified Quick Start instructions for both the terminal and graphical
  interfaces.
- Documented Tkinter installation and verification on common Linux
  distributions.
- Retained the terminal workflow and the shared, tested grading and planning
  core without changing its rules or behavior.

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
- Added full-course future simulation for reaching or maintaining a selected
  grade and planning toward the next higher grade.
