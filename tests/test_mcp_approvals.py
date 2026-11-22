"""Testes de propostas MCP: nenhuma escrita antes da aprovação humana."""
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mcp_approvals


class MCPApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projeto"
        self.root.mkdir()
        self.old_db = mcp_approvals.DB
        mcp_approvals.DB = Path(self.tmp.name) / "test-proposals.sqlite3"
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        mcp_approvals.DB = self.old_db
        self.tmp.cleanup()

    def test_create_requires_human_approval(self):
        created = mcp_approvals.propose_write("codigo.py", "print('wmk')\n", "Criar exemplo")
        self.assertFalse((self.root / "codigo.py").exists())
        self.assertEqual(len(mcp_approvals.list_pending()), 1)
        data = mcp_approvals.get_proposal(created["id"])
        self.assertIn("print", data["diff"])
        result = mcp_approvals.approve(created["id"], data["sha256"])
        self.assertEqual(result["status"], "aprovada")
        self.assertEqual((self.root / "codigo.py").read_text(encoding="utf-8"), "print('wmk')\n")
        with self.assertRaises(ValueError):
            mcp_approvals.approve(created["id"], data["sha256"])

    def test_traversal_denied(self):
        with self.assertRaises(PermissionError):
            mcp_approvals.propose_write("../fora.py", "x=1", "teste")

    def test_sensitive_file_denied(self):
        with self.assertRaises(PermissionError):
            mcp_approvals.propose_write(".env", "TOKEN=abc", "teste")

    def test_denied_extension(self):
        with self.assertRaises(PermissionError):
            mcp_approvals.propose_write("script.exe", "abc", "teste")

    def test_reject_keeps_existing_file(self):
        source = self.root / "codigo.py"
        source.write_text("x=1", encoding="utf-8")
        created = mcp_approvals.propose_write("codigo.py", "x=2", "Mudar valor")
        mcp_approvals.reject(created["id"])
        self.assertEqual(source.read_text(encoding="utf-8"), "x=1")

    def test_stale_version_denied(self):
        source = self.root / "codigo.py"
        source.write_text("x=1", encoding="utf-8")
        created = mcp_approvals.propose_write("codigo.py", "x=2", "Mudar valor")
        source.write_text("x=99", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            mcp_approvals.get_proposal(created["id"])
        self.assertEqual(source.read_text(encoding="utf-8"), "x=99")


if __name__ == "__main__":
    unittest.main()
