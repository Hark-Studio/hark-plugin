---
name: hark-handoff
description: Write the Hark handoff that ends a session, so the next session, agent or teammate picks up without re-deriving anything. Use when work on a Hark project is finishing, the user says hand off / wrap up / write the handoff, a brief shows an unconfirmed draft handoff, or a session stopped without end_session.
---

# The Hark handoff

A handoff is a journal entry of four parts: what I did, what changed, what's next, watch out for. The next session reads it at the top of its brief. It is private to the workshop and never appears on public project pages.

Write it with `end_session`. What you say changed or shipped is recorded as a **proposed claim** for a person to accept; what's next is appended to the project's next up.

## When to write one

- At the end of any session where something happened: files edited, a feature moved, a decision logged, state updated, a commit or PR made.
- When the user says hand off, wrap up, done for today, or write the handoff.
- Before switching to another project with `switch_venture`.
- Once per piece of work. If a handoff was already written for this work (by you, by another process, or by a client mod), do not write it again.

When nothing happened, call `close_session` with a `reason` instead, for example `Questions only, no changes`.

## The four fields

**`what_i_did`** — two to five sentences, past tense, concrete. What was asked, what was done, what was verified and how (tests run, checks passed, pages loaded). If something was left unfinished, say so here.

**`what_changed`** — one item per line, each a thing that now differs:

```
edited src/billing/invoice.ts: tax rounding now half-up
feature "Invoice export" moved to in progress
decision proposed: "Round tax half-up, never bankers"
commit 4f2a9c1 Round tax half-up
PR https://github.com/acme/app/pull/88
```

No prose. No file contents or diffs. Paths relative to the repo root.

**`whats_next`** — one item per line, most important first, each a thing the next session can start without asking. The first line is the next action. Include the open question if one blocks it:

```
Merge PR #88 after review
Decide: does rounding apply to credits too? (ask Dana)
Remove the old rounding helper once #88 is in
```

**`watch_out_for`** — the gotchas only: a failing test, a flaky step, an environment quirk, a decision the work came close to. Leave it out when there are none.

Also pass:
- `features_touched`: feature names moved or worked on.
- `links`: PR URLs first, then the touched files or docs, ten at most.
- `supersedes`: only journal entry ids the user confirmed this session replaces, for example a decision reversed during the session. Never guess ids; read them from `list_journal_entries`.

## Style

- Say what, not how you felt about it. No "successfully", no "simply".
- Name files, PRs and features; they are what the next session searches for.
- Keep secrets out: no tokens, keys, passwords or credentials, not even in a code excerpt. Never paste file contents; name the file.
- Under 1,500 characters for `what_i_did`. The handoff is a note, not a report.

## A session that stopped without a handoff

If a session ends without `end_session` (a crash, a closed tab, a routine that timed out), Hark's stop hook, or its 45-minute idle sweep, drafts a handoff from repo activity, or from the session's tool calls when no repo is linked. The draft is served at the top of the next brief until someone confirms it.

When your brief shows a draft:
1. Read it and compare it with what the user knows happened.
2. Tell the user in two lines what it claims.
3. With the user's agreement, `confirm_handoff`, correcting the text where the draft is wrong. Without it, leave the draft for a person.

## Decisions are not handoffs

A decision made during the session belongs in `add_journal_entry` with `kind: "decision"` and a rationale, at the moment it is made, not buried in `what_i_did`. The handoff can mention it as `decision proposed: "…"` in `what_changed`. Agent-written decisions are candidates until a person accepts them.
