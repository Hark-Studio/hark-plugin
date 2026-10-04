---
name: hark-session
description: Hark's session flow for any work on a Hark project. Use when the Hark MCP tools are available and the work concerns a project (a V-### code, a brief, decisions, next steps, a handoff), or when a repo holds a .hark/project file. Read the brief with get_agent_brief before doing anything, work inside the accepted decisions, log as you go, and call end_session (or close_session) before you stop.
---

# Hark session flow

Hark is the shared memory for a project: its current state, accepted decisions, non-goals, blockers, next action, journal and handoffs. Every agent and teammate reads from it and writes to it, so one session's work carries over to the next. Hark, not a README or CLAUDE.md, is the source of truth for live build state.

A session has three parts: read the brief, work inside it, hand off.

## 1. Find the project

- In a repo, look for `.hark/project` at the repo root, then in each parent folder. It holds the project's code, for example `V-012`. A `.hark` file holding `venture=V-012` means the same thing.
- Without one, ask the user which project, or find it: `search_ventures` by name or `list_ventures`. If the user belongs to several workspaces, `list_workspaces` first, then pass `workspace_id` on workspace-scoped calls.
- To create the file: `mkdir -p .hark && echo V-012 > .hark/project`, and commit it so teammates share it.

## 2. Read the brief

Call `get_agent_brief` with the project (`venture`) and what you are about to do (`task`). Do this before any other work on the project, and again after a context reset.

- The brief is compact, about 1,500 tokens: identity, handoff status, current state (phase, summary, next up, blockers, non-goals, kill criterion), the last accepted decisions, a count of unreviewed proposals, and the primary repo's status. Pass `depth: "full"` only when you need the whole project (the AI context doc, every decision, features, checklist, sparks).
- The brief binds the session to that one project. Calls naming another project are rejected until you call `switch_venture`.
- If the brief carries an unconfirmed **draft handoff** from a session that stopped without `end_session`, read it, tell the user what it says, and confirm it with `confirm_handoff` only when the user agrees with it. The brief shows it at the top until someone does.
- Treat the brief's **next up** as the default task when the user has not said what to do.

## 3. Work inside the brief

- **Accepted decisions and non-goals are settled.** Before changing something an accepted decision or non-goal covers, say which decision it is and why you want to go against it, and wait for the user. Do not silently undo a decision.
- **Blockers** stay listed until the user clears them.
- The brief's **don't retry** list holds failed attempts. Do not repeat one without saying why this time is different.
- Records marked **proposed** or **candidate** were written by an agent and not yet reviewed by a person. They are suggestions, not decisions.

## 4. Log as you go, not at the end

Write to Hark when something happens, in the user's words where you can:

| What happened | Call |
| --- | --- |
| A decision was made, with the why | `add_journal_entry` with `kind: "decision"`, `title`, `rationale`, and `rejected_alternatives` when options were weighed |
| Something shipped (merged, released, deployed) | `add_journal_entry` with `kind: "ship"` and a link in the body |
| Something was tried and failed, so nobody retries it | `add_journal_entry` with `kind: "attempt"`, `outcome: "failed"`, and `do_instead` |
| A feature moved (planned, in progress, shipped) | `move_feature_status`, or `add_feature` for a new one |
| A readiness item is done | `toggle_checklist_item` (`list_checklist` for the labels) |
| The plan changed | `update_build_state` with only the fields that changed: `next_up`, `in_progress`, `just_shipped`, `open_questions` apply at once; `current_phase`, `summary`, `blockers` become proposals |
| An idea came up that is not this project's work | `capture_spark` |

Decisions and state proposals written by an agent are **candidates** until a person accepts them (`list_candidates`, `accept_candidate`, `reject_candidate`). Do not accept your own candidates unless the user asks you to.

Keep entries short: a title that reads as a sentence, one paragraph of body, the rationale in the user's reasoning.

## 5. End the session, every time

Before you stop, hand off. See the `hark-handoff` skill for what to write.

- Work happened (files, features, decisions, state): `end_session` with `what_i_did`, `what_changed`, `whats_next`, and `watch_out_for` when there is a gotcha.
- Nothing happened (questions and answers only): `close_session` with a one-line `reason`, so Hark does not draft an empty handoff.
- Stopping without either leaves the session open. Hark then drafts a handoff from repo activity after 45 minutes, and a person has to review it. Avoid that.
- After `end_session`, the next piece of work starts with a new `get_agent_brief`.

If the user says "hand off", "wrap up" or "write the handoff", do step 5 now.

## Client notes

- **ChatGPT and dots:** the Hark connector must be enabled for the chat. Writes ask for confirmation in ChatGPT; answer the user's question first, then make the write.
- **Codex:** `codex mcp login hark` signs in through the browser. In a repo, the project file does the binding.
- **Grok Build and Grok Bot:** xAI's remote MCP does not pause for approval before a write. Confirm destructive or wide changes (`move_stage`, `archive_venture`, `delete_venture`, `supersede_decision`) with the user in words before calling them. If the connection uses a read-only Hark token, write tools fail; report that and continue with reads.
- **Claude Code:** use the Hark mod (`Hark-Studio/hark-mod`) instead of this plugin. It does the brief, an edit guard and the handoff inside Claude Code.
