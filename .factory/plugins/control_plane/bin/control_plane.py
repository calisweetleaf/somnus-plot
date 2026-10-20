#!/usr/bin/env python3
"""Expose the actual Surgeon and Colony through a reloadable local MCP plane.

Source: supplied Surgeon engine, Colony helper, and codex_docs MCP reference.
Integrated: 2026-10-09
Purpose: compose existing tools with caste profiles and observable config changes.
IO: workspace source through Surgeon; Colony scent/claims through its helper;
    metadata of config.toml, agent contracts and workspace.json; local event log.
    No credentials, network, or autonomous global configuration edits.
Modified: 2026-10-10 by codex.
Justification: global calls need explicit project routing while reusing the
    existing engine, profile registry, and per-project state isolation.
Provenance: snapshots/stage-2-global/manifest.json -> domains.control_plane.edits[0].
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from types import ModuleType


BUNDLE_ROOT = Path(__file__).resolve().parents[3]
READ_OPS = frozenset({"outline", "view", "search", "stat", "log", "diff",
                      "capabilities", "workspace", "periphery", "references",
                      "check", "transaction"})
COLONY_COMMANDS = frozenset({"mark", "sniff", "cold", "scent", "claim", "release", "claims"})


class ControlPlaneError(RuntimeError):
    """A local registration, profile, or transport operation could not complete."""


def load_engine() -> ModuleType:
    """Load the single authoritative engine without duplicating its logic."""
    name = "codex_workspace_surgeon"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, BUNDLE_ROOT / "plugins/surgeon/bin/surgeon.py")
    if spec is None or spec.loader is None:
        raise ControlPlaneError("Surgeon engine cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class WorkspaceHost:
    """Composition host; the constituents retain their own semantics and state."""

    def __init__(self, root: str, config_dir: str, profile: str = "all",
                 read_only: bool = False) -> None:
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ControlPlaneError(f"workspace root is not a directory: {self.root}")
        self.config_dir = Path(config_dir).resolve()
        self.profile = profile
        self.read_only = read_only
        # Surgeon is optional: the engine loads lazily on first surgeon call, so a
        # colony-only install (no plugins/surgeon) still serves Colony and workspace.
        self.engine: ModuleType | None = None
        self.surgeon = None
        self._lock = threading.RLock()
        self._events: list[dict[str, object]] = []
        self._sequence = 0
        self._baseline: dict[str, tuple[int, int]] = {}
        self._registry: dict[str, object] = {}
        self._registry_text = ""
        self._registry_error: str | None = None
        self.refresh()
        self._baseline = self._metadata()

    def refresh(self) -> dict[str, object]:
        """Reload validated profiles; a malformed update keeps the last valid state."""
        with self._lock:
            try:
                source = (BUNDLE_ROOT / "workspace.json").read_text(encoding="utf-8")
                registry = json.loads(source)
                if not isinstance(registry, dict) or registry.get("schema_version") != 1:
                    raise ControlPlaneError("workspace.json needs schema_version 1")
                profiles = registry.get("profiles")
                if not isinstance(profiles, dict) or self.profile not in profiles:
                    raise ControlPlaneError(f"unknown profile {self.profile!r}")
                for name, value in profiles.items():
                    if not isinstance(name, str) or not isinstance(value, dict):
                        raise ControlPlaneError("profile entries must be named objects")
                    if not isinstance(value.get("source_edits"), bool):
                        raise ControlPlaneError(f"profile {name} needs source_edits")
                    tool_names = value.get("tools")
                    if not isinstance(tool_names, list) or any(not isinstance(t, str) or t not in ("surgeon", "colony", "workspace") for t in tool_names):
                        raise ControlPlaneError(f"invalid tool list for profile {name}")
                changed = source != self._registry_text
                self._registry, self._registry_text, self._registry_error = registry, source, None
                return {"ok": True, "changed": changed, "profile": self.profile}
            except (OSError, ValueError, ControlPlaneError) as exc:
                self._registry_error = str(exc)
                if not self._registry:
                    raise ControlPlaneError(str(exc)) from exc
                return {"ok": False, "changed": False, "error": str(exc), "retained_previous": True}

    def _policy(self) -> dict[str, object]:
        profiles = self._registry["profiles"]
        assert isinstance(profiles, dict)
        policy = profiles[self.profile]
        assert isinstance(policy, dict)
        return policy

    def _surgeon(self):
        """Load the Surgeon engine on first use; raises if the plugin is absent."""
        if self.engine is None:
            self.engine = load_engine()
        if self.surgeon is None:
            self.surgeon = self.engine.Surgeon(str(self.root), str(self.root / ".surgeon/journal"), sandbox=True)
        return self.surgeon

    def tool_specs(self) -> list[dict[str, object]]:
        """Return live schemas only for tools assigned to this caste profile."""
        with self._lock:
            allowed = self._policy()["tools"]
            descriptions = {}
            if "surgeon" in allowed:
                try:
                    engine = self.engine or load_engine()
                    self.engine = engine
                    descriptions["surgeon"] = {"name": "surgeon", "description": engine.TOOL_DESCRIPTION,
                                               "inputSchema": engine.TOOL_SCHEMA}
                except ControlPlaneError:
                    pass  # surgeon plugin not installed: colony-only plane
            descriptions.update({
                "colony": {"name": "colony", "description": "Use the real Colony helper for scent, cold marks and atomic claims. TASTED needs via; LEAP needs breaks_if. Castes retain the Six Laws.",
                           "inputSchema": {"type": "object", "properties": {
                               "command": {"type": "string", "enum": sorted(COLONY_COMMANDS)},
                               "place": {"type": "string"}, "kind": {"type": "string"},
                               "taste": {"type": "string"}, "what": {"type": "string"},
                               "via": {"type": "string"}, "breaks_if": {"type": "string"},
                               "crosses": {"type": "string"}, "worker": {"type": "string"}},
                               "required": ["command"], "additionalProperties": False}},
                "workspace": {"name": "workspace", "description": "Inspect profile/transport status, refresh specialization, scan global .codex metadata, or page change events. Config and agent edits are observed, not automatically executed.",
                              "inputSchema": {"type": "object", "properties": {
                                  "op": {"type": "string", "enum": ["status", "refresh", "scan", "events"]},
                                  "cursor": {"type": "integer", "minimum": 0},
                                  "limit": {"type": "integer", "minimum": 1, "maximum": 200}},
                                  "required": ["op"], "additionalProperties": False}}
            })
            return [descriptions[name] for name in descriptions if name in allowed]

    def dynamic_specs(self) -> list[dict[str, object]]:
        """Adapt the same tools to app-server dynamicTools without an MCP process."""
        return [{"type": "namespace", "name": "codex_workspace",
                 "description": "Surgeon editing, Colony collaboration, and workspace state.",
                 "tools": [{"type": "function", **tool} for tool in self.tool_specs()]}]

    def call(self, tool: str, arguments: object) -> dict[str, object]:
        """Route a request to the actual constituent and return a structured result.

        Args:
            tool: A tool name present in the selected profile.
            arguments: External JSON tool arguments; the shape is validated here.
        Returns:
            Engine, helper, or control-plane result with an explicit ok field.
        """
        with self._lock:
            if tool not in self._policy()["tools"]:
                return {"ok": False, "error": {"code": "profile_tool", "message": f"{tool} is absent from {self.profile}"}}
            if not isinstance(arguments, dict):
                return {"ok": False, "error": {"code": "bad_request", "message": "arguments must be an object"}}
            try:
                if tool == "surgeon":
                    editing = arguments.get("op") not in READ_OPS
                    if editing and (self.read_only or not self._policy()["source_edits"]):
                        raise ControlPlaneError(f"profile {self.profile} permits perception, not source mutation")
                    return self._surgeon().call(arguments)
                if tool == "colony":
                    return self._colony(arguments)
                return self._workspace(arguments)
            except (ControlPlaneError, OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
                return {"ok": False, "error": {"code": "control_plane", "message": str(exc)}}

    def _colony(self, arguments: dict[str, object]) -> dict[str, object]:
        command = arguments.get("command")
        if command not in COLONY_COMMANDS:
            raise ControlPlaneError("unknown Colony command")
        if self.read_only and command in ("mark", "claim", "release"):
            raise ControlPlaneError("read-only transport cannot mutate scent or claims")
        bash = shutil.which("bash")
        if not bash:
            raise ControlPlaneError("the supplied Colony helper requires bash on PATH")
        argv = [bash, str(BUNDLE_ROOT / "tools/colony"), str(command)]
        if command == "mark":
            for key in ("kind", "place", "taste", "what"):
                if not isinstance(arguments.get(key), str) or not arguments[key]:
                    raise ControlPlaneError(f"mark requires {key}")
                argv.append(str(arguments[key]))
            for key, option in (("via", "--via"), ("breaks_if", "--breaks-if"), ("crosses", "--crosses")):
                if arguments.get(key):
                    argv.extend([option, str(arguments[key])])
        elif command in ("claim", "release"):
            if not isinstance(arguments.get("place"), str) or not arguments["place"]:
                raise ControlPlaneError(f"{command} requires place")
            argv.append(str(arguments["place"]))
        elif command == "sniff" and arguments.get("place"):
            argv.append(str(arguments["place"]))
        env = dict(os.environ, COLONY_DIR=str(self.root / ".colony"),
                   COLONY_ROOT=str(self.root), COLONY_WORKER=str(arguments.get("worker") or self.profile))
        completed = subprocess.run(argv, cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        return {"ok": completed.returncode == 0, "command": command, "exit_code": completed.returncode,
                "stdout": completed.stdout, "stderr": completed.stderr}

    def _metadata(self) -> dict[str, tuple[int, int]]:
        paths = [BUNDLE_ROOT / "workspace.json", self.config_dir / "config.toml"]
        paths.extend(sorted((self.config_dir / "agents").glob("*.toml")))
        paths.extend([self.root / "AGENTS.md", self.root / "SWARM.md"])
        result = {}
        for path in paths:
            try:
                stat = path.stat()
                result[str(path)] = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                continue
        return result

    def scan(self) -> dict[str, object]:
        """Observe file metadata changes and retain pageable events on disk."""
        with self._lock:
            current = self._metadata()
            changes = [path for path in sorted(current.keys() | self._baseline.keys())
                       if current.get(path) != self._baseline.get(path)]
            self._baseline = current
            for path in changes:
                self._sequence += 1
                event = {"cursor": self._sequence, "time": time.time(), "path": path,
                         "state": "changed" if path in current else "removed"}
                self._events.append(event)
                self._events = self._events[-2000:]
                event_dir = self._event_dir()
                event_dir.mkdir(parents=True, exist_ok=True)
                with (event_dir / f"{self.profile}-{os.getpid()}.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(event) + "\n")
            reload_result = self.refresh() if str(BUNDLE_ROOT / "workspace.json") in changes else None
            return {"ok": reload_result is None or reload_result.get("ok", False),
                    "changed_paths": changes, "cursor": self._sequence, "reload": reload_result}

    def _event_dir(self) -> Path:
        """Keep project observations alongside that project's Colony state."""
        return self.root / ".colony/control-plane"

    def _workspace(self, arguments: dict[str, object]) -> dict[str, object]:
        op = arguments.get("op")
        if op == "refresh":
            return self.refresh()
        if op == "scan":
            return self.scan()
        if op == "events":
            cursor, limit = int(arguments.get("cursor", 0)), int(arguments.get("limit", 50))
            if cursor < 0 or not 1 <= limit <= 200:
                raise ControlPlaneError("events requires cursor >= 0 and limit 1..200")
            events = [event for event in self._events if int(event["cursor"]) > cursor]
            page = events[:limit]
            return {"ok": True, "events": page, "cursor": page[-1]["cursor"] if page else cursor,
                    "has_more": len(events) > limit, "oldest_cursor": self._events[0]["cursor"] if self._events else 0}
        if op != "status":
            raise ControlPlaneError("workspace op must be status, refresh, scan, or events")
        return {"ok": self._registry_error is None, "root": str(self.root), "bundle": str(BUNDLE_ROOT),
                "config_dir": str(self.config_dir), "profile": self.profile, "policy": self._policy(),
                "transports": ["cli", "stdio-mcp", "app-server-dynamic"],
                "watch_scope": sorted(self._baseline), "reload_error": self._registry_error,
                "watch_kind": "metadata polling; credential files excluded", "cursor": self._sequence}


class GlobalWorkspaceHost(WorkspaceHost):
    """Route one installed tool surface to explicit projects with isolated state.

    The base host supplies policy and schemas, never source operations. Every
    request selects an existing absolute project directory; server cwd and the
    installation directory cannot silently become the editing target.
    """

    def __init__(self, config_dir: str, profile: str = "all",
                 read_only: bool = False) -> None:
        self._projects: dict[Path, WorkspaceHost] = {}
        super().__init__(str(BUNDLE_ROOT), config_dir, profile, read_only)

    def _metadata(self) -> dict[str, tuple[int, int]]:
        """Observe the global registry and instruction plane without credentials."""
        paths = [BUNDLE_ROOT / "workspace.json", self.config_dir / "config.toml",
                 self.config_dir / "AGENTS.md"]
        paths.extend(sorted((self.config_dir / "agents").glob("*.toml")))
        result = {}
        for path in paths:
            try:
                stat = path.stat()
                result[str(path)] = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                continue
        return result

    def _event_dir(self) -> Path:
        """Persist global observations separately from all source projects."""
        return self.config_dir / "somnus-workspace-events"

    def refresh(self) -> dict[str, object]:
        """Apply a valid specialization update to every already selected project."""
        result = super().refresh()
        if result.get("ok"):
            for host in self._projects.values():
                host.refresh()
        return result

    def tool_specs(self) -> list[dict[str, object]]:
        """Require the current project's absolute path on each global tool call."""
        specs = copy.deepcopy(super().tool_specs())
        for tool in specs:
            schema = tool["inputSchema"]
            assert isinstance(schema, dict)
            properties = schema["properties"]
            required = schema["required"]
            assert isinstance(properties, dict) and isinstance(required, list)
            properties["project_root"] = {
                "type": "string", "description": "Absolute existing project directory from the current codex session cwd. Required on every call; never the installed bundle by default."}
            required.append("project_root")
        return specs

    def call(self, tool: str, arguments: object) -> dict[str, object]:
        """Validate explicit routing before invoking real per-project tools.

        Args:
            tool: A tool authorized by this server's specialization profile.
            arguments: JSON object with an absolute existing project_root.
        Returns:
            Constituent output with the selected root, or a structured error.
        """
        with self._lock:
            if tool not in self._policy()["tools"]:
                return {"ok": False, "error": {"code": "profile_tool", "message": f"{tool} is absent from {self.profile}"}}
            if not isinstance(arguments, dict):
                return {"ok": False, "error": {"code": "bad_request", "message": "arguments must be an object"}}
            selected = arguments.get("project_root")
            if not isinstance(selected, str) or not selected or not Path(selected).is_absolute():
                return {"ok": False, "error": {"code": "project_root", "message": "project_root must be an absolute existing project directory"}}
            try:
                root = Path(selected).resolve(strict=True)
                if not root.is_dir():
                    raise ControlPlaneError("project_root must be a directory")
                payload = {key: value for key, value in arguments.items() if key != "project_root"}
                if tool == "workspace" and payload.get("op") in ("scan", "events", "refresh"):
                    result = self._workspace(payload)
                else:
                    host = self._projects.get(root)
                    if host is None:
                        host = WorkspaceHost(str(root), str(self.config_dir), self.profile, self.read_only)
                        self._projects[root] = host
                    result = host.call(tool, payload)
                return {**result, "project_root": str(root), "global_install": True}
            except (ControlPlaneError, OSError, ValueError, TypeError) as exc:
                return {"ok": False, "error": {"code": "project_root", "message": str(exc)}}


def serve(host: WorkspaceHost, interval: float = 1.0) -> int:
    """Serve stdio MCP and observe config changes while requests are idle."""
    lock, stopped = threading.Lock(), threading.Event()

    def send(payload: dict[str, object]) -> None:
        with lock:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    def watch() -> None:
        while not stopped.wait(interval):
            try:
                changes = host.scan()
                if changes.get("reload") and changes["reload"].get("changed"):
                    send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            except (OSError, ValueError, ControlPlaneError) as exc:
                print(f"control-plane watch error: {exc}", file=sys.stderr)

    watcher = threading.Thread(target=watch, name="codex-plane-watch", daemon=True)
    watcher.start()
    try:
        for line in sys.stdin:
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("JSON-RPC request must be an object")
            except ValueError as exc:
                send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}})
                continue
            request_id, method = message.get("id"), message.get("method")
            if request_id is None:
                continue
            params = message.get("params", {})
            if not isinstance(params, dict):
                send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "params must be an object"}})
                continue
            if method == "initialize":
                result = {"protocolVersion": params.get("protocolVersion", "2024-11-05"),
                          "capabilities": {"tools": {"listChanged": True}},
                          "serverInfo": {"name": "codex-workspace-plane", "version": "1.1.0"},
                          "instructions": "Use your caste's supplied contract. Surgeon owns file edits; Colony owns scent and claims. Config changes are observed and profile refresh is explicit." +
                          (" Global mode: pass the absolute current project directory as project_root on every call. Journals and Colony state belong to that project." if isinstance(host, GlobalWorkspaceHost) else "")}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": host.tool_specs()}
            elif method == "tools/call":
                outcome = host.call(str(params.get("name", "")), params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(outcome, ensure_ascii=False)}],
                          "isError": not outcome.get("ok", False)}
            else:
                send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"unknown method {method}"}})
                continue
            send({"jsonrpc": "2.0", "id": request_id, "result": result})
    finally:
        stopped.set()
        watcher.join(timeout=2)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run a direct request, inspect schemas, or serve the global MCP adapter."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    routing = parser.add_mutually_exclusive_group()
    routing.add_argument("--root")
    routing.add_argument("--global", dest="global_mode", action="store_true")
    parser.add_argument("--config-dir", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--profile", default="all")
    parser.add_argument("--read-only", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve")
    server.add_argument("--watch-interval", type=float, default=1.0)
    call = commands.add_parser("call")
    call.add_argument("tool")
    call.add_argument("request", help="JSON object or - to read stdin")
    commands.add_parser("spec")
    args = parser.parse_args(argv)
    try:
        host = (GlobalWorkspaceHost(args.config_dir, args.profile, args.read_only)
                if args.global_mode else WorkspaceHost(args.root or os.getcwd(), args.config_dir, args.profile, args.read_only))
        if args.command == "serve":
            if args.watch_interval <= 0:
                raise ControlPlaneError("watch interval must be positive")
            return serve(host, args.watch_interval)
        if args.command == "spec":
            print(json.dumps({"mcp_tools": host.tool_specs(), "dynamicTools": host.dynamic_specs()}, indent=2))
            return 0
        payload = json.loads(sys.stdin.read() if args.request == "-" else args.request)
        result = host.call(args.tool, payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    except (ControlPlaneError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
