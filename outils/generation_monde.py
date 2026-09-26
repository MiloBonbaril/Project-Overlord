#!/usr/bin/env python3
"""Générateur déterministe des trois couches du monde de la Tranche 4."""
from __future__ import annotations

import hashlib
import random
from collections import deque
from typing import Any

VERSION = 1
LEVELS = ("nul", "faible", "moyen", "fort", "total")
RESOURCES = ("vivres", "bois", "metal", "mana", "relique")
RARE = {"mana", "relique"}
ARCHETYPES = (
    {"id": "frontiere", "nations": 3, "locations": 8},
    {"id": "archipel", "nations": 3, "locations": 8},
    {"id": "cour_des_cendres", "nations": 3, "locations": 6},
    {"id": "terres_riches", "nations": 3, "locations": 10},
    {"id": "silence", "nations": 3, "locations": 7},
)


def _rng(seed: int, layer: str) -> random.Random:
    digest = hashlib.sha256(f"world-v{VERSION}:{seed}:{layer}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _level(value: int) -> str:
    return LEVELS[min(4, max(0, value // 20))]


def _distance(world: dict[str, Any], start: str, end: str) -> int:
    graph: dict[str, list[tuple[str, int]]] = {place["id"]: [] for place in world["locations"]}
    for edge in world["edges"]:
        graph[edge["a"]].append((edge["b"], edge["ticks"]))
        graph[edge["b"]].append((edge["a"], edge["ticks"]))
    queue = [(0, start)]
    best = {start: 0}
    while queue:
        queue.sort(reverse=True)
        distance, node = queue.pop()
        if node == end:
            return distance
        for neighbour, ticks in graph[node]:
            candidate = distance + ticks
            if candidate < best.get(neighbour, 10**9):
                best[neighbour] = candidate
                queue.append((candidate, neighbour))
    raise ValueError("graphe déconnecté")


def _skeleton(seed: int, archetype: dict[str, Any]) -> dict[str, Any]:
    rng = _rng(seed, "squelette")
    location_count, nation_count = archetype["locations"], archetype["nations"]
    # Blocs contigus non vides : une chaîne donne exactement deux lieux
    # frontaliers par changement de nation (4 pour trois nations).
    base, remainder = divmod(location_count, nation_count)
    sizes = [base + (index < remainder) for index in range(nation_count)]
    assignments = [f"nation_{nation + 1}" for nation, size in enumerate(sizes) for _ in range(size)]
    locations = []
    for index, nation in enumerate(assignments):
        locations.append({
            "id": f"lieu_{index + 1}", "nation": nation,
            "resources": [], "fortified": rng.random() < .35,
            "loyalty": _level(rng.randint(20, 100)),
            "opinion_player": _level(rng.randint(0, 100)),
            "security": _level(rng.randint(0, 100)),
            "wealth": _level(rng.randint(20, 100)),
        })
    edges = []
    for index in range(location_count - 1):
        crossing = assignments[index] != assignments[index + 1]
        low, high = ((12, 12) if archetype["id"] in {"frontiere", "terres_riches"} and crossing else (4, 4))
        edges.append({"a": f"lieu_{index + 1}", "b": f"lieu_{index + 2}", "ticks": rng.randint(low, high)})

    if archetype["id"] == "terres_riches":
        for place in locations:
            count = rng.randint(1, 3)
            place["resources"] = rng.sample(RESOURCES, count)
        # Au moins trois rares, réparties sans dépasser deux par nation.
        for nation in {place["nation"] for place in locations}:
            seen = 0
            for place in (item for item in locations if item["nation"] == nation):
                kept = []
                for resource in place["resources"]:
                    if resource in RARE:
                        seen += 1
                        if seen > 2:
                            # Consider the complete location, including resources
                            # not visited yet, to preserve local uniqueness.
                            occupied = set(place["resources"]) | set(kept)
                            resource = next(item for item in RESOURCES[:3] if item not in occupied)
                    kept.append(resource)
                place["resources"] = kept
        rare_count = sum(resource in RARE for place in locations for resource in place["resources"])
        nation_rare = {nation: sum(resource in RARE for place in locations if place["nation"] == nation for resource in place["resources"]) for nation in {place["nation"] for place in locations}}
        for place in locations:
            if rare_count >= 3:
                break
            if nation_rare[place["nation"]] < 2 and not any(resource in RARE for resource in place["resources"]):
                if len(place["resources"]) == 3:
                    place["resources"].pop()
                place["resources"].append(("mana", "relique")[rare_count % 2])
                rare_count += 1
                nation_rare[place["nation"]] += 1
    else:
        target = rng.randint(max(location_count, 6), min(12, location_count * 2))
        for place in locations:
            place["resources"] = [rng.choice(RESOURCES[:3])]
        while sum(len(place["resources"]) for place in locations) < target:
            place = rng.choice(locations)
            available = [resource for resource in RESOURCES if resource not in place["resources"]]
            if available and len(place["resources"]) < 3:
                place["resources"].append(rng.choice(available))

    rare_target = {"frontiere": 2, "archipel": 3, "cour_des_cendres": 1, "silence": rng.randint(0, 1)}.get(archetype["id"])
    if rare_target is not None:
        for place in locations:
            place["resources"] = [resource for resource in place["resources"] if resource not in RARE]
            if not place["resources"]:
                place["resources"] = [rng.choice(RESOURCES[:3])]
        frontier_ids = {node for edge in edges for node in (edge["a"], edge["b"]) if assignments[int(edge["a"].split("_")[1]) - 1] != assignments[int(edge["b"].split("_")[1]) - 1]}
        candidates = [place for place in locations if place["id"] in frontier_ids] if archetype["id"] == "frontiere" else locations[:]
        rng.shuffle(candidates)
        for index, place in enumerate(candidates[:rare_target]):
            if len(place["resources"]) == 3:
                place["resources"].pop()
            place["resources"].append(("mana", "relique")[index % 2])

    return {
        "locations": locations, "edges": edges,
        "nations": [{"id": f"nation_{index + 1}"} for index in range(nation_count)],
        "dungeon": {"nearest": "lieu_1", "ticks": rng.randint(4, 12)},
    }


def _politics(seed: int, world: dict[str, Any], archetype: str) -> None:
    rng = _rng(seed, "politique")
    successions = ["stable"] * len(world["nations"])
    if archetype == "cour_des_cendres":
        successions[:2] = ["contestee", "vacante"]
    powers = rng.sample(range(15, 96, 10), len(world["nations"]))
    if max(powers) - min(powers) < 10:
        powers[-1] = min(100, powers[-1] + 10)
    for index, nation in enumerate(world["nations"]):
        security = rng.randint(20, 100)
        nation.update({
            "power": powers[index], "wealth": "fort" if archetype == "terres_riches" else _level(rng.randint(0, 100)),
            "security": _level(security), "fervour": _level(rng.randint(0, 100)),
            "opinion_player": _level(rng.randint(0, 100)), "succession": successions[index],
        })
        owned = [place for place in world["locations"] if place["nation"] == nation["id"]]
        if security < 40 and not any(place["fortified"] for place in owned):
            owned[0]["fortified"] = True
    if archetype == "cour_des_cendres":
        world["nations"][0]["opinion_player"] = "faible"

    relations = []
    for left in range(len(world["nations"])):
        for right in range(left + 1, len(world["nations"])):
            states = ["alliee", "cordiale", "neutre", "tiede", "froide", "declaree"]
            if archetype in {"archipel", "terres_riches"}:
                states.remove("declaree")
            hostility = "neutre" if archetype == "silence" else rng.choice(states)
            if archetype == "cour_des_cendres" and not relations:
                hostility = "alliee"
            if archetype == "frontiere" and left == 0 and right == 1:
                hostility = "froide"
            tension = rng.randint(60, 100) if hostility == "declaree" else rng.randint(0, 20) if hostility == "alliee" else rng.randint(0, 100)
            relations.append({"a": f"nation_{left + 1}", "b": f"nation_{right + 1}", "hostility": hostility, "tension": tension, "alliance": hostility in {"alliee", "cordiale"}})
    world["relations"] = relations


def _secrets(seed: int, index: int, world: dict[str, Any], archetype: str) -> None:
    rng = _rng(seed, "secret")
    without_pair = index % 20 in {0, 1, 2}
    pair_count = 0 if without_pair else rng.choices((1, 2, 3), weights=(70, 25, 5))[0]
    if archetype == "silence":
        pair_count = min(pair_count, 1)
    relation = {frozenset((item["a"], item["b"])): item for item in world["relations"]}
    candidates = []
    for left, first in enumerate(world["locations"]):
        for second in world["locations"][left + 1:]:
            distance = _distance(world, first["id"], second["id"])
            if first["nation"] != second["nation"] and 5 <= distance <= 32:
                candidates.append((first, second, distance))
    rng.shuffle(candidates)
    pairs, used = [], set()
    hostility_order = ("alliee", "cordiale", "neutre", "tiede", "froide", "declaree")
    for first, second, distance in candidates:
        if len(pairs) == pair_count:
            break
        if first["id"] in used or second["id"] in used:
            continue
        political = relation[frozenset((first["nation"], second["nation"]))]
        intentions = []
        if hostility_order.index(political["hostility"]) <= hostility_order.index("tiede"):
            intentions.append("proteger")
        nations = [next(n for n in world["nations"] if n["id"] == place["nation"]) for place in (first, second)]
        if any(nation["succession"] in {"contestee", "vacante"} for nation in nations):
            intentions.append("renverser")
        if any(LEVELS.index(place["wealth"]) >= LEVELS.index("moyen") for place in (first, second)):
            intentions.append("exploiter")
        if any(LEVELS.index(place["security"]) <= LEVELS.index("faible") for place in (first, second)):
            intentions.append("fuir")
        if intentions:
            pairs.append({"locations": [first["id"], second["id"]], "distance": distance, "intention": rng.choice(intentions)})
            used.update((first["id"], second["id"]))
    if len(pairs) != pair_count:
        # Les blocs garantissent normalement assez de candidats ; une erreur
        # explicite conserve l'invariant au lieu de publier un monde partiel.
        raise ValueError("impossible de distribuer les paires demandées")
    anomaly_places = rng.sample(world["locations"], rng.randint(0, 2))
    anomalies = [{"location": place["id"], "observable": rng.choice((True, False))} for place in anomaly_places]
    if archetype == "silence" and not any(not item["observable"] for item in anomalies):
        anomalies = [{"location": rng.choice(world["locations"])["id"], "observable": False}]
    world["secrets"] = {"pairs": pairs, "anomalies": anomalies, "without_pair": without_pair}


def generate_world(seed: int, index: int = 0) -> dict[str, Any]:
    archetype = ARCHETYPES[_rng(seed, "archetype").randrange(len(ARCHETYPES))]
    world = _skeleton(seed, archetype)
    world.update({"version": VERSION, "seed": seed, "index": index, "archetype": archetype["id"]})
    _politics(seed, world, archetype["id"])
    _secrets(seed, index, world, archetype["id"])
    validate_world(world)
    return world


def player_world(world: dict[str, Any]) -> dict[str, Any]:
    """Projection publique : les clés secrètes sont absentes, jamais nulles."""
    return {
        "version": world["version"], "seed": world["seed"],
        "nations": [{key: value for key, value in nation.items() if key not in {"power"}} for nation in world["nations"]],
        "locations": [{key: value for key, value in place.items() if key not in {"loyalty"}} for place in world["locations"]],
        "observed_anomalies": [item["location"] for item in world["secrets"]["anomalies"] if item["observable"]],
    }


def validate_world(world: dict[str, Any]) -> None:
    archetype = next(item for item in ARCHETYPES if item["id"] == world["archetype"])
    if len(world["locations"]) != archetype["locations"] or len(world["nations"]) != archetype["nations"]:
        raise ValueError("cardinalités d'archétype invalides")
    ids = {place["id"] for place in world["locations"]}
    reached, queue = set(), deque([next(iter(ids))])
    while queue:
        node = queue.popleft()
        if node in reached:
            continue
        reached.add(node)
        queue.extend(edge["b"] if edge["a"] == node else edge["a"] for edge in world["edges"] if node in {edge["a"], edge["b"]})
    if reached != ids:
        raise ValueError("graphe déconnecté")
    degrees = {node: sum(node in {edge["a"], edge["b"]} for edge in world["edges"]) for node in ids}
    if not all(1 <= degree <= 3 for degree in degrees.values()) or not all(4 <= edge["ticks"] <= 32 for edge in world["edges"]):
        raise ValueError("graphe hors bornes")
    nation_by_place = {place["id"]: place["nation"] for place in world["locations"]}
    frontier = {node for edge in world["edges"] for node in (edge["a"], edge["b"]) if nation_by_place[edge["a"]] != nation_by_place[edge["b"]]}
    if len(frontier) != 4:
        raise ValueError("nombre de lieux frontaliers invalide")
    for place in world["locations"]:
        if not 1 <= len(place["resources"]) <= 3 or len(place["resources"]) != len(set(place["resources"])):
            raise ValueError("ressources invalides")
    rare_places = [place for place in world["locations"] if any(resource in RARE for resource in place["resources"])]
    if archetype["id"] == "frontiere" and (len(rare_places) != 2 or not all(place["id"] in frontier for place in rare_places)):
        raise ValueError("ressources rares de frontière invalides")
    if archetype["id"] == "terres_riches" and sum(resource in RARE for place in world["locations"] for resource in place["resources"]) < 3:
        raise ValueError("terres riches sans assez de ressources rares")
    for nation in world["nations"]:
        rare_count = sum(resource in RARE for place in world["locations"] if place["nation"] == nation["id"] for resource in place["resources"])
        if rare_count > 2:
            raise ValueError("trop de ressources rares dans une nation")
    powers = [nation["power"] for nation in world["nations"]]
    if len(powers) != len(set(powers)) or max(powers) - min(powers) < 10:
        raise ValueError("rapports de force invalides")
    if archetype["id"] == "cour_des_cendres":
        if sum(nation["succession"] in {"contestee", "vacante"} for nation in world["nations"]) < 2:
            raise ValueError("successions de la cour invalides")
        if not any(nation["opinion_player"] in {"nul", "faible"} for nation in world["nations"]):
            raise ValueError("opinion de la cour invalide")
    if world["secrets"]["without_pair"] != (world["index"] % 20 in {0, 1, 2}):
        raise ValueError("quota sans pair invalide")
    if world["secrets"]["without_pair"] != (not world["secrets"]["pairs"]):
        raise ValueError("présence de paire incohérente")
    for relation in world["relations"]:
        if relation["alliance"] and relation["hostility"] == "declaree":
            raise ValueError("alliance en guerre")
        if relation["hostility"] == "declaree" and relation["tension"] < 60:
            raise ValueError("tension de guerre invalide")
        if relation["hostility"] == "alliee" and relation["tension"] > 20:
            raise ValueError("tension alliée invalide")
    if archetype["id"] == "frontiere" and not any(item["hostility"] in {"froide", "declaree"} for item in world["relations"]):
        raise ValueError("frontière sans hostilité")
    if archetype["id"] in {"archipel", "terres_riches"} and any(item["hostility"] == "declaree" for item in world["relations"]):
        raise ValueError("guerre déclarée interdite")
    if archetype["id"] == "cour_des_cendres" and not any(item["alliance"] for item in world["relations"]):
        raise ValueError("cour sans alliance")
    if archetype["id"] == "silence":
        if any(item["alliance"] for item in world["relations"]):
            raise ValueError("alliance interdite dans Silence")
        if not any(not item["observable"] for item in world["secrets"]["anomalies"]):
            raise ValueError("anomalie cachée absente")
