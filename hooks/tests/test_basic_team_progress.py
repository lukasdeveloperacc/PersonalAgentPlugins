import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "hooks" / "basic-team-progress.py"
WRAPPER = ROOT / "hooks" / "basic-team-progress.sh"


class HookTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.page = self.root / "docs/inprogress/run.html"
        self.page.parent.mkdir(parents=True)
        self.page.write_text("unchanged")
        self.state = Path(self.temp.name) / "state"

    def tearDown(self):
        self.temp.cleanup()

    def env(self, host="codex", **extra):
        env = os.environ.copy()
        env["XDG_STATE_HOME"] = str(self.state)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env.pop("CLAUDE_SESSION_ID", None)
        env.pop("CODEX_THREAD_ID", None)
        env.pop("CODEX_SESSION_ID", None)
        if host == "codex":
            env.update(CODEX_THREAD_ID="session-1", CODEX_SESSION_ID="session-1")
        else:
            env["CLAUDE_SESSION_ID"] = "session-1"
        env.update(extra)
        return env

    def run_json(self, args, payload=None, host="codex", env=None):
        return subprocess.run(["python3", str(ENGINE), *args], cwd=self.root,
                              env=env or self.env(host), input="" if payload is None else json.dumps(payload),
                              text=True, capture_output=True, check=True).stdout.strip()

    def arm(self, host="codex"):
        args = ["arm", str(self.page), "--host", host]
        env = self.env(host)
        if host == "claude":
            args += ["--session-id", "session-1"]
            env.pop("CLAUDE_SESSION_ID", None)
        raw = self.run_json(args, host=host, env=env)
        return json.loads(raw)["basic_team_hook"]

    def post(self, host="codex", name="Agent", receipt=None, **extra):
        event = {"session_id": "session-1", "tool_name": name, "turn_id": "turn-1"}
        if receipt:
            event["tool_response"] = json.dumps({"basic_team_hook": receipt})
        event["exit_code"] = 0
        if host == "claude" and receipt:
            event.pop("exit_code")
            event["tool_response"] = {"stdout": json.dumps({"basic_team_hook": receipt}), "stderr": "", "interrupted": False}
        event.update(extra)
        return self.run_json(["hook", "PostToolUse", "--host", host], event, host)

    def test_silent_until_explicit_verified_arm_for_both_hosts(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.assertEqual("", self.run_json(["hook", "PostToolUse", "--host", host],
                                  {"session_id": "session-1", "tool_name": "Agent", "turn_id": "turn-1"}, host))
                if host == "codex":
                    self.assertFalse(self.state.exists())
                receipt = self.arm(host)
                output = self.post(host, "Bash", receipt)
                self.assertIn("armed", output)
                self.assertIn(str(self.page), self.post(host))
        self.assertEqual("unchanged", self.page.read_text())

    def test_identity_failure_does_not_create_state(self):
        env = self.env(CODEX_THREAD_ID="one", CODEX_SESSION_ID="two")
        proc = subprocess.run(["python3", str(ENGINE), "arm", str(self.page), "--host", "codex"],
                              cwd=self.root, env=env, text=True, capture_output=True, check=True)
        self.assertIn("unarmed", proc.stdout)
        self.assertFalse(self.state.exists())

    def test_turn_and_child_mismatch_are_silent(self):
        receipt = self.arm()
        self.post("codex", "Bash", receipt)
        self.assertEqual("", self.post("codex", turn_id="turn-2"))
        env = self.env(CLAUDE_SESSION_ID="session-1")
        self.assertEqual("", self.run_json(["hook", "PostToolUse", "--host", "claude"],
                            {"session_id": "session-1", "tool_name": "Agent", "agent_id": "child"}, "claude", env))

    def test_prompt_and_resume_clear_active_state_and_stale_arm(self):
        receipt = self.arm()
        payload = {"session_id": "session-1", "tool_name": "Bash", "turn_id": "turn-1",
                   "tool_response": json.dumps({"basic_team_hook": receipt}), "exit_code": 0}
        self.run_json(["hook", "UserPromptSubmit", "--host", "codex"], {"session_id": "session-1"})
        self.assertEqual("", self.run_json(["hook", "PostToolUse", "--host", "codex"], payload))
        receipt = self.arm()
        self.run_json(["hook", "SessionStart", "--host", "codex"], {"session_id": "session-1", "source": "resume"})
        self.assertEqual("", self.run_json(["hook", "PostToolUse", "--host", "codex"], payload | {"tool_response": json.dumps({"basic_team_hook": receipt}), "exit_code": 0}))

    def test_failed_or_unproven_tool_and_bad_receipt_do_not_arm(self):
        receipt = self.arm()
        self.assertEqual("", self.post("codex", "Bash", receipt, exit_code=1))
        self.assertEqual("", self.post("codex", "Bash", receipt, exit_code=None))
        self.assertEqual("", self.post("codex"))
        self.assertEqual("", self.post("codex", "Bash", receipt | {"request_id": "x"}))

    def test_running_tool_response_is_not_a_successful_receipt(self):
        receipt = self.arm()
        self.assertEqual("", self.post("codex", "Bash", receipt, tool_response={"session_id": "running"}))
        self.assertEqual("", self.post("codex"))

    def test_disarm_is_bound_to_run_and_page_is_not_touched(self):
        receipt = self.arm()
        self.post("codex", "Bash", receipt)
        disarm = self.run_json(["disarm", "--host", "codex", "--run-id", receipt["run_id"]])
        payload = {"session_id": "session-1", "tool_name": "Bash", "turn_id": "turn-1",
                   "tool_response": disarm, "exit_code": 0}
        self.run_json(["hook", "PostToolUse", "--host", "codex"], payload)
        self.assertEqual("", self.post("codex"))
        self.assertEqual("unchanged", self.page.read_text())

    def test_child_lifecycle_does_not_clear_main_and_latest_arm_replaces_page(self):
        receipt = self.arm()
        self.post("codex", "Bash", receipt)
        child_event = {"session_id": "session-1", "source": "resume", "agent_id": "child"}
        self.run_json(["hook", "SessionStart", "--host", "codex"], child_event)
        self.assertIn(str(self.page), self.post("codex"))
        newer = self.root / "docs/inprogress/new.html"
        newer.write_text("unchanged too")
        args = ["arm", str(newer), "--host", "codex"]
        latest = json.loads(self.run_json(args))["basic_team_hook"]
        self.post("codex", "Bash", latest)
        reminder = self.post("codex")
        self.assertIn(str(newer), reminder)
        self.assertNotIn(str(self.page), reminder)

    def test_late_arm_receipt_cannot_replace_newer_request(self):
        old = self.arm()
        newer = self.root / "docs/inprogress/new.html"
        newer.write_text("unchanged too")
        new = json.loads(self.run_json(["arm", str(newer), "--host", "codex"]))["basic_team_hook"]
        self.post("codex", "Bash", new)
        self.assertEqual("", self.post("codex", "Bash", old))
        reminder = self.post("codex")
        self.assertIn(str(newer), reminder)
        self.assertNotIn(str(self.page), reminder)

    def test_foreign_receipt_does_not_remove_its_pending_request(self):
        receipt = self.arm("claude")
        pending = self.state / "lukas-plugin/basic-team" / ("request-" + receipt["request_id"] + ".json")
        self.assertTrue(pending.exists())
        self.assertEqual("", self.post("codex", "Bash", receipt))
        self.assertTrue(pending.exists())
        self.assertIn("armed", self.post("claude", "Bash", receipt))

    def test_receipt_request_id_must_be_hex(self):
        receipt = self.arm()
        receipt["request_id"] = "g" * 48
        self.assertEqual("", self.post("codex", "Bash", receipt))

    def test_codex_root_compatibility_variable_does_not_select_claude(self):
        env = self.env()
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        env["PLUGIN_ROOT"] = str(ROOT)
        event = {"session_id": "session-1", "tool_name": "Agent", "turn_id": "turn-1"}
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps(event), text=True, capture_output=True, check=True)
        self.assertEqual("", proc.stdout)
        receipt = self.arm("codex")
        event.update({"tool_name": "Bash", "exit_code": 0,
                      "tool_response": json.dumps({"basic_team_hook": receipt}), "exit_code": 0})
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps(event), text=True, capture_output=True, check=True)
        self.assertIn("armed", proc.stdout)
        reminder_event = {"session_id": "session-1", "tool_name": "Agent", "turn_id": "turn-1"}
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps(reminder_event), text=True, capture_output=True, check=True)
        self.assertIn(str(self.page), proc.stdout)

    def test_claude_wrapper_auto_host_without_session_environment(self):
        env = self.env("claude")
        env.pop("CLAUDE_SESSION_ID", None)
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        receipt = self.arm("claude")
        event = {"session_id": "session-1", "tool_name": "Bash",
                 "tool_response": {"stdout": json.dumps({"basic_team_hook": receipt}),
                                   "stderr": "", "interrupted": False}}
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps(event), text=True, capture_output=True, check=True)
        self.assertIn("armed", proc.stdout)
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps({"session_id": "session-1", "tool_name": "Agent"}),
                              text=True, capture_output=True, check=True)
        self.assertIn(str(self.page), proc.stdout)
        proc = subprocess.run(["bash", str(WRAPPER), "SessionStart"], cwd=self.root, env=env,
                              input=json.dumps({"session_id": "session-1", "source": "resume"}),
                              text=True, capture_output=True, check=True)
        self.assertEqual("", proc.stdout)
        proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse"], cwd=self.root, env=env,
                              input=json.dumps({"session_id": "session-1", "tool_name": "Agent"}),
                              text=True, capture_output=True, check=True)
        self.assertEqual("", proc.stdout)

    def test_wrapper_is_silent_on_malformed_payload_and_both_root_conventions(self):
        for root_var in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
            env = self.env()
            env[root_var] = str(ROOT)
            proc = subprocess.run(["bash", str(WRAPPER), "PostToolUse", "--host", "codex"],
                                 env=env, input="{bad", text=True, capture_output=True)
            self.assertEqual("", proc.stdout)
            self.assertEqual("", proc.stderr)
            env = self.env("claude")
            env.pop("CLAUDE_SESSION_ID", None)
            env[root_var] = str(ROOT)
            command = 'bash "${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}/hooks/basic-team-progress.sh" UserPromptSubmit'
            proc = subprocess.run(["bash", "-c", command], cwd=self.root, env=env,
                                 input=json.dumps({"session_id": "session-1"}), text=True,
                                 capture_output=True, check=True)
            self.assertEqual("", proc.stdout)
        self.assertEqual("unchanged", self.page.read_text())



if __name__ == "__main__":
    unittest.main()
