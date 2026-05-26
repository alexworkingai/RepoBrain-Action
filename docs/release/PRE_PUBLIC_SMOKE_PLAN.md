# Pre-Public Smoke Plan

## Issue Command Sequence

1. `/repobrain doctor`
2. `/repobrain status`
3. `/repobrain audit Focus on public-ready partner testing.`
4. `/repobrain score Focus on public-ready partner testing.`
5. `/repobrain ask Where is the RepoBrain workflow and what runtime mode is configured?`

## Optional PR Command Sequence

- `/repobrain review`
- `/repobrain verify`
- `/repobrain fix`
- optional `/repobrain audit`
- optional `/repobrain score`

## Expected Outcomes

- audit and score use `v6`-enriched mode when runtime is available
- verify remains informational
- fix remains no-patch and no-mutation
- no secret or source exposure
- no `v5`
- no `repobrain-community`
- read-mostly permissions remain intact

## Safety Expectations

- no patch/autofix
- no RepoBrain-created branch, commit, or PR
- no private checkout evidence in outputs
