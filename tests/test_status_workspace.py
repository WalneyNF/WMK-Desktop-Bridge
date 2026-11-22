"""Regressão do endpoint /api/status: sem falha se workspace não existir."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge import diagnostic


class DiagnosticStatusTests(unittest.TestCase):
    def test_inexistent_workspace_does_not_crash(self):
        with tempfile.TemporaryDirectory() as root:
            missing = str(Path(root) / "NAO_EXISTE")
            with patch.dict(os.environ, {"WMK_WORKSPACE": missing}):
                result = diagnostic()
                self.assertEqual(result["politica"]["modo"], "projeto_restrito")
                self.assertFalse(result["workspace"]["configurado"])
                self.assertEqual(result["raizes_autorizadas"], [])
                self.assertIn("aviso", result)

    def test_valid_project_reports_root_and_not_drives(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root) / "projeto"
            project.mkdir()
            with patch.dict(os.environ, {"WMK_WORKSPACE": str(project)}):
                result = diagnostic()
                self.assertEqual(result["politica"]["modo"], "projeto_restrito")
                self.assertTrue(result["workspace"]["configurado"])
                self.assertEqual(result["raizes_autorizadas"], [str(project.resolve())])
                self.assertEqual(result["unidades"], [])


if __name__ == "__main__":
    unittest.main()
