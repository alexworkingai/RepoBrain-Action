# RepoBrain v6 Scoring Model

## 1. Purpose

RepoBrain v6''s core product differentiator is full repository analysis and 100-point quality and readiness scoring.

## 2. Overall Score

RepoBrain v6 targets a 0-100 repository quality and readiness score.

## 3. Proposed Categories And Weights

- Architecture and modularity: 15
- Code quality and maintainability: 12
- Testing and validation: 12
- Security posture: 12
- CI/CD and automation: 10
- Dependency hygiene: 8
- Documentation and onboarding: 8
- Release and operations readiness: 8
- GitHub governance: 8
- AI-readiness / repository intelligence: 7

Total: 100

## 4. Evidence Model

Each score must be evidence-grounded.
Relevant evidence can include:

- files
- workflows
- tests
- docs
- dependency manifests
- security and config files
- release artifacts
- PR history later if available

## 5. Output Model

A full audit output should include:

- executive summary
- overall score
- category scores
- critical blockers
- evidence references
- top improvements
- 30/60/90-day roadmap
- confidence level
- limitations
- no-mutation safety statement

## 6. Command Roadmap

### `/repobrain audit`

- flagship full repository audit and score

### `/repobrain score`

- short score summary or compact audit view

### `/repobrain doctor`

- installation and runtime diagnostic

### `/repobrain status`

- runtime status snapshot

### `/repobrain fix-lite`

- unsupported
- use `/repobrain fix`

## 7. Implementation Status

- Sprint 77 documents the model and roadmap.
- `/repobrain audit` MVP is planned for Sprint 78.
- `/repobrain doctor` and `/repobrain status` are planned for Sprint 79 unless priorities change.
