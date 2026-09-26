#!/usr/bin/env python3
"""Vertical slice jouable : conseil, choix, résolution et rapports.

Le moteur volontairement petit ne connaît que le contrat du catalogue. Il est
fait pour être remplacé par une interface sans déplacer les règles.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRAITS = ["zele", "cruaute", "initiative", "discretion", "franchise"]
LEVELS = ["nul", "faible", "moyen", "fort", "total"]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def score(option: dict[str, Any], figure: dict[str, Any], labels: dict[str, Any]) -> float:
    weights = labels["etiquettes"]
    x = {trait: (figure["traits"][trait] - 50) / 50 for trait in TRAITS}
    total = sum(weights[tag]["poids"][trait] * x[trait] for tag in option["etiquettes"] for trait in TRAITS)
    return labels["score"]["centre"] + labels["score"]["amplitude"] / (labels["score"]["poids_max_par_etiquette"] * len(option["etiquettes"])) * total


def traits_for(figure: dict[str, Any], rng: random.Random) -> dict[str, int]:
    return {trait: rng.randint(*figure["enveloppes"][trait]) for trait in TRAITS}


def choose(options: list[dict[str, Any]], figure: dict[str, Any], labels: dict[str, Any], noise: dict[str, Any], rng: random.Random, clauses: set[str]) -> tuple[dict[str, Any], dict[str, float]]:
    scores = {option["id"]: score(option, figure, labels) for option in options}
    best = max(scores.values())
    survivors = [option for option in options if best - scores[option["id"]] <= noise["elagage"]["ecart"] and not (clauses & set(option.get("interdit_par", [])))]
    if not survivors:
        survivors = options
    noisy = {option["id"]: scores[option["id"]] + rng.uniform(-noise["bruit"]["amplitude"], noise["bruit"]["amplitude"]) for option in survivors}
    return max(survivors, key=lambda option: noisy[option["id"]]), scores


def level_change(current: str, sense: str, magnitude: str, settings: dict[str, Any]) -> str:
    values = settings["defaut"]["valeurs"]
    points = LEVELS.index(current) * 20
    delta = values[magnitude]
    points += delta if sense == "hausse" else -delta
    return LEVELS[min(4, max(0, int(points // 20)))]


def make_world() -> dict[str, dict[str, Any]]:
    return {
        "lieu": {"dans_le_domaine": True, "population": "bourg", "frontaliere": True, "anomalie_observable": True, "securite": "faible", "loyaute_envers_nation": "moyen", "opinion_envers_joueur": "moyen", "richesse": "fort"},
        "nation": {"en_guerre": True, "succession": "contestee", "opinion_envers_joueur": "moyen", "securite": "moyen"},
        "notable": {"endette": True, "ambitieux": True, "charge": "negoce", "opinion_envers_joueur": "moyen", "influence": "fort"},
        "faction": {"nature": "culte", "ferveur": "fort", "opinion_envers_joueur": "moyen"},
    }


def report(figure: dict[str, Any], option: dict[str, Any], rng: random.Random) -> str:
    franchise = figure["traits"]["franchise"]
    lines = [f"{figure['nom']} conseille : {option['nom']}. ", option["prose"]]
    if franchise < 40 and rng.random() > franchise / 100:
        lines.append("Une part du rapport reste soigneusement tue.")
    else:
        lines.append("Le rapport ne signale aucune réserve supplémentaire.")
    return " ".join(lines)


def play(seed: int, turns: int, chosen: list[str] | None = None, clauses: set[str] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    settings = load(ROOT / "contenu/reglages/ampleurs.json")
    labels = load(ROOT / "contenu/reglages/etiquettes.json")
    noise = load(ROOT / "contenu/reglages/bruit.json")
    figures = [load(path) for path in sorted((ROOT / "contenu/figures").glob("*.json"))]
    for figure in figures:
        figure["traits"] = traits_for(figure, rng)
    situations = [load(path) for path in sorted((ROOT / "contenu/catalogue").glob("*.json")) if path.name != "exemple-canonique.json"]
    rng.shuffle(situations)
    rng.shuffle(figures)
    world = make_world()
    log: list[dict[str, Any]] = []
    for turn, situation in enumerate(situations[:turns], 1):
        figure = figures[(turn - 1) % len(figures)]
        # Le générateur fournit un contexte admissible pour chaque situation.
        # Les conditions restent donc visibles dans le journal sans introduire
        # un système de génération supplémentaire dans cette tranche.
        for condition in situation["conditions"]:
            role, field = condition["chemin"].split(".", 1)
            value = condition["valeur"]
            if condition["operateur"] in {"==", "!="}:
                world.setdefault(role, {})[field] = value if condition["operateur"] == "==" else world[role].get(field)
            elif field in {"population", "securite", "richesse"}:
                world.setdefault(role, {})[field] = "bourg" if field == "population" else "moyen"
        options = situation["options"]
        auto, scores = choose(options, figure, labels, noise, rng, clauses or set())
        option = next((item for item in options if chosen and item["id"] == chosen[turn - 1]), auto) if chosen and turn <= len(chosen) else auto
        before = json.loads(json.dumps(world, ensure_ascii=False))
        facts = []
        for effect in option["effets"]:
            role, field = effect["cible"].split(".", 1)
            old = world[role].get(field, "moyen")
            if isinstance(old, str) and old in LEVELS:
                world[role][field] = level_change(old, effect["sens"], effect["ampleur"], settings)
            facts.append(f"{effect['cible']} : {old} → {world[role][field]}")
        log.append({"tour": turn, "situation": situation["id"], "serviteur": figure["id"], "conseil": [{"id": o["id"], "score": round(scores[o["id"]], 2)} for o in options], "action": option["id"], "faits": facts, "rapport": report(figure, option, rng), "etat_avant": before, "etat_apres": world})
    return {"seed": seed, "tours": len(log), "figures_du_vivier": sorted(figure["id"] for figure in figures), "journal": log, "etat_final": world}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument("--tours", type=int, default=8)
    parser.add_argument("--clause", action="append", default=[], help="étiquette interdite par l'ordre (répétable)")
    parser.add_argument("--json", action="store_true", help="émet le journal machine lisible")
    args = parser.parse_args()
    result = play(args.seed, args.tours, clauses=set(args.clause))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Partie seed={args.seed} — {result['tours']} tours")
        for item in result["journal"]:
            print(f"\nTour {item['tour']} · {item['situation']} · conseil de {item['serviteur']}")
            print("  " + ", ".join(f"{c['id']} ({c['score']})" for c in item["conseil"]))
            print(f"  Action : {item['action']}\n  {item['rapport']}\n  Faits : {'; '.join(item['faits'])}")
        print("\nPartie terminée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
