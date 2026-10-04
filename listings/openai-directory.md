# OpenAI plugin directory submission (ChatGPT + Codex; dots use the same plugins)

Portal: https://platform.openai.com/plugins. Submitter needs the organisation owner role or "Apps Management Write", and the organisation must have completed individual or business verification.

## Before submitting (Hark side)

| Prerequisite | Status on 2026-10-03 | What to do |
| --- | --- | --- |
| `https://harkstudio.io/.well-known/openai-apps-challenge` serves the exact token as plain text | Route exists; returns `404 Not configured` | Copy the token from the portal's Verify Domain step and set it in production (the route reads an environment variable), then press Verify |
| OAuth sign-in works from OpenAI's origins (ChatGPT, Codex, dots) | Hark's connect pages document ChatGPT and Codex OAuth today | Confirm the OAuth origin allowlist covers every surface the directory serves, including dots |
| `https://harkstudio.io/support` resolves (interface.supportURL) | 404 | Publish a support page, or point supportURL at the page that exists |
| Rate limits tolerate always-on reads from dots | Unverified | Confirm the per-workspace caps and the "plan cap" error text the bot-notes skill tells agents to stop on |
| Read-only personal access tokens exist | Documented at harkstudio.io/connections | None |

## What goes in the ZIP

The repo root as is: `plugin.json`, `mcp.json`, `skills/`, `assets/`. The directory reads the root `plugin.json` (Agent Plugins 1.0.0) with `extensions.com.openai.interface`; `.codex-plugin/plugin.json` is the compatibility copy and is ignored when the root extension is present.

```bash
git archive --format=zip -o hark-plugin.zip HEAD plugin.json mcp.json skills assets LICENSE README.md
```

## Review information to prepare

**Five positive test cases** (description, prompt, tools triggered, expected behaviour):

1. Read a brief. "Read the Hark brief for V-012 and tell me what's next." → `get_agent_brief` → a short summary of current state and the next action.
2. Log a decision. "Log in Hark that we picked Postgres over SQLite because of concurrent writers." → `add_journal_entry` (kind decision) → confirms the entry is recorded as a candidate for a person to accept.
3. Write a handoff. "Write the Hark handoff for this session." → `end_session` → four-part handoff, reported back in two lines.
4. Capture a spark. "Note in Hark: idea, export the roadmap as a one-pager." → `capture_spark` → confirms the spark on the project.
5. Digest projects. "What's moving across my Hark workspace this week?" → `list_ventures`, `get_venture_context` → a per-project digest.

**Three negative test cases** (description, prompt, expected refusal or fallback):

1. Not signed in. "Read my Hark brief." with no connection → the agent explains how to sign in; no tool call succeeds.
2. Wrong project. After binding to V-012, "Log a decision on V-040." → Hark rejects the cross-project call; the agent offers `switch_venture` and asks before switching.
3. Destructive request. "Delete the project V-012." → the agent asks for explicit confirmation; `delete_venture` is not called on the first turn.

**Also needed:** a demo recording URL, release notes, and a dedicated test account on Hark with sample projects (no MFA, no real user data), entered in the dashboard form.

## After approval

- Pick the publish date in the dashboard.
- Skills or metadata changes: bump `version` in every manifest, upload a new ZIP.
- MCP server changes are rescanned daily; request a rescan after a deploy.
- Until the listing is live, do not say the plugin is available in ChatGPT, Codex or dots.
