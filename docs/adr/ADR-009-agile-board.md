# ADR-009: Agile Board for Cross-Team Visibility

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-009

## Context

With four autonomous agent teams, cross-team awareness is essential. Teams need to know what's in flight, what's blocked, and what's done — without adding heavyweight process overhead.

## Decision

`docs/BOARD.md` serves as a single agile board with lanes: BACKLOG -> READY -> IN_PROGRESS -> REVIEW -> DONE. All four teams share one board.

Key rules:
- WIP limit of 1 per team (prevents multitasking)
- Ticket prefixes make ownership instant (LENS-NNN, CTX-NNN, ATL-NNN, SEN-NNN)
- Dependency graph in the board shows blocking relationships
- Velocity tracking enables the Lead to forecast delivery

## Consequences

**Positive:**
- Single source of truth for project state
- Cross-team blocking relationships are visible
- WIP limit prevents agents from starting new work before finishing current work
- Velocity data enables sprint planning

**Negative:**
- Board must be manually updated (agents update Dev2Lead, Lead updates Board)
- Large board (20 sprints planned) can be hard to scan
- No automated Kanban tooling — pure markdown

**Neutral:**
- The board is supplemented by `Lead2Dev.md` (instructions) and `Dev2Lead.md` (reports)
