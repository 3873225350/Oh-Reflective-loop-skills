# Workspace Shell Companion

`codex-loop` can be paired with an optional operator-facing workspace shell.

This repository keeps the loop runtime self-contained and treats any browser or app shell as a companion layer rather than a required part of the skill.

## What a workspace shell may provide

A reusable shell may choose to:

- list active plans or tasks
- open the selected plan file
- help draft short evolution notes
- surface daemon status and recent logs
- highlight the currently active loop context

## Minimum relay contract

If the shell talks to a local relay, the relay should expose only generic workspace capabilities such as:

- workspace metadata
- plan or task indexes
- guarded plan read and write operations
- daemon status
- recent loop logs

## Reuse strategy

When moving a companion shell into another project:

1. copy the UI surface
2. copy the relay endpoints the UI expects
3. replace branding, routing, and task-source assumptions
4. keep project-specific assets outside the core skill package

## Why this split exists

The loop runtime should stay small, scriptable, and easy to install.

Any companion shell is useful, but it is optional infrastructure and should remain loosely coupled so the exported skill stays generic.
