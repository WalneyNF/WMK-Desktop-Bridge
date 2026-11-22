"""Testes offline do WMK Coding Agent: ações iterativas limitadas e sem escrita."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import coding_agent
import mcp_approvals


class CodingAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        (self.root / "main.py").write_text("print('base')\n", encoding="utf-8")
        self.old_db = mcp_approvals.DB
        mcp_approvals.DB = Path(self.tmp.name) / "proposals.sqlite3"
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        mcp_approvals.DB = self.old_db
        self.tmp.cleanup()

    def test_requires_permission(self):
        with self.assertRaises(PermissionError):
            coding_agent.coding_task("codigo-leitura", "Analise o programa", False)

    @patch("coding_agent._request")
    def test_read_and_propose_do_not_write(self, request):
        request.side_effect = [
            '{"acao":"list","path":""}',
            '{"acao":"read","path":"main.py"}',
            '{"acao":"propose_write","path":"main.py","content":"print(42)\\n","description":"Atualizar exemplo"}',
            '{"acao":"finish","message":"Proposta pronta"}',
        ]
        result = coding_agent.coding_task("codigo-leitura", "Melhore este pequeno exemplo", True)
        self.assertEqual(result["status"], "concluido")
        self.assertEqual(len(result["propostas"]), 1)
        self.assertEqual((self.root / "main.py").read_text(encoding="utf-8"), "print('base')\n")
        self.assertEqual(len(mcp_approvals.list_pending()), 1)

    @patch("coding_agent._request")
    def test_disallows_escape(self, request):
        request.return_value = '{"acao":"read","path":"../outside.py"}'
        with self.assertRaises(PermissionError):
            coding_agent.coding_task("codigo-leitura", "Leia fora do projeto", True)

    @patch("coding_agent._request")
    def test_rejects_shell(self, request):
        request.return_value = '{"acao":"shell","command":"Remove-Item C:\\\\test"}'
        with self.assertRaises(ValueError):
            coding_agent.coding_task("codigo-leitura", "Apague meus arquivos por comando", True)

    @patch("coding_agent._request")
    def test_limits_steps(self, request):
        request.return_value = '{"acao":"list","path":""}'
        result = coding_agent.coding_task("codigo-leitura", "Faça uma varredura simples", True)
        self.assertEqual(result["status"], "limite_de_passos")
        self.assertEqual(len(result["passos"]), coding_agent.MAX_STEPS)


if __name__ == "__main__":
    unittest.main()
