"""Testes locais de inicialização controlada do motor OpenCode.

Todos os processos e chamadas de rede são simulados. Não chama Groq nem OpenCode.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import opencode_bridge


class OpenCodeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        self.original_config = opencode_bridge.CONFIG
        opencode_bridge.CONFIG = Path(self.tmp.name) / "config" / "policy.json"
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root)})
        self.env.start()
        opencode_bridge.PROCESS = None
        opencode_bridge.PASSWORD = None
        opencode_bridge.PROJECT = None
        opencode_bridge.LOG = None

    def tearDown(self):
        if opencode_bridge.LOG:
            opencode_bridge.LOG.close()
        opencode_bridge.PROCESS = None
        opencode_bridge.PASSWORD = None
        opencode_bridge.PROJECT = None
        opencode_bridge.LOG = None
        opencode_bridge.CONFIG = self.original_config
        self.env.stop()
        self.tmp.cleanup()

    def test_policy_blocks_external_folders_and_shell(self):
        path = opencode_bridge._policy()
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn({"action":"shell","resource":"*","effect":"deny"}, data["permissions"])
        self.assertIn({"action":"external_directory","resource":"*","effect":"deny"},data["permissions"])
        self.assertIn({"action":"edit","resource":"*","effect":"ask"},data["permissions"])
        self.assertIn({"action":"tool.use","resource":"shell:*","effect":"deny"},data["policies"])

    @patch("opencode_bridge._healthy", return_value=True)
    @patch("opencode_bridge._command", return_value="opencode")
    @patch("opencode_bridge.subprocess.Popen")
    def test_start_runs_actual_opencode_cli_in_workspace(self, popen, command, healthy):
        fake = MagicMock()
        fake.poll.return_value = None
        fake.pid = 1234
        popen.return_value = fake
        result = opencode_bridge.start()
        self.assertTrue(result["ativo"])
        self.assertEqual(result["pasta"], str(self.root.resolve()))
        cmd = popen.call_args.args[0]
        self.assertIn("serve",cmd)
        self.assertIn("127.0.0.1",cmd)
        self.assertEqual(popen.call_args.kwargs["cwd"],str(self.root.resolve()))
        env = popen.call_args.kwargs["env"]
        self.assertTrue(env["OPENCODE_PASSWORD"])
        self.assertEqual(env["OPENCODE_PASSWORD"],result["senha"])
        self.assertEqual(env["OPENCODE_CONFIG"],str(opencode_bridge.CONFIG))
        self.assertNotIn("0.0.0.0",cmd)
        opencode_bridge.stop()
        fake.terminate.assert_called_once()

    @patch("opencode_bridge._command", return_value="opencode")
    @patch("opencode_bridge.subprocess.Popen")
    def test_start_never_runs_without_workspace(self, popen, command):
        os.environ.pop("WMK_WORKSPACE")
        with self.assertRaises(RuntimeError):
            opencode_bridge.start()
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
