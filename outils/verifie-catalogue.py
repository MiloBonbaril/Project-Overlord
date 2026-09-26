#!/usr/bin/env python3
"""Linter normatif du catalogue de situations (règles R0 à R12)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    rule: str
    where: str
    what: str
    action: str

    def render(self) -> str:
        return f"ERREUR {self.rule} — {self.where}\nQuoi : {self.what}\nAction : {self.action}"


class LoadFailure(Exception):
    pass


class Linter:
    REQUIRED = {"id": str, "nom": str, "roles": dict, "conditions": list, "options": list}
    CONDITION_KEYS = {"chemin", "operateur", "valeur"}
    EFFECT_KEYS = {"cible", "sens", "ampleur"}
    OPTION_REQUIRED = {"id": str, "nom": str, "etiquettes": list, "effets": list, "prose": str}
    ORDERED_OPERATORS = {"==", "!=", "<", "<=", ">", ">="}
    EQUALITY_OPERATORS = {"==", "!="}

    def __init__(self, settings: dict[str, Any]):
        self.world = settings["monde"]
        self.tags = set(settings["etiquettes"]["etiquettes"])
        self.magnitudes = set(settings["ampleurs"]["ampleurs"])
        self.prose = settings["prose"]
        self.errors: list[Diagnostic] = []

    def error(self, rule: str, where: str, what: str, action: str) -> None:
        self.errors.append(Diagnostic(rule, where, what, action))

    def validate(self, documents: list[tuple[Path, Any]]) -> list[Diagnostic]:
        seen: dict[str, Path] = {}
        for path, data in documents:
            where = path.as_posix()
            if not isinstance(data, dict):
                self.error("R1", where, "la racine JSON n'est pas un objet", "remplacez la racine par un objet situation")
                continue
            sid = data.get("id")
            if not isinstance(sid, str) or not sid.strip():
                self.error("R2", where, "l'identifiant est absent ou illisible", "ajoutez un champ id texte non vide")
            elif sid in seen:
                self.error("R2", where, f"l'identifiant « {sid} » existe déjà dans {seen[sid].as_posix()}", "donnez un identifiant unique à cette situation")
            else:
                seen[sid] = path
            if not isinstance(data.get("nom"), str) or not data.get("nom", "").strip():
                self.error("R2", where, "le nom lisible est absent ou vide", "ajoutez un champ nom destiné aux auteurs")
            if not self._shape(where, data):
                continue
            roles = data["roles"]
            self._roles(where, roles)
            for i, condition in enumerate(data["conditions"]):
                self._condition(f"{where}:conditions[{i}]", condition, roles)
            option_ids: set[str] = set()
            for i, option in enumerate(data["options"]):
                ow = f"{where}:options[{i}]"
                if not self._option_shape(ow, option):
                    continue
                if option["id"] in option_ids:
                    self.error("R3", ow, f"l'identifiant d'option « {option['id']} » est dupliqué", "donnez un id unique dans la situation")
                option_ids.add(option["id"])
                self._option(ow, option, roles)
        return self.errors

    def _shape(self, where: str, data: dict[str, Any]) -> bool:
        ok = True
        for key, expected in self.REQUIRED.items():
            if key not in data:
                self.error("R3", where, f"le champ obligatoire « {key} » manque", f"ajoutez « {key} » avec le type {expected.__name__}")
                ok = False
            elif not isinstance(data[key], expected):
                self.error("R3", f"{where}:{key}", f"type {type(data[key]).__name__}, attendu {expected.__name__}", "corrigez le type du champ")
                ok = False
        if isinstance(data.get("options"), list) and not data["options"]:
            self.error("R3", f"{where}:options", "une situation sans option est impossible à résoudre", "ajoutez au moins une option")
            ok = False
        return ok

    def _option_shape(self, where: str, option: Any) -> bool:
        if not isinstance(option, dict):
            self.error("R3", where, "l'option n'est pas un objet", "remplacez-la par un objet option")
            return False
        ok = True
        for key, expected in self.OPTION_REQUIRED.items():
            if key not in option or not isinstance(option[key], expected):
                self.error("R3", f"{where}:{key}", f"champ obligatoire absent ou de type incorrect (attendu {expected.__name__})", "ajoutez ou corrigez ce champ")
                ok = False
        return ok

    def _roles(self, where: str, roles: dict[str, Any]) -> None:
        for role, kind in roles.items():
            if not isinstance(role, str) or not role or kind not in self.world["types"]:
                self.error("R8", f"{where}:roles.{role}", f"le rôle cible le type inconnu « {kind} »", f"utilisez un type connu : {', '.join(sorted(self.world['types']))}")
            elif not self.world["types"][kind].get("liable"):
                self.error("R8", f"{where}:roles.{role}", f"le type « {kind} » ne peut pas être lié à un rôle", "retirez ce rôle ; utilisez un rôle implicite si le schéma le prévoit")

    def _resolve(self, raw: str, roles: dict[str, Any], where: str) -> tuple[str, str] | None:
        if not isinstance(raw, str) or "." not in raw:
            self.error("R5", where, f"le chemin « {raw} » n'a pas la forme rôle.champ", "écrivez un chemin résolu, par exemple lieu.population")
            return None
        role, field = raw.split(".", 1)
        implicit = set(self.world.get("roles_implicites", []))
        kind = role if role in implicit else roles.get(role)
        if kind is None:
            self.error("R8", where, f"le rôle « {role} » n'est pas déclaré", "déclarez ce rôle dans roles ou utilisez un rôle implicite")
            return None
        refusal = self.world.get("refus", {})
        refused_key = next((key for key in (f"{kind}.{field}", f"*.{field}", role) if key in refusal), None)
        if refused_key:
            self.error("R10", where, f"le chemin « {raw} » est interdit : {refusal[refused_key]}", "utilisez uniquement une information observable autorisée par monde.json")
            return None
        spec = self.world["types"].get(kind)
        if not spec or field not in spec["champs"]:
            self.error("R5", where, f"le chemin « {raw} » n'existe pas dans monde.json", "corrigez le rôle ou le champ d'après le schéma")
            return None
        return kind, field

    def _condition(self, where: str, condition: Any, roles: dict[str, Any]) -> None:
        if not isinstance(condition, dict) or not self.CONDITION_KEYS <= set(condition):
            self.error("R3", where, "condition incomplète : chemin, operateur et valeur sont obligatoires", "ajoutez les trois champs de condition")
            return
        resolved = self._resolve(condition["chemin"], roles, f"{where}:chemin")
        if not resolved:
            return
        kind, field = resolved
        descriptor = self.world["types"][kind]["champs"][field]
        operator = condition["operateur"]
        allowed = self.EQUALITY_OPERATORS
        values: set[Any] | None = None
        if descriptor.startswith("echelle:"):
            scale = descriptor.split(":", 1)[1]
            values = set(self.world["echelles"][scale]["valeurs"])
            if self.world["echelles"][scale].get("ordonnee"):
                allowed = self.ORDERED_OPERATORS
        elif descriptor.startswith("enum:"):
            values = set(self.world["enums"][descriptor.split(":", 1)[1]])
        if operator not in allowed:
            self.error("R6", f"{where}:operateur", f"« {operator} » est incompatible avec {descriptor}", f"utilisez un opérateur parmi {', '.join(sorted(allowed))}")
        value = condition["valeur"]
        if descriptor == "bool" and type(value) is not bool:
            self.error("R7", f"{where}:valeur", f"« {value} » n'est pas un booléen", "utilisez true ou false")
        elif values is not None and value not in values:
            self.error("R7", f"{where}:valeur", f"« {value} » n'appartient pas à {descriptor}", f"utilisez une valeur connue : {', '.join(map(str, sorted(values)))}")
        elif descriptor.startswith("ref:"):
            target = descriptor.split(":", 1)[1]
            if value not in roles and value not in self.world.get("roles_implicites", []):
                self.error("R8", f"{where}:valeur", f"la référence de rôle « {value} » n'est pas résolue", f"déclarez un rôle de type {target}")
            elif value in roles and roles[value] != target:
                self.error("R8", f"{where}:valeur", f"le rôle « {value} » est de type {roles[value]}, attendu {target}", f"référencez un rôle de type {target}")

    def _option(self, where: str, option: dict[str, Any], roles: dict[str, Any]) -> None:
        tags = option["etiquettes"]
        if any(not isinstance(tag, str) or not tag for tag in tags):
            self.error("R4", f"{where}:etiquettes", "une étiquette est vide ou n'est pas du texte", "retirez-la ou nommez une étiquette connue")
        duplicate = next((tag for tag in tags if tags.count(tag) > 1), None)
        if duplicate:
            self.error("R4", f"{where}:etiquettes", f"l'étiquette « {duplicate} » est dupliquée", "ne gardez qu'une occurrence")
        unknown = sorted({tag for tag in tags if tag not in self.tags})
        if unknown:
            self.error("R4", f"{where}:etiquettes", f"étiquettes inconnues : {', '.join(unknown)}", "utilisez le vocabulaire fermé de etiquettes.json")
        forbidden = option.get("interdit_par", [])
        if not isinstance(forbidden, list) or any(tag not in tags for tag in forbidden):
            self.error("R11", f"{where}:interdit_par", "une clause interdite ne correspond pas aux étiquettes de l'option", "ne citez ici que des étiquettes présentes sur cette option")
        for i, effect in enumerate(option["effets"]):
            self._effect(f"{where}:effets[{i}]", effect, roles)
        self._check_prose(f"{where}:prose", option["prose"])

    def _effect(self, where: str, effect: Any, roles: dict[str, Any]) -> None:
        if not isinstance(effect, dict) or not self.EFFECT_KEYS <= set(effect):
            self.error("R3", where, "effet incomplet : cible, sens et ampleur sont obligatoires", "ajoutez les trois champs d'effet")
            return
        resolved = self._resolve(effect["cible"], roles, f"{where}:cible")
        if not resolved:
            return
        kind, field = resolved
        descriptor = self.world["types"][kind]["champs"][field]
        if field in self.world["types"][kind].get("lecture_seule", []):
            self.error("R10", f"{where}:cible", f"« {effect['cible']} » est en lecture seule", "choisissez une grandeur inscriptible dérivée de monde.json")
        elif not descriptor.startswith("echelle:"):
            self.error("R9", f"{where}:cible", f"« {effect['cible']} » n'est pas une grandeur inscriptible", "ciblez un champ echelle non placé en lecture_seule")
        if effect["sens"] not in {"hausse", "baisse"}:
            self.error("R9", f"{where}:sens", f"sens inconnu « {effect['sens']} »", "utilisez hausse ou baisse")
        if effect["ampleur"] not in self.magnitudes:
            self.error("R9", f"{where}:ampleur", f"ampleur inconnue « {effect['ampleur']} »", f"utilisez : {', '.join(sorted(self.magnitudes))}")

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn").replace("’", "'").replace("‑", "-")

    def _check_prose(self, where: str, text: str) -> None:
        normalized = self._normalize(text)
        tokens = re.findall(r"\d+(?:[.,]\d+)?|[a-z]+(?:-[a-z]+)*", normalized)
        numbers = set(self.prose["nombres_en_lettres"]["unites"] + self.prose["nombres_en_lettres"]["dizaines"] + self.prose["nombres_en_lettres"]["multiplicateurs"])
        window = self.prose["fenetre_unite"]
        for group, spec in self.prose["unites_simulees"].items():
            units = {self._normalize(word) for word in spec["mots"]}
            for i, token in enumerate(tokens):
                if token in units and any(t.isdigit() or re.fullmatch(r"\d+(?:[.,]\d+)?", t) or t in numbers for t in tokens[max(0, i-window):i]):
                    self.error("R12", where, f"quantité simulée interdite ({group}) : {spec['message']}", "remplacez la quantité précise par une formulation vague prévue dans prose.json")
                    return


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LoadFailure(f"{path}: {exc}") from exc


def load_settings(root: Path) -> dict[str, Any]:
    return {name: load_json(root / f"{name}.json") for name in ("monde", "ampleurs", "etiquettes", "prose")}


def run(catalogue: Path, settings_root: Path) -> int:
    try:
        settings = load_settings(settings_root)
        if not catalogue.is_dir():
            raise LoadFailure(f"{catalogue}: le catalogue n'est pas un dossier lisible")
        files = sorted(catalogue.glob("*.json"))
        if not files:
            raise LoadFailure(f"{catalogue}: aucun fichier JSON")
        documents = [(path, load_json(path)) for path in files]
    except (LoadFailure, KeyError, TypeError) as exc:
        print(Diagnostic("R0", str(catalogue), f"chargement impossible : {exc}", "corrigez l'UTF-8, le JSON, la racine ou les fichiers de réglage").render())
        return 2
    errors = Linter(settings).validate(documents)
    if errors:
        print("\n".join(error.render() for error in errors))
        return 1
    print(f"OK — {len(documents)} situation(s), règles R0 à R12 validées")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("--reglages", type=Path, default=Path("contenu/reglages"))
    args = parser.parse_args()
    return run(args.catalogue, args.reglages)


if __name__ == "__main__":
    sys.exit(main())
