#!/usr/bin/env python3
"""Tests ciblés de la boucle jouable du vertical slice."""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("joue_partie", ROOT / "outils/joue-partie.py")
GAME = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(GAME)


class PlayableLoopTests(unittest.TestCase):
    def test_resolution_thresholds_and_magnitude_reduction(self):
        resolution = GAME.load(ROOT / "contenu/reglages/resolution-serviteur.json")
        settings = GAME.load(ROOT / "contenu/reglages/ampleurs.json")
        expected = {
            0: ("adhesion", "majeure"),
            5: ("adhesion", "majeure"),
            10: ("reserve", "grande"),
            20: ("reserve", "grande"),
            25: ("resistance", "notable"),
        }
        for pool in (["yldra", "corvin"], ["orine", "tessia"]):
            for gap, (state, magnitude) in expected.items():
                with self.subTest(pool=pool, gap=gap):
                    actual_state, _, reduction = GAME.resolution_for_gap(gap, resolution)
                    self.assertEqual(actual_state, state)
                    self.assertEqual(GAME.reduced_magnitude("majeure", reduction, settings), magnitude)

    def test_magnitude_reduction_is_bounded_at_nul(self):
        settings = GAME.load(ROOT / "contenu/reglages/ampleurs.json")
        self.assertEqual(GAME.reduced_magnitude("nul", 2, settings), "nul")
        self.assertEqual(GAME.reduced_magnitude("infime", 2, settings), "nul")

    def test_compositions_are_selectable_and_deterministic(self):
        for pool in (["yldra", "corvin"], ["orine", "tessia"]):
            first = GAME.play(42, 4, pool=pool)
            second = GAME.play(42, 4, pool=pool)
            self.assertEqual(first, second)
            self.assertEqual(first["figures_du_vivier"], sorted(pool))
            self.assertEqual({entry["serviteur"] for entry in first["journal"]}, set(pool))

    def test_explicit_choice_and_turn_clause_are_recorded(self):
        preview = GAME.play(20260926, 1, pool=["yldra", "corvin"])
        choice = preview["journal"][0]["conseil"][1]["id"]
        result = GAME.play(20260926, 1, chosen=[choice], pool=["yldra", "corvin"], turn_clauses=[{"terreur"}])
        self.assertEqual(result["journal"][0]["action"], choice)
        self.assertEqual(result["journal"][0]["clauses"], ["terreur"])
        self.assertIn("resolution_probable", result["journal"][0])
        for hidden in ("score_max", "score_choisi", "ecart", "ampleurs", "etat_resolution"):
            self.assertNotIn(hidden, result["journal"][0])
            self.assertIn(hidden, result["journal_testeur"][0])

    def test_forbidden_preference_is_excluded_from_score_max(self):
        for seed in range(100):
            preview = GAME.play(seed, 8, pool=["yldra", "corvin"])
            candidate = next((entry for entry in preview["journal_testeur"] if any(
                option["id"] == "interdire" for option in entry["conseil"]
            )), None)
            if candidate:
                turn = candidate["tour"]
                choices = [entry["action"] for entry in preview["journal"][:turn]]
                choices[-1] = "tolerer"
                clauses = [set() for _ in range(turn)]
                clauses[-1] = {"terreur"}
                result = GAME.play(seed, turn, chosen=choices, pool=["yldra", "corvin"], turn_clauses=clauses)
                entry = result["journal_testeur"][-1]
                self.assertEqual(entry["ecart"], 0)
                self.assertEqual(entry["etat_resolution"], "adhesion")
                return
        self.fail("situation messe-sans-temoin introuvable")

    def test_omitted_fact_is_only_in_tester_log(self):
        result = GAME.play(20260926, 8)
        omissions = [entry for entry in result["journal_testeur"] if entry["fait_omis"]]
        self.assertTrue(omissions)
        for tester_entry in omissions:
            player_entry = result["journal"][tester_entry["tour"] - 1]
            self.assertEqual(player_entry["faits"], [])
            self.assertNotIn("etat_avant", player_entry)
            self.assertNotIn("etat_apres", player_entry)
            self.assertTrue(tester_entry["faits"])

    def test_existing_json_command_still_runs(self):
        command = [sys.executable, str(ROOT / "outils/joue-partie.py"), "--seed", "42", "--json"]
        first = subprocess.check_output(command, cwd=ROOT)
        second = subprocess.check_output(command, cwd=ROOT)
        self.assertEqual(first, second)
        self.assertIn("journal_testeur", json.loads(first))


if __name__ == "__main__":
    unittest.main()
