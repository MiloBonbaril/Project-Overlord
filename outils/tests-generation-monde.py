#!/usr/bin/env python3
"""Régressions des invariants et des deux projections du monde."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generation_monde", ROOT / "outils/generation_monde.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(GEN)


class WorldGenerationTests(unittest.TestCase):
    def test_twenty_worlds_are_valid_distinct_and_reproducible(self):
        worlds = []
        for seed in range(20):
            first = GEN.generate_world(seed, seed)
            second = GEN.generate_world(seed, seed)
            self.assertEqual(first, second)
            GEN.validate_world(first)
            worlds.append(first)
        self.assertEqual(sum(world["secrets"]["without_pair"] for world in worlds), 3)
        canonicals = []
        for world in worlds:
            canonical = copy.deepcopy(world)
            canonical.pop("seed")
            canonical.pop("index")
            canonicals.append(json.dumps(canonical, sort_keys=True))
        self.assertEqual(len(set(canonicals)), 20)

    def test_all_archetypes_are_reached_and_obey_cardinalities(self):
        worlds = {}
        for seed in range(200):
            world = GEN.generate_world(seed, 3 + seed % 17)
            worlds.setdefault(world["archetype"], world)
            if len(worlds) == 5:
                break
        self.assertEqual(set(worlds), {item["id"] for item in GEN.ARCHETYPES})
        rich = worlds["terres_riches"]
        self.assertEqual(len(rich["locations"]), 10)
        self.assertTrue(all(1 <= len(place["resources"]) <= 3 for place in rich["locations"]))
        self.assertTrue(10 <= sum(len(place["resources"]) for place in rich["locations"]) <= 30)

    def test_player_projection_omits_every_secret(self):
        world = GEN.generate_world(19, 19)
        player = GEN.player_world(world)
        encoded = json.dumps(player, sort_keys=True)
        for forbidden in ("archetype", "pairs", "intention", "without_pair", "tension", "alliance", "power"):
            self.assertNotIn(forbidden, encoded)
        self.assertIn("secrets", world)
        self.assertIn("relations", world)

    def test_validator_rejects_broken_connectivity(self):
        world = GEN.generate_world(19, 19)
        world["edges"] = []
        with self.assertRaisesRegex(ValueError, "déconnecté"):
            GEN.validate_world(world)


if __name__ == "__main__":
    unittest.main()
