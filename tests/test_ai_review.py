"""Testes sem acesso à rede para revisão Groq e Ollama do WMK Code Studio."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_ai import suggest_code


class AIReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projeto"
        self.root.mkdir()
        (self.root / "app.js").write_text("const somar=(a,b)=>a+b;\n", encoding="utf-8")
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.root),
                                             "GROQ_API_KEY": "chave_de_teste_nao_real"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def request(self, provider="groq", action="revisar"):
        return {"path":"app.js", "provider":provider,
                "model":"openai/gpt-oss-20b" if provider=="groq" else "qwen3:1.7b",
                "action":action,"code":"const somar=(a,b)=>a+b;",
                "instruction":"Revise a função de soma.",
                "consent":True}

    @patch("code_ai._fetch")
    def test_groq_review_accepts_plain_text(self, fetch):
        fetch.return_value = {"choices":[{"finish_reason":"stop",
            "message":{"content":"O código soma os parâmetros corretamente."}}]}
        response = suggest_code(self.request())
        self.assertIn("corretamente",response["explicacao"])
        self.assertIsNone(response["codigo"])
        body = fetch.call_args.args[1]
        self.assertNotIn("response_format",body)

    @patch("code_ai._fetch")
    def test_groq_edit_requires_structured_json(self, fetch):
        fetch.return_value = {"choices":[{"finish_reason":"stop",
            "message":{"content":'{"explicacao":"Incluído ponto e vírgula","codigo":"const somar = (a,b) => a + b;"}'}}]}
        response = suggest_code(self.request(action="corrigir"))
        self.assertIn("somar",response["codigo"])
        self.assertFalse(response["salvo"])
        self.assertIn("response_format",fetch.call_args.args[1])
        self.assertEqual((self.root / "app.js").read_text(encoding="utf-8"),"const somar=(a,b)=>a+b;\n")

    @patch("code_ai._fetch")
    def test_ollama_review_accepts_plain_text(self, fetch):
        fetch.return_value = {"message":{"content":"Função simples."}}
        response = suggest_code(self.request(provider="ollama"))
        self.assertEqual(response["explicacao"],"Função simples.")
        self.assertNotIn("format",fetch.call_args.args[1])

    def test_missing_groq_key_explains_problem(self):
        os.environ.pop("GROQ_API_KEY",None)
        with self.assertRaisesRegex(RuntimeError,"GROQ_API_KEY"):
            suggest_code(self.request())

    @patch("code_ai._fetch")
    def test_provider_groq_accepts_valid_model_name(self, fetch):
        from code_ai import test_provider
        fetch.return_value = {"choices":[{"message":{"content":"OK"},"finish_reason":"stop"}]}
        result = test_provider({"provider":"groq", "model":"openai/gpt-oss-20b", "consent":True})
        self.assertTrue(result["ok"])
        self.assertEqual(result["arquivos_lidos"],0)

    @patch("code_ai._fetch")
    def test_provider_ollama_accepts_valid_model_name(self, fetch):
        from code_ai import test_provider
        fetch.return_value = {"message":{"content":"OK"}}
        result = test_provider({"provider":"ollama", "model":"qwen3:1.7b", "consent":True})
        self.assertTrue(result["ok"])

    def test_missing_consent(self):
        payload=self.request()
        payload["consent"]=False
        with self.assertRaises(PermissionError):
            suggest_code(payload)


if __name__ == "__main__":
    unittest.main()
