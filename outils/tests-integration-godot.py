#!/usr/bin/env python3
"""Contrat minimal entre la scène Godot et le moteur déterministe."""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ["python3", str(ROOT / "outils/joue-partie.py"), "--seed", "20260926", "--tours", "8", "--json"]


class GodotIntegrationTest(unittest.TestCase):
    def run_game(self) -> dict:
        return json.loads(subprocess.check_output(COMMAND, cwd=ROOT, text=True))

    def test_same_seed_produces_same_player_log(self) -> None:
        self.assertEqual(self.run_game()["journal"], self.run_game()["journal"])

    def test_scene_references_engine_and_main_scene(self) -> None:
        project = (ROOT / "project.godot").read_text(encoding="utf-8")
        scene = (ROOT / "godot/Main.gd").read_text(encoding="utf-8")
        self.assertIn('run/main_scene="res://godot/Main.tscn"', project)
        self.assertIn('res://outils/joue-partie.py', scene)
        self.assertIn('OS.execute("python3"', scene)

    def test_scene_requires_a_valid_selection_before_resolving(self) -> None:
        scene = (ROOT / "godot/Main.gd").read_text(encoding="utf-8")
        self.assertIn('resolve_button.disabled = true', scene)
        self.assertIn('button.disabled = not forbidden_by.is_empty()', scene)
        self.assertIn('INTERDITE PAR LA CLAUSE', scene)
        self.assertIn('func resolve_selected_order()', scene)


if __name__ == "__main__":
    unittest.main()
