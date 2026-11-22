"""Testes básicos da política de workspace. Execute: py -m unittest discover -s tests -v"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workspace import _path, list_workspace, read_workspace
from security_policy import require_diagnostic_mode
from bridge import list_folder, folder_sizes, drives


class WorkspaceSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projeto"
        self.root.mkdir()
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('OK')\n", encoding="utf-8")
        (self.root / ".env").write_text("SECRET=test", encoding="utf-8")
        (self.root / "chave.pem").write_text("SECRET=test", encoding="utf-8")
        self.context = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root)})
        self.context.start()

    def tearDown(self):
        self.context.stop()
        self.tmp.cleanup()

    def test_read_allowed(self):
        self.assertIn("OK", read_workspace("src/main.py")["conteudo"])

    def test_blocks_traversal(self):
        with self.assertRaises(PermissionError):
            read_workspace("../fora.txt")

    def test_blocks_absolute_path(self):
        with self.assertRaises(PermissionError):
            _path(str((self.root.parent / "fora.txt").resolve()))

    def test_blocks_secrets(self):
        for name in (".env", "chave.pem", ".git/config"):
            with self.subTest(name=name):
                with self.assertRaises(PermissionError):
                    _path(name)

    def test_hides_secrets_in_listing(self):
        names = {x["nome"] for x in list_workspace()["itens"]}
        self.assertIn("src", names)
        self.assertNotIn(".env", names)
        self.assertNotIn("chave.pem", names)

    def test_blocks_generic_files(self):
        with self.assertRaises(PermissionError):
            list_folder(str(self.root))
        with self.assertRaises(PermissionError):
            folder_sizes(str(self.root))

    def test_blocks_diagnostics(self):
        with self.assertRaises(PermissionError):
            require_diagnostic_mode()
        with self.assertRaises(PermissionError):
            drives()

    def test_blocks_symlink(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("SECRET", encoding="utf-8")
        try:
            (self.root / "outside-link").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Sistema não permite criar symlink sem privilégios")
        with self.assertRaises(PermissionError):
            read_workspace("outside-link/secret.txt")


if __name__ == "__main__":
    unittest.main()
