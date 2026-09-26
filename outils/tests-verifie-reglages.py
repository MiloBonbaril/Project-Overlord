#!/usr/bin/env python3
"""Jeu de tests de verifie-reglages.py.

Une panne fabriquée par règle, plus les réglages livrés qui doivent passer.
Chaque cas vérifie le message et le code de sortie : un vérificateur qui
signale sans échouer laisse passer une intégration continue verte sur un
dossier cassé.

Usage : python3 outils/tests-verifie-reglages.py [racine]
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# (nom du cas, règle visée, fichier muté, mutation, fragment attendu)
CAS = [
    ("etiquette-sans-definition", "E1", "etiquettes.json",
     lambda d: d["etiquettes"]["patience"].pop("qualifie"),
     "sans définition"),
    ("plafond-abaisse", "E5", "etiquettes.json",
     lambda d: d["score"].update(poids_max_par_etiquette=3),
     "le score sort de l'intervalle"),
    ("poids-hors-domaine", "E2", "etiquettes.json",
     lambda d: d["etiquettes"]["ruse"]["poids"].update(zele=7),
     "poids 7"),
    ("ligne-saturee", "E3", "etiquettes.json",
     lambda d: d["etiquettes"]["terreur"]["poids"].update(initiative=2),
     "somme des poids absolus = 8"),
    ("franchise-non-nulle", "E4", "etiquettes.json",
     lambda d: d["etiquettes"]["ruse"]["poids"].update(franchise=2),
     "la colonne franchise n'est pas nulle"),
    ("village-casse", "E6", "etiquettes.json",
     lambda d: d["etiquettes"]["patience"]["poids"].update(cruaute=-2),
     "exemple du village"),
    ("sensibilite-deplacee", "E7", "etiquettes.json",
     lambda d: d["etiquettes"]["conformite"]["poids"].update(initiative=-2),
     "sensibilité maximale en initiative"),
    ("ampleurs-non-monotones", "A1", "ampleurs.json",
     lambda d: d["defaut"]["valeurs"].update(grande=12),
     "n'est pas monotone"),
    ("domaine-incomplet", "A2", "ampleurs.json",
     lambda d: d["domaine"]["attendu"].remove("ferveur"),
     "manquant ['ferveur']"),
    ("population-par-defaut", "A3", "ampleurs.json",
     lambda d: d["par_grandeur"].pop("population"),
     "projetée sur l'échelle population"),
    ("indices-trop-forts", "A4", "ampleurs.json",
     lambda d: d["par_grandeur"]["indices_sur_joueur"]["valeurs"].update(majeure=25),
     "ampleur maximale 25"),
    ("grande-sous-le-cran", "A5", "ampleurs.json",
     lambda d: d["defaut"]["valeurs"].update(grande=18, majeure=40),
     "sous le cran"),
    ("infime-decouple", "A5", "ampleurs.json",
     lambda d: d["defaut"]["valeurs"].update(infime=1),
     "amplitude du bruit"),
    ("bruit-double", "B1", "bruit.json",
     lambda d: d["bruit"].update(amplitude=6),
     "largeur minimale utile devient 30"),
    ("elagage-trop-large", "B2", "bruit.json",
     lambda d: d["elagage"].update(ecart=45),
     "hors de la fenêtre"),
    ("elagage-trop-etroit", "B2", "bruit.json",
     lambda d: d["elagage"].update(ecart=20),
     "hors de la fenêtre"),
    ("marge-deplacee", "B3", "bruit.json",
     lambda d: d["marge"].update(plancher=0.4),
     "marge, yldra sans clause"),
    ("trop-previsible", "B5", "bruit.json",
     lambda d: d["audace"]["temperature"].update(pente=3),
     "prédictibilité moyenne"),
    ("trop-imprevisible", "B5", "bruit.json",
     lambda d: d["audace"]["temperature"].update(base=20, pente=20),
     "prédictibilité moyenne"),
    ("grand-ecart-renverse", "B6", "bruit.json",
     lambda d: d["audace"]["temperature"].update(pente=22),
     "se renverse"),
]

# B4 — « une option élaguée sort quand même » — n'a pas de cas ici, et c'est
# volontaire : aucune valeur de réglage ne peut le produire, seule une erreur de
# code le pourrait. La règle est un garde-fou sur l'ordre élagage / bruit, qui est
# la chose qu'une réécriture de cet outil intervertira en premier.


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    outil = racine / "outils/verifie-reglages.py"
    echecs = []

    code, sortie = lance(outil, racine)
    if code != 0 or "Aucune erreur bloquante" not in sortie:
        echecs.append("les réglages livrés ne passent plus le vérificateur")
    else:
        print("ok    réglages livrés : aucune erreur bloquante")

    for nom, regle, fichier, mutation, attendu in CAS:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "cas"
            (tmp / "contenu").mkdir(parents=True)
            shutil.copytree(racine / "contenu/reglages", tmp / "contenu/reglages")
            chemin = tmp / "contenu/reglages" / fichier
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            mutation(donnees)
            chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
            code, sortie = lance(outil, tmp)
            ok = attendu in sortie and code == 1
            print(f"{'ok   ' if ok else 'ÉCHEC'} {regle} {nom}")
            if not ok:
                echecs.append(f"{regle} {nom} : attendu « {attendu} », code {code}")

    if echecs:
        print(f"\n{len(echecs)} échec(s) :")
        for e in echecs:
            print(f"  {e}")
        return 1
    print("\nTous les cas passent.")
    return 0


def lance(outil, cible):
    r = subprocess.run([sys.executable, str(outil), str(cible)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


if __name__ == "__main__":
    sys.exit(main())
