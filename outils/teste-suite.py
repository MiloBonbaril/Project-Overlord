#!/usr/bin/env python3
"""Validation unique du socle : réglages, figures et catalogue canonique."""

import subprocess
import sys
from pathlib import Path


def main():
    racine = Path(__file__).resolve().parents[1]
    commandes = [
        [sys.executable, str(racine / "outils/tests-verifie-reglages.py"), str(racine)],
        [sys.executable, str(racine / "outils/tests-verifie-figures.py"), str(racine)],
        [sys.executable, str(racine / "outils/tests-verifie-catalogue.py")],
        [sys.executable, str(racine / "outils/tests-joue-partie.py")],
    ]
    for commande in commandes:
        resultat = subprocess.run(commande, cwd=racine)
        if resultat.returncode:
            return resultat.returncode
    print("\nSuite de validation complète : réglages, figures et catalogue validés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
