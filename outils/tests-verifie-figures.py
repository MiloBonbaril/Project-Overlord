#!/usr/bin/env python3
"""Jeu de tests de verifie-figures.py.

Une figure fautive par mode de panne, plus le dossier livré qui doit passer.
Un vérificateur qu'on n'a jamais vu refuser quoi que ce soit n'est pas un
vérificateur, c'est une impression.

Usage : python3 outils/tests-verifie-figures.py [racine]
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# (nom du cas, règle visée, mutation, fragment attendu dans la sortie)
CAS = [
    ("champ-manquant", "G1", lambda f: f.pop("titre"), "champs obligatoires absents : titre"),
    ("champ-inconnu", "G1", lambda f: f.update(culture="valdane"), "champs inconnus : culture"),
    ("id-renomme", "G2", lambda f: f.update(id="autre-chose"), "et nom de fichier"),
    ("genre-invalide", "G3", lambda f: f.update(genre="neutre"), "genre « neutre » inconnu"),
    ("registre-fantome", "G4", lambda f: f.update(registre="sarcastique"), "absent de reglages/voix.json"),
    ("aptitude-doublee", "G5", lambda f: f.update(aptitude={"majeure": "combat", "mineure": "combat"}),
     "majeure et mineure identiques"),
    ("bornes-inversees", "G6", lambda f: f["enveloppes"].update(cruaute=[90, 40]), "bornes [90, 40] invalides"),
    ("trait-inconnu", "G6", lambda f: f["enveloppes"].update(loyaute=[0, 100]), "traits attendus"),
    ("sous-plancher", "G7", lambda f: f["enveloppes"].update(
        zele=[85, 100], cruaute=[60, 85], initiative=[65, 90], discretion=[40, 80], franchise=[30, 70]),
     "sous le plancher de doute"),
    ("franchise-exacte", "G8", lambda f: f["enveloppes"].update(franchise=[50, 50]), "franchise exacte"),
    # Registre lisse : la règle porte sur les seuils nus, 20 / 40 / 60 / 80.
    ("franchise-sans-seuil", "G8",
     lambda f: (f.update(registre="laconique"), f["enveloppes"].update(franchise=[41, 56])),
     "ne traverse aucun seuil d'aveu"),
    # Registre marqué : [15, 25] contient le seuil nu 20 et serait légale sans surcharge.
    # Surchargée de 10, elle ne contient plus rien. Les deux autres enveloppes sont
    # élargies pour que le plancher de doute ne soit pas ce qui fait échouer le cas.
    ("franchise-sans-seuil-surcharge", "G8",
     lambda f: (f.update(registre="exalte"),
                f["enveloppes"].update(cruaute=[0, 100], initiative=[0, 100], franchise=[15, 25])),
     "surchargés de 10 par le registre"),
    ("cran-hors-bareme", "G9", lambda f: f["enveloppes"].update(cruaute=[55, 88]), "largeur 33 hors barème"),
    ("nombre-en-presentation", "G10",
     lambda f: f.update(presentation="Elle a tué trois notables et n'en a rapporté aucun."),
     "la présentation cite un nombre"),
    ("sup-fantome", "G11", lambda f: f.update(superieur_par_defaut="inconnu"), "n'est pas une figure"),
]


def prepare(racine, tmp):
    (tmp / "contenu").mkdir(parents=True)
    shutil.copytree(racine / "contenu/reglages", tmp / "contenu/reglages")
    (tmp / "contenu/figures").mkdir()
    return json.loads((racine / "contenu/figures/yldra.json").read_text(encoding="utf-8"))


def lance(outil, cible):
    r = subprocess.run([sys.executable, str(outil), str(cible)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    outil = racine / "outils/verifie-figures.py"
    echecs = []

    # Le dossier livré passe.
    code, sortie = lance(outil, racine)
    if code != 0 or "Aucune erreur bloquante" not in sortie:
        echecs.append("le dossier livré ne passe plus le vérificateur")
    else:
        print("ok    dossier livré : aucune erreur bloquante")

    # Une panne à la fois.
    for nom, regle, mutation, attendu in CAS:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "cas"
            base = prepare(racine, tmp)
            base["id"] = nom
            base["nom"] = nom.capitalize()
            mutation(base)
            (tmp / "contenu/figures" / f"{nom}.json").write_text(
                json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
            code, sortie = lance(outil, tmp)
            attrape = attendu in sortie
            bloquant = regle != "G9"
            ok = attrape and (code == 1 if bloquant else True)
            print(f"{'ok   ' if ok else 'ÉCHEC'} {regle} {nom}")
            if not ok:
                echecs.append(f"{regle} {nom} : attendu « {attendu} », code {code}")

    # Deux figures homonymes.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "cas"
        base = prepare(racine, tmp)
        for suffixe in ("a", "b"):
            f = dict(base, id=f"homonyme-{suffixe}", nom="Homonyme")
            (tmp / "contenu/figures" / f"homonyme-{suffixe}.json").write_text(
                json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")
        code, sortie = lance(outil, tmp)
        ok = "déjà porté par" in sortie and code == 1
        print(f"{'ok   ' if ok else 'ÉCHEC'} G11 homonymes")
        if not ok:
            echecs.append("G11 homonymes")

    # Cycle de hiérarchie.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "cas"
        prepare(racine, tmp)
        for a, b in (("yldra", "corvin"), ("corvin", "yldra")):
            f = json.loads((racine / f"contenu/figures/{a}.json").read_text(encoding="utf-8"))
            f["superieur_par_defaut"] = b
            (tmp / "contenu/figures" / f"{a}.json").write_text(
                json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")
        code, sortie = lance(outil, tmp)
        ok = "cycle de hiérarchie" in sortie and code == 1
        print(f"{'ok   ' if ok else 'ÉCHEC'} G11 cycle")
        if not ok:
            echecs.append("G11 cycle")

    if echecs:
        print(f"\n{len(echecs)} échec(s) :")
        for e in echecs:
            print(f"  {e}")
        return 1
    print("\nTous les cas passent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
