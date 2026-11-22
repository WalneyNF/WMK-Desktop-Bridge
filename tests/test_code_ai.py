"""Testes offline de segurança do assistente (sem chamadas ao Groq/Ollama)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_ai import suggest_code


class CodeAITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "projeto"
        self.root.mkdir()
        (self.root / "main.py").write_text("print('Olá')\n", encoding="utf-8")
        (self.root / ".env").write_text("TOKEN=12345678", encoding="utf-8")
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root), "GROQ_API_KEY": "teste"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def data(self, **changes):
        d = {"path": "main.py", "provider": "ollama", "action": "corrigir",
             "model": "qwen3:1.7b", "code": "print('Olá')", "instruction": "Corrigir",
             "consent": True}
        d.update(changes)
        return d

    def test_no_consent(self):
        with self.assertRaises(PermissionError), patch("code_ai._fetch") as fetch:
            suggest_code(self.data(consent=False))
        fetch.assert_not_called()

    def test_rejects_secret(self):
        with self.assertRaises(PermissionError), patch("code_ai._fetch") as fetch:
            suggest_code(self.data(code="api_key=super_secret_123456789"))
        fetch.assert_not_called()

    def test_rejects_parent(self):
        with self.assertRaises(PermissionError):
            suggest_code(self.data(path="../fora.py"))

    def test_rejects_absolute(self):
        with self.assertRaises(PermissionError):
            suggest_code(self.data(path=str(self.root.parent / "fora.py")))

    def test_rejects_sensitive(self):
        with self.assertRaises(PermissionError):
            suggest_code(self.data(path=".env"))

    def test_rejects_large_code(self):
        with self.assertRaises(ValueError):
            suggest_code(self.data(code="x" * 31000))

    def test_rejects_unknown_provider(self):
        with self.assertRaises(ValueError):
            suggest_code(self.data(provider="executar_shell"))

    @patch("code_ai._fetch")
    def test_suggestion_does_not_write(self, fetch):
        fetch.return_value = {"message": {"content": '{"explicacao":"Feito","codigo":"print(1)"}'}}
        reply = suggest_code(self.data())
        self.assertEqual(reply["codigo"], "print(1)")
        self.assertFalse(reply["salvo"])
        self.assertEqual((self.root / "main.py").read_text(encoding="utf-8"), "print('Olá')\n")

    @patch("code_ai._fetch")
    def test_explanation_has_no_patch(self, fetch):
        fetch.return_value = {"message": {"content": '{"explicacao":"Exemplo","codigo":null}'}}
        reply = suggest_code(self.data(action="explicar"))
        self.assertIsNone(reply["codigo"])


if __name__ == "__main__":
    unittest.main()
