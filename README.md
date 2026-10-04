# Hark — shared project memory, as a plugin

The Hark plugin (`hark`) for ChatGPT, Codex, dots, Grok Build and Grok Bot. It connects an agent to your project on [Hark](https://harkstudio.io), so the plan, the decisions and the handoff carry over from one session (and one teammate, and one agent) to the next.

It is one package in the portable [Agent Plugins](https://agent-plugins.org) format, read by OpenAI's and xAI's catalogs alike:

- **The Hark MCP connector.** One remote server, `https://harkstudio.io/mcp`, with OAuth sign-in to your Hark account.
- **Three skills.** `hark-session` (read the brief first, work inside the accepted decisions, log as you go, end the session), `hark-handoff` (what a good handoff says) and `hark-bot-notes` (rules for always-on agents such as dots and Grok Bot routines: one short session per run, read first, write little).

The plugin ships no code, no scripts and no hooks. Nothing in it runs on your machine; the client talks to Hark, and the skills tell the agent how.

**Claude Code users:** install the [Hark mod](https://github.com/Hark-Studio/hark-mod) instead. It uses Claude Code's in-process hooks for a brief on start, an edit guard and a handoff on stop, which this plugin cannot do.

## Install

Listings are in progress; see [Listings](#listings). Until a listing is live, install from this repository.

**Codex (CLI and IDE extension)**

```bash
codex plugin marketplace add Hark-Studio/hark-plugin
```

Then install `hark` from the plugin browser (`/plugins` in the TUI), and sign in:

```bash
codex mcp login hark
```

Without the plugin, the connector alone is `codex mcp add hark --url https://harkstudio.io/mcp`.

**ChatGPT and dots.** Once the directory listing is live, add Hark from the plugin directory; dots use the same plugins as ChatGPT and Codex. Until then, ChatGPT users add a custom connector: Settings → Apps → Advanced settings → Developer mode → Create, name `Hark`, MCP server URL `https://harkstudio.io/mcp`, authentication OAuth. Enable it per chat.

**Grok Build.** Once the marketplace entry is merged, install `hark` from the Grok Build marketplace. Until then, register the server directly:

```bash
grok mcp add --transport http hark https://harkstudio.io/mcp
```

Headless, where no browser can open: `--header "Authorization: Bearer $HARK_TOKEN"` with a Hark personal access token.

**Grok Bot.** No config file: ask the bot to add the MCP server `hark` at `https://harkstudio.io/mcp` with the header `Authorization: Bearer <your Hark token>`. Start with a read-only token. The marketplace path for Grok Bot is not verified yet ([listings/grok-bot.md](listings/grok-bot.md)).

## Setup

1. **Project.** In the repo, write the project's code to `.hark/project` and commit it:

   ```bash
   mkdir -p .hark && echo V-012 > .hark/project
   ```

   The `hark-session` skill looks for it at the repo root and in each parent folder, and also accepts a `.hark` file holding `venture=V-012`. Outside a repo (ChatGPT, dots, Grok Bot), name the project in the prompt or let the agent find it with `search_ventures`.
2. **Sign in.** The first Hark tool call opens the browser; sign in with your Hark account and approve. Codex: `codex mcp login hark`. Headless clients use a personal access token from [harkstudio.io/connections](https://harkstudio.io/connections) instead; a read-only token is enough for routines.
3. **Try it.** "Read the Hark brief for V-012 and tell me what's next."

## What the skills do

**`hark-session`** is the session flow Hark's own server instructions describe: `get_agent_brief` before any work (it binds the session to one project; `switch_venture` to change), work inside accepted decisions, non-goals and blockers, log decisions, ships and failed attempts as they happen, and `end_session` before stopping, or `close_session` when nothing changed. It tells the agent that agent-written decisions and state changes are candidates until a person accepts them, and not to accept its own.

**`hark-handoff`** is the handoff itself: the four fields of `end_session` (what I did, what changed, what's next, watch out for), one item per line, files and PRs named, no secrets, under 1,500 characters. It covers the draft handoff Hark writes when a session stops without one, and `confirm_handoff` only with the user's agreement.

**`hark-bot-notes`** is for unattended runs: one brief per run, the reads a routine may use (`list_journal_entries`, `get_repo_activity`, `get_metrics`, `list_candidates`, `get_venture_context` across projects), the notes it may write (`capture_spark`, `capture_feedback`, `log_metric`, a `ship` entry only with a URL as evidence), and the tools it must not call without the owner's explicit instruction (decisions, state, stage, candidates, anything destructive). It ends every run with `end_session` or `close_session`, stops on a plan-cap error, and prefers a read-only token.

The skills are plain Markdown in [skills/](skills/). Read them before trusting them; they are the whole behaviour.

## Every outbound request

The package makes none. Your client makes these, on the agent's behalf:

| URL | When | What |
| --- | --- | --- |
| `https://harkstudio.io/mcp` | Each Hark tool call | MCP over Streamable HTTP: the tool's name and arguments, with your OAuth token or personal access token in the `Authorization` header |
| `https://harkstudio.io/.well-known/oauth-protected-resource` | First connection | OAuth discovery. It names Hark's authorization server, where the client registers itself and you sign in |

Nothing else. No telemetry, no other hosts. The package embeds no credential and no header; `mcp.json` holds the one URL. What the agent sends to Hark is what the skills tell it to write: brief requests, journal entries, state changes and the handoff. The `hark-handoff` skill tells it to name files rather than paste them and to keep secrets out.

## Layout

| Path | Read by | Holds |
| --- | --- | --- |
| `plugin.json` | OpenAI (ChatGPT, Codex, dots), any Agent Plugins client | Agent Plugins 1.0.0 manifest, with the directory's listing fields under `extensions.com.openai.interface` |
| `mcp.json` | Same | The one `streamable-http` server |
| `.mcp.json` | Codex compatibility, Grok Build, Claude-format readers | The same server in the client-native form (`type: http`) |
| `.grok-plugin/plugin.json` | xAI's marketplace | Same metadata; points at `./skills/` and `./.mcp.json` |
| `.claude-plugin/plugin.json` | xAI's marketplace fallback | Same |
| `.codex-plugin/plugin.json` | Older Codex builds | Same, with the `interface` block inline. Ignored by current Codex when the root `plugin.json` carries `extensions.com.openai` |
| `.agents/plugins/marketplace.json` | `codex plugin marketplace add Hark-Studio/hark-plugin` | A one-entry marketplace for this repo |
| `skills/*/SKILL.md` | Every client | The three skills |
| `assets/` | Catalogs | Icon and logo (1024 px PNG) |
| `listings/` | Us | The catalog entry, PR body and submission notes for each listing |

`scripts/check.py` keeps the copies honest: it fails if the manifests disagree, a field breaks a schema or a limit, a skill's frontmatter is wrong, an asset is missing, or anything looks like a credential. CI runs it on every push.

## Listings

One repo, three listings. Rule: never say Hark is available on a platform until its listing is merged or approved.

| Platform | Catalog | Status | How |
| --- | --- | --- | --- |
| ChatGPT, Codex, dots | OpenAI plugin directory | Not submitted | [listings/openai-directory.md](listings/openai-directory.md): prerequisites, the ZIP, the test cases review asks for |
| Grok Build | `xai-org/plugin-marketplace` | Not submitted | PR adding [listings/xai-marketplace-entry.json](listings/xai-marketplace-entry.json) with a pinned commit SHA, body from [listings/xai-pr-body.md](listings/xai-pr-body.md) |
| Grok Bot | Unverified | Path unknown | [listings/grok-bot.md](listings/grok-bot.md) |

**Hark-side prerequisites** (checked 2026-10-03):

- `https://harkstudio.io/.well-known/openai-apps-challenge` must serve the directory's verification token as plain text. The route exists and answers `404 Not configured`; set the token in production during submission.
- OAuth origins for OpenAI (ChatGPT, Codex, dots) and xAI (Grok Build, Grok) must be allowlisted. ChatGPT, Codex and Grok Build sign-in are documented on Hark's connect pages today; confirm dots.
- Rate limits that tolerate always-on background reads, and read-only tokens that suffice for bots. Tokens exist; the caps are unverified.
- `https://harkstudio.io/support` (the listing's support URL) returns 404 and needs a page.

## Development

```bash
python3 scripts/check.py
```

No dependencies. The same manifests are read by three catalogs, so change `version`, `description`, `author`, `keywords` or the interface block in `plugin.json` and copy it to the three compatibility manifests; the check fails until they match. To tag a release for the xAI entry, commit, then:

```bash
git ls-remote https://github.com/Hark-Studio/hark-plugin.git HEAD
```

and put that SHA in the marketplace entry.

## Changelog

### 0.1.0 (2026-10-03)

- First package: the Hark MCP connector, the `hark-session`, `hark-handoff` and `hark-bot-notes` skills, manifests for OpenAI's directory and xAI's marketplace, the Codex marketplace file, and the listing materials.

## License

MIT. See [LICENSE](LICENSE).
