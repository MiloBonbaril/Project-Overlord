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


def choose(options: list[dict[str, Any]], figure: dict[str, Any], labels: dict[str, Any], noise: dict[str, Any], rng: random.Random, clauses: set[str]) -> tuple[dict[str, Any], dict[str, float], list[dict[str, Any]]]:
    scores = {option["id"]: score(option, figure, labels) for option in options}
    admissible = [option for option in options if not (clauses & set(option.get("interdit_par", [])))]
    if not admissible:
        raise ValueError("aucune option admissible avec les clauses actives")
    best = max(scores[option["id"]] for option in admissible)
    survivors = [option for option in admissible if best - scores[option["id"]] <= noise["elagage"]["ecart"]]
    noisy = {option["id"]: scores[option["id"]] + rng.uniform(-noise["bruit"]["amplitude"], noise["bruit"]["amplitude"]) for option in survivors}
    return max(survivors, key=lambda option: noisy[option["id"]]), scores, admissible


def resolution_for_gap(gap: float, resolution: dict[str, Any]) -> tuple[str, str, int]:
    thresholds = resolution["seuils"]
    if gap <= thresholds["adhesion_max"]:
        state = "adhesion"
    elif gap <= thresholds["reserve_max"]:
        state = "reserve"
    else:
        state = "resistance"
    setting = resolution["etats"][state]
    return state, setting["libelle"], setting["reduction"]


def reduced_magnitude(magnitude: str, reduction: int, settings: dict[str, Any]) -> str:
    magnitudes = ["nul", *settings["ampleurs"]]
    return magnitudes[max(0, magnitudes.index(magnitude) - reduction)]


def level_change(current: str, sense: str, magnitude: str, settings: dict[str, Any]) -> str:
    if magnitude == "nul":
        return current
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


def report(figure: dict[str, Any], option: dict[str, Any], rng: random.Random) -> tuple[str, bool]:
    franchise = figure["traits"]["franchise"]
    lines = [f"{figure['nom']} conseille : {option['nom']}. ", option["prose"]]
    omitted = franchise < 40 and rng.random() > franchise / 100
    if omitted:
        lines.append("Une part du rapport reste soigneusement tue.")
    else:
        lines.append("Le rapport ne signale aucune réserve supplémentaire.")
    return " ".join(lines), omitted


def play(seed: int, turns: int, chosen: list[str] | None = None,
         clauses: set[str] | None = None, pool: list[str] | None = None,
         turn_clauses: list[set[str]] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    settings = load(ROOT / "contenu/reglages/ampleurs.json")
    labels = load(ROOT / "contenu/reglages/etiquettes.json")
    noise = load(ROOT / "contenu/reglages/bruit.json")
    resolution = load(ROOT / "contenu/reglages/resolution-serviteur.json")
    figures = [load(path) for path in sorted((ROOT / "contenu/figures").glob("*.json"))]
    known_figures = {figure["id"] for figure in figures}
    if pool:
        unknown = set(pool) - known_figures
        if unknown:
            raise ValueError(f"figure(s) inconnue(s) : {', '.join(sorted(unknown))}")
        figures = [figure for figure in figures if figure["id"] in set(pool)]
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
        active_clauses = set(clauses or set())
        if turn_clauses and turn <= len(turn_clauses):
            active_clauses.update(turn_clauses[turn - 1])
        auto, scores, admissible = choose(options, figure, labels, noise, rng, active_clauses)
        if chosen and turn <= len(chosen):
            option = next((item for item in options if item["id"] == chosen[turn - 1]), None)
            if option is None:
                available = ", ".join(item["id"] for item in options)
                raise ValueError(f"choix '{chosen[turn - 1]}' invalide au tour {turn} (attendus : {available})")
            forbidden_by = active_clauses & set(option.get("interdit_par", []))
            if forbidden_by:
                raise ValueError(f"choix '{option['id']}' interdit au tour {turn} par : {', '.join(sorted(forbidden_by))}")
        else:
            option = auto
        score_max = max(scores[item["id"]] for item in admissible)
        chosen_score = scores[option["id"]]
        gap = max(0.0, score_max - chosen_score)
        resolution_state, resolution_label, reduction = resolution_for_gap(gap, resolution)
        before = json.loads(json.dumps(world, ensure_ascii=False))
        facts = []
        magnitudes = []
        for effect in option["effets"]:
            role, field = effect["cible"].split(".", 1)
            old = world[role].get(field, "moyen")
            applied_magnitude = reduced_magnitude(effect["ampleur"], reduction, settings)
            if isinstance(old, str) and old in LEVELS:
                world[role][field] = level_change(old, effect["sens"], applied_magnitude, settings)
            magnitudes.append({"cible": effect["cible"], "avant": effect["ampleur"], "apres": applied_magnitude})
            facts.append(f"{effect['cible']} : {old} → {world[role][field]}")
        text, omitted = report(figure, option, rng)
        common = {"tour": turn, "situation": situation["id"], "serviteur": figure["id"], "conseil": [{"id": o["id"], "score": round(scores[o["id"]], 2)} for o in options], "clauses": sorted(active_clauses), "action": option["id"], "rapport": text}
        player_entry = {**common, "resolution_probable": resolution_label, "faits": [] if omitted else facts}
        tester_entry = {**common, "resolution_probable": resolution_label, "faits": facts, "fait_omis": omitted, "score_max": score_max, "score_choisi": chosen_score, "ecart": gap, "etat_resolution": resolution_state, "ampleurs": magnitudes, "etat_avant": before, "etat_apres": json.loads(json.dumps(world, ensure_ascii=False))}
        log.append((player_entry, tester_entry))
    return {"seed": seed, "tours": len(log), "figures_du_vivier": sorted(figure["id"] for figure in figures), "journal": [item[0] for item in log], "journal_testeur": [item[1] for item in log], "etat_final": world}


def interactive_choices(seed: int, turns: int, pool: list[str] | None) -> tuple[list[str], list[set[str]]]:
    """Collecte les ordres avec un aperçu déterministe des situations."""
    preview = play(seed, turns, pool=pool)
    choices: list[str] = []
    clauses: list[set[str]] = []
    for item in preview["journal"]:
        option_ids = [option["id"] for option in item["conseil"]]
        print(f"\nTour {item['tour']} · {item['situation']} · conseil de {item['serviteur']}")
        print("  " + ", ".join(f"{option['id']} ({option['score']})" for option in item["conseil"]))
        while True:
            value = input(f"  Option [{'/'.join(option_ids)}] : ").strip()
            if value in option_ids:
                choices.append(value)
                break
            print("  Option inconnue.")
        raw_clauses = input("  Clause(s), séparées par des virgules (entrée = aucune) : ")
        clauses.append({value.strip() for value in raw_clauses.split(",") if value.strip()})
    return choices, clauses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument("--tours", type=int, default=8)
    parser.add_argument("--clause", action="append", default=[], help="étiquette interdite par l'ordre (répétable)")
    parser.add_argument("--choix", action="append", default=[], help="option choisie au prochain tour (répétable)")
    parser.add_argument("--clause-tour", action="append", default=[], help="clauses du prochain tour, séparées par des virgules (répétable)")
    parser.add_argument("--composition", help="identifiants des figures autorisées, séparés par des virgules")
    parser.add_argument("--json", action="store_true", help="émet le journal machine lisible")
    args = parser.parse_args()
    pool = [value.strip() for value in args.composition.split(",") if value.strip()] if args.composition else None
    turn_clauses = [{value.strip() for value in raw.split(",") if value.strip()} for raw in args.clause_tour]
    choices = args.choix
    if not args.json and not choices:
        choices, turn_clauses = interactive_choices(args.seed, args.tours, pool)
    try:
        result = play(args.seed, args.tours, choices, set(args.clause), pool, turn_clauses)
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Partie seed={args.seed} — {result['tours']} tours")
        for item in result["journal"]:
            print(f"\nTour {item['tour']} · {item['situation']} · conseil de {item['serviteur']}")
            print("  " + ", ".join(f"{c['id']} ({c['score']})" for c in item["conseil"]))
            facts = "; ".join(item["faits"]) if item["faits"] else "non établis dans le rapport"
            print(f"  Clause(s) : {', '.join(item['clauses']) or 'aucune'}")
            print(f"  Action : {item['action']} — {item['resolution_probable']}\n  {item['rapport']}\n  Faits : {facts}")
        print("\nPartie terminée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
