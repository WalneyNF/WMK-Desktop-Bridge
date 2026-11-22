"""Testes offline de agentes e propostas, sem abrir Blender nem usar API externa."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import agent_hub


class AgentHubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "agents.json"
        self.original = agent_hub.AGENTS_FILE
        agent_hub.AGENTS_FILE = self.file

    def tearDown(self):
        agent_hub.AGENTS_FILE = self.original
        agent_hub.PENDING.clear()
        self.tmp.cleanup()

    def test_default_agents_and_register(self):
        names = [a["id"] for a in agent_hub.list_agents()]
        self.assertIn("blender-assistente", names)
        result = agent_hub.register_agent({"nome": "Especialista em objetos",
                 "provider": "ollama", "model": "qwen3:1.7b",
                 "system": "Ajude com modelagem.", "capabilities": ["blender_create"]})
        self.assertEqual(result["id"], "especialista-em-objetos")
        self.assertTrue(self.file.exists())

    def test_reject_unknown_capability(self):
        with self.assertRaises(ValueError):
            agent_hub.register_agent({"nome": "Perigoso", "provider": "ollama",
                "model": "qwen3:1.7b", "capabilities": ["executar_powershell"]})

    def test_reject_delete_or_python(self):
        for kind in ("delete_object", "execute_python", "run_shell"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                agent_hub._validate_action({"type": kind})

    def test_reject_outside_bounds(self):
        with self.assertRaises(ValueError):
            agent_hub._validate_action({"type":"create_cube","name":"Teste","size":3,"location":[500,0,0]})

    @patch("agent_hub._request")
    def test_plan_needs_approval(self, request):
        request.return_value = '{"explicacao":"Cria cubo","acoes":[{"type":"create_cube","name":"Cubo WMK","size":2,"location":[0,0,1]}]}'
        plan = agent_hub.propose("blender-assistente", "Crie um cubo de testes")
        self.assertFalse(plan["executado"])
        self.assertEqual(len(agent_hub.consume_approval(plan["proposta"])), 1)
        with self.assertRaises(PermissionError):
            agent_hub.consume_approval(plan["proposta"])

    @patch("agent_hub._request")
    def test_reject_unapproved_action_in_plan(self, request):
        request.return_value = '{"acoes":[{"type":"delete_object"}]}'
        with self.assertRaises(ValueError):
            agent_hub.propose("blender-assistente", "Apague todos os objetos")

if __name__ == "__main__":
    unittest.main()
