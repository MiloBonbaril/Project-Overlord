#!/usr/bin/env python3
"""Tests CLI du linter : exemple canonique, codes de sortie et R0 à R12."""

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "outils/verifie-catalogue.py"
CANONICAL = ROOT / "contenu/catalogue/exemple-canonique.json"
SETTINGS = ROOT / "contenu/reglages"


class CatalogueLintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalogue = self.root / "catalogue"
        self.settings = self.root / "reglages"
        self.catalogue.mkdir()
        shutil.copytree(SETTINGS, self.settings)
        self.data = json.loads(CANONICAL.read_text(encoding="utf-8"))

    def tearDown(self):
        self.temp.cleanup()

    def run_lint(self, data=None, raw=None, extra=None):
        if raw is not None:
            (self.catalogue / "case.json").write_text(raw, encoding="utf-8")
        else:
            (self.catalogue / "case.json").write_text(json.dumps(data if data is not None else self.data), encoding="utf-8")
        if extra is not None:
            (self.catalogue / "extra.json").write_text(json.dumps(extra), encoding="utf-8")
        return subprocess.run(
            ["python3", str(LINTER), str(self.catalogue), "--reglages", str(self.settings)],
            text=True, capture_output=True, check=False,
        )

    def assert_rule(self, rule, mutate):
        data = copy.deepcopy(self.data)
        mutate(data)
        result = self.run_lint(data)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"ERREUR {rule} —", result.stdout)
        self.assertIn("\nQuoi : ", result.stdout)
        self.assertIn("\nAction : ", result.stdout)

    def test_canonical_passes_all_rules(self):
        result = self.run_lint()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("règles R0 à R12 validées", result.stdout)

    def test_r0_unreadable_json_returns_2(self):
        result = self.run_lint(raw="{")
        self.assertEqual(2, result.returncode)
        self.assertIn("ERREUR R0 —", result.stdout)

    def test_r1_array_root(self):
        result = self.run_lint(data=[])
        self.assertEqual(1, result.returncode)
        self.assertIn("ERREUR R1 —", result.stdout)

    def test_r2_unique_id(self):
        result = self.run_lint(extra=copy.deepcopy(self.data))
        self.assertEqual(1, result.returncode)
        self.assertIn("ERREUR R2 —", result.stdout)

    def test_r3_required_fields_and_types(self):
        self.assert_rule("R3", lambda data: data.pop("options"))

    def test_r4_known_unique_nonempty_tags(self):
        self.assert_rule("R4", lambda data: data["options"][0].update(etiquettes=["inconnue"]))

    def test_r5_path_comes_from_schema(self):
        self.assert_rule("R5", lambda data: data["conditions"][0].update(chemin="lieu.inventee"))

    def test_r6_operator_matches_type(self):
        self.assert_rule("R6", lambda data: data["conditions"][1].update(operateur=">"))

    def test_r7_scale_value_is_known(self):
        self.assert_rule("R7", lambda data: data["conditions"][0].update(valeur="metropole"))

    def test_r8_role_reference_resolves(self):
        self.assert_rule("R8", lambda data: data["conditions"][2].update(valeur="empire"))

    def test_r9_effect_magnitude_is_known(self):
        self.assert_rule("R9", lambda data: data["options"][0]["effets"][0].update(ampleur="colossale"))

    def test_r10_read_only_target_is_rejected(self):
        self.assert_rule("R10", lambda data: data["options"][0]["effets"][0].update(cible="lieu.distance_donjon"))

    def test_r10_hidden_information_has_business_message(self):
        self.assert_rule("R10", lambda data: data["conditions"][0].update(chemin="joueur.archetype"))

    def test_r11_forbidden_clause_matches_option_tags(self):
        self.assert_rule("R11", lambda data: data["options"][0].update(interdit_par=["violence"]))

    def test_r12_simulated_quantity_in_digits(self):
        self.assert_rule("R12", lambda data: data["options"][0].update(prose="Le lieu compte 700 habitants."))

    def test_r12_simulated_quantity_in_words(self):
        self.assert_rule("R12", lambda data: data["options"][0].update(prose="Le voyage a duré trois jours."))


if __name__ == "__main__":
    unittest.main()
