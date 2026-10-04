#!/usr/bin/env python3
"""Check the hark plugin package. No dependencies; run `python3 scripts/check.py`.

What it checks, so each catalog resolves the same plugin:
  - plugin.json      conforms to Agent Plugins 1.0.0 (schema const, name rule, closed field set)
                     and carries the OpenAI directory's interface fields within their limits
  - mcp.json         conforms to the Agent Plugins MCP schema: one streamable-http server, HTTPS, no headers
  - .mcp.json        the client-native form (Codex compatibility, Grok Build, Claude): same server, same URL
  - .grok-plugin/plugin.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json
                     same name, version, description, author, license and keywords as plugin.json
  - .agents/plugins/marketplace.json  lists this plugin at ./ with an installation policy
  - skills/*/SKILL.md  Agent Skills frontmatter: name matches the directory, description within 1024 chars
  - every asset path a manifest names exists, and the icons are square PNGs of at least 48 px
  - no file embeds a credential-looking token
Exit status 1 and a list of problems if anything fails; "OK" otherwise.
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
ENDPOINT = "https://harkstudio.io/mcp"
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
PORTABLE_FIELDS = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
INTERFACE_LIMITS = {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80,
                    "websiteURL": 1024, "supportURL": 1024, "privacyPolicyURL": 1024, "termsOfServiceURL": 1024}
INTERFACE_REQUIRED = ["displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities",
                      "logo", "composerIcon", "websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"]
SHARED = ["name", "version", "description", "author", "homepage", "repository", "license", "keywords"]
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|sk_live_[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,})")

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def load(rel: str) -> dict | None:
    p = ROOT / rel
    if not p.is_file():
        fail(f"{rel}: missing")
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        fail(f"{rel}: invalid JSON ({e})")
        return None


def asset(rel: str, where: str) -> None:
    if not isinstance(rel, str) or not rel.startswith("./"):
        fail(f"{where}: asset path {rel!r} must start with ./")
        return
    p = ROOT / rel[2:]
    if not p.is_file():
        fail(f"{where}: asset {rel} does not exist")
        return
    if p.suffix == ".png":
        b = p.read_bytes()
        if b[:8] != b"\x89PNG\r\n\x1a\n":
            fail(f"{where}: {rel} is not a PNG")
            return
        w, h = struct.unpack(">II", b[16:24])
        if w != h or w < 48 or w > 4096:
            fail(f"{where}: {rel} is {w}x{h}; icons must be square, 48 to 4096 px")
        if len(b) > 5 * 1024 * 1024:
            fail(f"{where}: {rel} is over 5 MiB")


def check_root_manifest() -> dict | None:
    m = load("plugin.json")
    if m is None:
        return None
    if m.get("$schema") != PLUGIN_SCHEMA:
        fail(f"plugin.json: $schema must be {PLUGIN_SCHEMA}")
    name = m.get("name", "")
    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not NAME_RE.match(name):
        fail(f"plugin.json: name {name!r} breaks the Agent Plugins name rule")
    extra = set(m) - PORTABLE_FIELDS
    if extra:
        fail(f"plugin.json: fields not allowed by the portable manifest: {sorted(extra)}")
    for k in ("version", "description", "license", "homepage", "repository"):
        if not m.get(k):
            fail(f"plugin.json: {k} is empty")
    author = m.get("author", {})
    if set(author) - {"name", "email", "url"}:
        fail("plugin.json: author may only have name, email, url")
    iface = m.get("extensions", {}).get("com.openai", {}).get("interface")
    if not isinstance(iface, dict):
        fail("plugin.json: extensions.com.openai.interface is missing")
        return m
    for k in INTERFACE_REQUIRED:
        if k not in iface or iface[k] in ("", [], None):
            fail(f"plugin.json: interface.{k} is required for the OpenAI directory")
    for k, lim in INTERFACE_LIMITS.items():
        v = iface.get(k)
        if isinstance(v, str) and len(v) > lim:
            fail(f"plugin.json: interface.{k} is {len(v)} chars; limit {lim}")
        if k.endswith("URL") and isinstance(v, str) and not v.startswith("https://"):
            fail(f"plugin.json: interface.{k} must be HTTPS")
    caps = iface.get("capabilities", [])
    if len(caps) > 20 or any(len(c) > 120 for c in caps):
        fail("plugin.json: interface.capabilities: at most 20 items of 120 chars")
    for k in ("logo", "composerIcon"):
        if k in iface:
            asset(iface[k], f"plugin.json interface.{k}")
    for s in iface.get("screenshots", []):
        asset(s, "plugin.json interface.screenshots")
    return m


def check_mcp(root: dict | None) -> None:
    m = load("mcp.json")
    if m is not None:
        if m.get("$schema") != MCP_SCHEMA:
            fail(f"mcp.json: $schema must be {MCP_SCHEMA}")
        if set(m) - {"$schema", "mcpServers"}:
            fail("mcp.json: only $schema and mcpServers are allowed")
        servers = m.get("mcpServers", {})
        if len(servers) != 1:
            fail("mcp.json: the directory allows one MCP server per plugin")
        for name, s in servers.items():
            if s.get("type") != "streamable-http":
                fail(f"mcp.json: server {name} must be streamable-http")
            if s.get("url") != ENDPOINT:
                fail(f"mcp.json: server {name} must point at {ENDPOINT}")
            if "headers" in s:
                fail(f"mcp.json: server {name} must not set headers (no credentials in the package)")
            if set(s) - {"type", "url", "headers"}:
                fail(f"mcp.json: server {name} has fields outside the schema")
    legacy = load(".mcp.json")
    if legacy is not None:
        servers = legacy.get("mcpServers", {})
        if set(servers) != set((m or {}).get("mcpServers", {})):
            fail(".mcp.json: server names differ from mcp.json")
        for name, s in servers.items():
            if s.get("type") != "http" or s.get("url") != ENDPOINT:
                fail(f".mcp.json: server {name} must be type http at {ENDPOINT}")
            for k in ("headers", "env", "oauth"):
                if k in s:
                    fail(f".mcp.json: server {name} must not set {k}")


def check_duplicates(root: dict | None) -> None:
    if root is None:
        return
    for rel in (".grok-plugin/plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        m = load(rel)
        if m is None:
            continue
        for k in SHARED:
            if m.get(k) != root.get(k):
                fail(f"{rel}: {k} differs from plugin.json")
        if m.get("skills") not in (None, "./skills/", "./skills"):
            fail(f"{rel}: skills must point at ./skills/")
        if rel != ".codex-plugin/plugin.json" and m.get("mcpServers") not in (None, "./.mcp.json"):
            fail(f"{rel}: mcpServers must point at ./.mcp.json")
        if rel == ".codex-plugin/plugin.json":
            want = root["extensions"]["com.openai"]["interface"]
            if m.get("interface") != want:
                fail(f"{rel}: interface differs from plugin.json extensions.com.openai.interface")
            if m.get("mcpServers") != "./.mcp.json":
                fail(f"{rel}: mcpServers must point at ./.mcp.json")
        if "logo" in m:
            asset(m["logo"], rel)
        if "icon" in m:
            asset(m["icon"], rel)


def check_marketplace(root: dict | None) -> None:
    m = load(".agents/plugins/marketplace.json")
    if m is None or root is None:
        return
    if not m.get("name") or not m.get("interface", {}).get("displayName"):
        fail(".agents/plugins/marketplace.json: name and interface.displayName are required")
    plugins = m.get("plugins", [])
    if len(plugins) != 1 or plugins[0].get("name") != root.get("name"):
        fail(".agents/plugins/marketplace.json: must list exactly this plugin")
        return
    p = plugins[0]
    src = p.get("source", {})
    if src.get("source") != "local" or src.get("path") != "./":
        fail(".agents/plugins/marketplace.json: source must be {source: local, path: ./}")
    pol = p.get("policy", {})
    if pol.get("installation") not in ("AVAILABLE", "INSTALLED_BY_DEFAULT") or "authentication" not in pol:
        fail(".agents/plugins/marketplace.json: policy.installation and policy.authentication are required")
    if not p.get("category"):
        fail(".agents/plugins/marketplace.json: category is required")


def check_skills() -> None:
    d = ROOT / "skills"
    if not d.is_dir():
        fail("skills/: missing")
        return
    found = 0
    for child in sorted(d.iterdir()):
        if not child.is_dir():
            continue
        f = child / "SKILL.md"
        if not f.is_file():
            fail(f"skills/{child.name}: no SKILL.md")
            continue
        found += 1
        text = f.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            fail(f"{f.relative_to(ROOT)}: no YAML frontmatter")
            continue
        fm: dict[str, str] = {}
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        name = fm.get("name", "")
        if name != child.name or not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name) or len(name) > 64:
            fail(f"{f.relative_to(ROOT)}: name must equal the directory name ({child.name}), lowercase with hyphens")
        desc = fm.get("description", "")
        if not desc or len(desc) > 1024:
            fail(f"{f.relative_to(ROOT)}: description is required and at most 1024 chars")
        unknown = set(fm) - {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
        if unknown:
            fail(f"{f.relative_to(ROOT)}: unknown frontmatter fields {sorted(unknown)}")
        body = text[m.end():].strip()
        if len(body) < 200:
            fail(f"{f.relative_to(ROOT)}: body is too short to be a skill")
    if found < 3:
        fail(f"skills/: expected the three skills, found {found}")


def check_secrets() -> None:
    for p in ROOT.rglob("*"):
        if p.is_dir() or ".git" in p.parts or p.suffix in (".png", ".jpg", ".webp"):
            continue
        try:
            t = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET_RE.search(t):
            fail(f"{p.relative_to(ROOT)}: contains something that looks like a credential")


def main() -> int:
    root = check_root_manifest()
    check_mcp(root)
    check_duplicates(root)
    check_marketplace(root)
    check_skills()
    check_secrets()
    if problems:
        print("Check failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("OK: plugin.json, mcp.json, the three compatibility manifests, the Codex marketplace and the skills agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
