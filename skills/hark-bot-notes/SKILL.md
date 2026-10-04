---
name: hark-bot-notes
description: Rules for always-on and scheduled agents (dots, Grok Bot routines, background runs) that read or note things in Hark without a person in the loop. Use when the Hark MCP tools are available and the run is unattended, recurring, or a routine. Each run is one short Hark session; read first, write little, and never leave the session open.
---

# Hark notes from an always-on agent

An always-on agent runs without a person watching. In Hark that means: it must not pile up open sessions, draft handoffs or unreviewed candidates, and it must not change the plan. Its job is to notice and to note.

## One run, one session

1. Start with `get_agent_brief`, `task` set to the routine's name (for example `Nightly repo watch`). This binds the run to the project. One brief per run; do not poll it.
2. Do the routine's reads and, if any, its notes.
3. End the run:
   - If you wrote anything: `end_session`. `what_i_did` names the routine, `what_changed` lists the notes written, `whats_next` is empty unless the routine found something a person must do, in which case that is the one line.
   - If you wrote nothing: `close_session` with `reason` set to the routine's name and `nothing to note`.

Never stop without one of the two. An open session makes Hark draft a handoff after 45 minutes that a person then has to review, once per run.

## Read first

These are always safe and are what a routine is usually for:

| Need | Call |
| --- | --- |
| Where the project stands | `get_agent_brief` (already done at start) |
| What happened since the last run | `list_journal_entries` with `limit`, filter by `occurred_at` newer than the last run |
| Repo activity (commits, PRs, releases) | `get_repo_activity` |
| Numbers over time | `get_metrics` |
| Proposals waiting for a person | `list_candidates` |
| A digest across several projects | `get_venture_context` with up to five codes, or `list_ventures` and `search_ventures`. These work before the session is bound, so call them before `get_agent_brief` when the routine covers several projects, and bind only the project you will write to |

Note the newest `occurred_at` you saw so the next run starts from there, in whatever memory the bot keeps.

## Write little

Allowed, because they are notes a person can act on and none changes the plan:

- `capture_spark`: an idea or an observation worth keeping, one line, with where it came from.
- `capture_feedback`: something a user, customer or reviewer said, quoted.
- `log_metric`: a number the routine measured, with its unit and when.
- `add_journal_entry` with `kind: "ship"`: only for work that is observably shipped (a merged PR, a published release) and only with the URL as evidence in the body. Do not log a ship because a commit message says done.
- `add_journal_entry` with `kind: "attempt"`: when the routine itself tried something that failed and the next run should not retry it.

Not allowed unless the routine's owner asked for that exact action in the routine's instructions:

- `add_journal_entry` with `kind: "decision"`. A bot does not make decisions, and it must not infer one from code or commit messages. If a decision seems to have been made, write a spark that says so and let a person record it.
- `update_build_state` beyond `open_questions`. Phase, summary, blockers and next up are the team's plan.
- `accept_candidate`, `reject_candidate`, `confirm_handoff`, `supersede_decision`, `unsupersede_decision`.
- `move_stage`, `move_feature_status`, `toggle_checklist_item`.
- `create_venture`, `fork_venture`, `archive_venture`, `delete_venture`, `promote_spark`, `update_claude_md`, `update_venture_business`, `update_venture_branding`, `connect_venture_repo`.

Write each note once. Before writing, check the recent journal for the same note from an earlier run.

## Keys, limits and failures

- Prefer a **read-only Hark token** for the connection. If a write tool answers with an authorization error, the token is read-only: report the note in the run's summary instead, and do not retry.
- A **plan cap** error means the workspace has used its agent calls for the month. Stop the run, end the session with `close_session`, and tell the owner.
- Hark is **unreachable**: skip the run. Do not queue writes for later.
- Keep the token out of anything you write to Hark or post anywhere else.

## What to tell the owner

When the routine reports to a person, lead with what changed since the last run and what needs them:

1. Journal entries, repo activity and metrics newer than the last run, one line each.
2. Proposals waiting for a person (the count from `list_candidates`) and any draft handoff in the brief.
3. Blockers from the brief that are still listed.
4. The notes this run wrote.

Say nothing when nothing changed, unless the routine's owner asked for a heartbeat.
