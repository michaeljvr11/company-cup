# Parallel Prompt: Future Simulator Audit Against Rules

Use the shared context from `00_shared_context_prompt.md`.

The current simulator is implemented in `f1/simulate.py` and covered by
`tests/test_simulate.py` plus all-level regression coverage in `tests/test_levels.py`.
The current code behaviour is summarized in `00_shared_context_prompt.md` and
`docs/PHYSICS.md`.

This document is a future extension plan for a broader edge-case audit suite, not
evidence that `simulator_audit_tests` or `simulator_audit_report.md` currently
exist.

## Goal

If more confidence is needed before aggressive optimisation, create a simulator
audit suite that tests edge cases and documents actual simulator behaviour.

## Areas to Audit

### 1. Weather Timing

Test:

```text
weather changes exactly at segment start
weather changes mid-straight
weather changes mid-corner
weather changes exactly at segment end
weather schedule cycles
```

Record whether weather is sampled:

```text
at segment start
continuously
at segment end
some other way
```

### 2. Corner Crash Boundary

Test corner entry speeds:

```text
exactly max safe speed
max safe speed + tiny epsilon
max safe speed - tiny epsilon
```

Determine whether crash condition is:

```text
speed > max
speed >= max
rounded comparison
```

### 3. Tyre Degradation Timing

Test whether tyre degradation affects friction:

```text
before segment
after segment
during segment
```

Especially check consecutive corners.

### 4. Fuel Depletion Timing

Test:

```text
fuel reaches exactly 0 at segment end
fuel reaches 0 mid-segment
fuel slightly negative by formula
```

Record when limp mode starts.

### 5. Limp Mode and Crawl Mode

Test:

```text
limp mode on straight
limp mode on corner
pit after limp mode
crawl after crash
crawl through consecutive corners
acceleration resumes on straight
```

### 6. Pit Stop Behaviour

Test:

```text
pit with no tyre and no fuel
pit with tyre only
pit with fuel only
pit with both
pit exit speed
pit timing
fuel tank overfill handling
```

### 7. Braking Point Edge Cases

Test:

```text
brake_start = 0
brake_start = straight length
brake_start > straight length
negative brake_start
target speed below entry speed
target speed above max speed
```

## Deliverables

Potential future deliverables:

```text
simulator_audit_tests
simulator_audit_report.md
```

The report should describe actual observed behaviour and any differences from the
PDF. Do not add a report file unless that artifact is explicitly useful for the
current task.

## Acceptance Criteria

The audit must:

- run deterministically
- use small synthetic tracks
- isolate one behaviour per test
- document expected vs observed results
- produce recommendations for optimiser implementation
