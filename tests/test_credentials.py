"""Testes offline da seleção de credenciais, sem usar chaves reais ou DPAPI."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import credential_store
import code_ai


class CredentialsTests(unittest.TestCase):
    def test_environment_key_visible(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_example_for_wmk"}, clear=False):
            with patch.object(credential_store.os, "name", "posix"):
                self.assertEqual(credential_store.get("GROQ_API_KEY"), "gsk_test_key_example_for_wmk")
                self.assertTrue(credential_store.status("GROQ_API_KEY")["configurada"])

    def test_reject_unsafe_credential_type(self):
        with self.assertRaises(ValueError):
            credential_store.save("MALICIOUS_KEY", "x" * 32)

    def test_status_will_follow_same_credential_store_as_suggest(self):
        with patch("code_ai.credential_status", return_value={"configurada":True, "origem":"DPAPI Windows"}):
            state=code_ai.ai_status()
            self.assertTrue(state["groq_configurado"])
            self.assertEqual(state["groq_chave_origem"],"DPAPI Windows")

    def test_missing_key_message_prompts_in_app_setup(self):
        from code_ai import suggest_code
        with tempfile.TemporaryDirectory() as base:
            project=Path(base)/"project"
            project.mkdir()
            with patch.dict(os.environ, {"WMK_WORKSPACE":str(project)}, clear=False):
                with patch("code_ai.get_credential", return_value=""):
                    payload={"path":"novo.js","provider":"groq","model":"openai/gpt-oss-20b",
                             "action":"gerar","code":"","instruction":"Crie uma funcao soma", "consent":True}
                    with self.assertRaisesRegex(RuntimeError,"Configurar chave Groq"):
                        suggest_code(payload)


if __name__=="__main__":
    unittest.main()
