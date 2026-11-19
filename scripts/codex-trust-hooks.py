#!/usr/bin/env -S uv run --script
"""Approve the installed Codex plugin hooks managed by plugin.sh."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys


def trust_hooks(server, codex_home, plugin_ids):
    request_id = 0

    def call(method, params):
        nonlocal request_id
        request_id += 1
        server.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
        server.stdin.flush()
        for line in server.stdout:
            response = json.loads(line)
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(f"{method}: {response['error']['message']}")
                return response["result"]
        raise RuntimeError(f"Codex closed the connection during {method}")

    cache = codex_home / "plugins" / "cache"
    roots = {}
    for plugin_id in plugin_ids:
        name, marketplace = plugin_id.split("@")
        roots[plugin_id] = cache / marketplace / name

    def installed_hooks():
        hooks = []
        for entry in call("hooks/list", {"cwds": [str(codex_home)]})["data"]:
            for warning in [*entry["warnings"], *(error["path"] for error in entry["errors"])]:
                if any(str(root) + "/" in warning for root in roots.values()):
                    raise RuntimeError(warning)
            for hook in entry["hooks"]:
                root = roots.get(hook["pluginId"])
                if root is None:
                    continue
                if (hook["source"] != "plugin"
                        or not Path(hook["sourcePath"]).resolve().is_relative_to(root)
                        or not hook["key"].startswith(hook["pluginId"] + ":")):
                    raise RuntimeError(f"Unexpected source for {hook['key']}: {hook['sourcePath']}")
                hooks.append(hook)
        return hooks

    call("initialize", {"clientInfo": {"name": "lukas-plugin-hook-setup", "version": "1"}})
    hooks = installed_hooks()
    edits = []
    for hook in hooks:
        # Codex returns the declaration and installed bundle fingerprints together.
        hashes = hook["currentHash"].split("/")
        if len(hashes) not in (1, 2) or not all(re.fullmatch(r"sha256:[a-f0-9]{64}", digest) for digest in hashes):
            raise RuntimeError(f"Invalid approval hash for {hook['key']}")
        for field, digest in zip(("trusted_hash", "trusted_content_hash"), hashes):
            edits.append({
                "keyPath": f'hooks.state.{json.dumps(hook["key"])}.{field}',
                "value": digest,
                "mergeStrategy": "upsert",
            })

    if edits:
        call("config/batchWrite", {"edits": edits})
        verified = {hook["key"]: hook for hook in installed_hooks()}
        for hook in hooks:
            current = verified.get(hook["key"])
            if current is None or current["trustStatus"] != "trusted" or current["currentHash"] != hook["currentHash"]:
                raise RuntimeError(f"Could not verify hook approval for {hook['key']}")
            print(f"trusted {hook['key']}")


if __name__ == "__main__":
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
    try:
        with subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            cwd=codex_home,
            env={**os.environ, "CODEX_HOME": str(codex_home)},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        ) as server:
            try:
                trust_hooks(server, codex_home, sys.argv[1:])
            finally:
                server.terminate()
    except (OSError, RuntimeError) as error:
        sys.exit(f"Codex hook approval failed: {error}")
