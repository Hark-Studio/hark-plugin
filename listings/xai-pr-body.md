<!-- Fill the sha from `git ls-remote https://github.com/Hark-Studio/hark-plugin.git HEAD` (or the release tag's commit) before opening the PR. Paste the entry from xai-marketplace-entry.json into .grok-plugin/marketplace.json, then run the three scripts. -->

## What this PR does

Adds the Hark plugin: Hark's shared project memory for Grok Build, as a remote-sourced third-party plugin.

- Plugin name: hark
- Type: remote source
- Source URL + pinned SHA (remote): https://github.com/Hark-Studio/hark-plugin.git @ `<sha>`
- Homepage: https://github.com/Hark-Studio/hark-plugin

## Ownership

- [x] I own this plugin or have the right to distribute it.
- [x] The `source` repo is published under our official org (Hark-Studio, the organisation behind harkstudio.io).

## Checklist

- [ ] Added/updated exactly one entry in `.grok-plugin/marketplace.json` (valid JSON, kebab-case `name`).
- [ ] Remote source pins a full 40-char lowercase commit `sha`, and that commit is public + reachable.
- [ ] Regenerated `.grok-plugin/plugin-index.json` (`python3 scripts/generate-plugin-index.py`).
- [ ] `python3 scripts/validate-catalog.py` passes locally.
- [ ] `python3 scripts/generate-plugin-index.py --check` passes locally.
- [x] `homepage` + clear `description` set; the plugin repo includes `README.md` and `.grok-plugin/plugin.json`.
- [x] License is stated: MIT.

## Security

- [x] No `curl | bash`, remote-code download/exec, or `postinstall` RCE. The plugin ships no code, scripts or hooks: three `SKILL.md` files, an `.mcp.json` pointing at one HTTPS MCP server, manifests and two icons.
- [x] No reading/exfiltration of secrets, tokens, `.env`, or env vars. Nothing in the package runs on the user's machine.
- [x] Hooks and MCP scope are least-privilege: no hooks; one MCP server; the skills tell unattended agents to prefer a read-only Hark token and list the write tools they must not call.
- Network endpoints this plugin calls (and why): `https://harkstudio.io/mcp` only, the Hark MCP server (the user's own project memory). Authorization is discovered from `https://harkstudio.io/.well-known/oauth-protected-resource` (OAuth, browser sign-in to the user's Hark account), or a Hark personal access token the user adds as a header in their own client config. No telemetry; the package itself makes no requests.
- Credentials/permissions it requires (and why): a Hark account. OAuth in Grok Build; for headless or Grok Bot use, a Hark personal access token (read-only recommended) that the user creates at harkstudio.io/connections. The plugin never stores or embeds a credential.

## Notes for reviewers

Hark (harkstudio.io) is a project-memory workshop: agents read a project's brief and decisions at the start of a session and write a handoff at the end. The MCP server and its tool list are documented in the plugin README, including every tool the skills name. The same repo is submitted to OpenAI's plugin directory; `.grok-plugin/plugin.json` and `.claude-plugin/plugin.json` carry the same metadata as the root `plugin.json`.
