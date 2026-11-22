"""Teste de integração offline: IA lê HTML CSS JS e propõe correção real."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import project_agent
import mcp_approvals


class ProjectAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "calculadora"
        self.folder.mkdir()
        (self.folder / "index.html").write_text('<button>AC</button><script src="app.js"></script>', encoding="utf-8")
        (self.folder / "app.js").write_text('const soma = (a,b) => a+b;\n', encoding="utf-8")
        (self.folder / "style.css").write_text('button { color: cyan; }\n', encoding="utf-8")
        self.db = mcp_approvals.DB
        mcp_approvals.DB = Path(self.temp.name) / "approvals.sqlite"
        self.env = patch.dict(os.environ, {"WMK_WORKSPACE": str(self.folder)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        mcp_approvals.DB = self.db
        self.temp.cleanup()

    def task(self):
        return {"path": "index.html", "provider": "groq",
                "model": "openai/gpt-oss-20b", "consent": True,
                "task": "Adicione um nome acessível ao botão AC"}

    @patch("project_agent._request")
    def test_reads_related_sources_and_applies_only_on_human_approval(self, request):
        request.return_value = json.dumps({
            "resumo":"Adicionei nome acessível",
            "alteracoes":[{"arquivo":"index.html","motivo":"Acessibilidade",
                           "substituicoes":[{"antes":"<button>AC</button>",
                                            "depois":'<button aria-label="Limpar">AC</button>'}]}]
        })
        result = project_agent.project_task(self.task())
        self.assertEqual(set(result["arquivos_lidos"]), {"index.html", "app.js", "style.css"})
        self.assertEqual(result["arquivos_modificados"], 0)
        self.assertEqual(len(result["propostas"]), 1)
        self.assertEqual((self.folder / "index.html").read_text(encoding="utf-8"),
                         '<button>AC</button><script src="app.js"></script>')
        prompt = json.loads(request.call_args.args[3])
        self.assertEqual(len(prompt["arquivos_autorizados"]), 3)
        proposed = mcp_approvals.get_proposal(result["propostas"][0]["id"])
        self.assertIn("aria-label", proposed["diff"])
        mcp_approvals.approve(proposed["id"], proposed["sha256"])
        self.assertIn("aria-label", (self.folder / "index.html").read_text(encoding="utf-8"))

    @patch("project_agent._request")
    def test_groq_request_disables_remote_json_mode(self, request):
        request.return_value='{"resumo":"ok","alteracoes":[]}'
        project_agent.project_task(self.task())
        self.assertIs(request.call_args.kwargs["json_mode"], False)
        self.assertEqual(request.call_args.kwargs["max_completion_tokens"], 8192)

    @patch("project_agent._request")
    def test_json_in_markdown_fence_accepted(self, request):
        request.return_value='```json\\n{"resumo":"Sem problemas","alteracoes":[]}\\n```'
        result=project_agent.project_task(self.task())
        self.assertEqual(result["status"],"sem_alteracoes")

    @patch("project_agent._request")
    def test_invalid_json_never_creates_proposal(self, request):
        request.return_value='Corrigi tudo no seu arquivo.'
        with self.assertRaisesRegex(ValueError,"JSON válido"):
            project_agent.project_task(self.task())
        self.assertEqual(mcp_approvals.list_pending(), [])

    @patch("project_agent._request")
    def test_false_claim_without_changes_does_not_write(self, request):
        request.return_value = '{"resumo":"Corrigido", "alteracoes":[]}'
        result=project_agent.project_task(self.task())
        self.assertEqual(result["status"], "sem_alteracoes")
        self.assertEqual(result["arquivos_modificados"], 0)
        self.assertEqual(mcp_approvals.list_pending(), [])

    @patch("project_agent._request")
    def test_reject_ambiguous_patch(self, request):
        request.return_value = json.dumps({"resumo":"teste",
            "alteracoes":[{"arquivo":"index.html",
                           "substituicoes":[{"antes":"nao_existe","depois":"x"}]}]})
        with self.assertRaisesRegex(ValueError,"Trecho original"):
            project_agent.project_task(self.task())
        self.assertEqual(mcp_approvals.list_pending(), [])

    @patch("project_agent._request")
    def test_reject_path_outside_context(self, request):
        request.return_value = json.dumps({"resumo":"teste",
             "alteracoes":[{"arquivo":"../segredo.txt","codigo":"hello"}]})
        with self.assertRaisesRegex(ValueError,"não fornecido"):
            project_agent.project_task(self.task())

    def test_requires_consent(self):
        payload=self.task()
        payload["consent"]=False
        with self.assertRaises(PermissionError):
            project_agent.project_task(payload)


if __name__ == "__main__":
    unittest.main()
