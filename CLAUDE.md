# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This is a company hackathon project. The goal is to ship something working, not something perfect. The project type is not yet decided.

For this repo's F1 optimiser, prior-session external scores to beat / reconcile are:
L1 1,601,646; L2 2,108,044; L3 1,437,072; L4 1,135,340. These do not match the
current local `tools/eval.py` formula, so treat them as leaderboard targets and
evidence that `time_reference_s` or another hidden normalisation may matter until
the exact official formula is confirmed.

## Core Philosophy

**Minimum viable code.** Every function, file, abstraction, and dependency must justify its existence against the immediate problem. When in doubt, leave it out.

- No speculative abstractions — don't build for imagined future requirements
- No helper utilities that are only used once
- No wrapper layers that add no logic
- No config files for things that have sensible defaults
- Three similar lines is better than a premature abstraction
- Delete unused code immediately; don't comment it out

## Architecture Principles

Keep the architecture flat. Resist layering (controllers → services → repositories → models) unless the problem genuinely demands it. A direct path through the code is faster to read, write, and debug under time pressure.

Dependencies: only add a library if writing the equivalent from scratch would cost more time than the hackathon allows. Prefer standard library / built-ins first.

## Code Style

No comments unless the *why* is non-obvious from the code itself. No docstrings on self-evident functions. Function and variable names should make the code readable without annotation.

Error handling only at system boundaries (user input, external APIs, file I/O). Don't defensively guard internal code paths that cannot fail.

## What to Avoid

- Over-engineering the data model before the problem is fully understood
- Premature optimisation
- Abstracting before you have at least three concrete examples of the pattern
- Adding CI, Docker, or deployment config unless the project explicitly needs it to demo
