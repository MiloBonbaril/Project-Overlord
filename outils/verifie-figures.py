#!/usr/bin/env python3
"""Vérification des figures livrées.

Ce n'est pas le linter du catalogue de situations, qui est spécifié à part et
reste à écrire. C'est le jeu de règles propre au dossier contenu/figures/,
exécuté à la main tant que le linter n'existe pas, et destiné à y être repris
tel quel : les règles portent ici les identifiants G1 à G11.

Usage : python3 outils/verifie-figures.py [racine]
Sortie : 0 si aucune erreur bloquante, 1 sinon.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

TRAITS = ["zele", "cruaute", "initiative", "discretion", "franchise"]
CHAMPS_OBLIGATOIRES = {
    "format", "id", "nom", "genre", "titre", "registre",
    "aptitude", "enveloppes", "superieur_par_defaut", "presentation",
}
CHAMPS_FACULTATIFS = {"deprecie", "lint"}
GENRES = {"masculin", "feminin"}
CRANS = {0: "exacte", 15: "serrée", 25: "marquée", 40: "nette", 65: "large", 100: "ouverte"}
PLANCHER_DE_DOUTE = 230
SEUIL_EXTREME = 80

erreurs = []
avertissements = []
infos = []


def erreur(ou, quoi, faire):
    erreurs.append((ou, quoi, faire))


def avertit(ou, quoi, faire):
    avertissements.append((ou, quoi, faire))


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def charge(racine):
    monde = json.loads((racine / "contenu/reglages/monde.json").read_text(encoding="utf-8"))
    voix = json.loads((racine / "contenu/reglages/voix.json").read_text(encoding="utf-8"))
    aveu = json.loads((racine / "contenu/reglages/aveu.json").read_text(encoding="utf-8"))
    prose = json.loads((racine / "contenu/reglages/prose.json").read_text(encoding="utf-8"))
    figures = {}
    for chemin in sorted((racine / "contenu/figures").glob("*.json")):
        figures[chemin.stem] = (chemin, json.loads(chemin.read_text(encoding="utf-8")))
    return monde, voix, aveu, prose, figures


def verifie(racine):
    monde, voix, aveu, prose, figures = charge(racine)

    competences = [c for c, t in monde["types"]["serviteur"]["champs"].items()
                   if t == "echelle:niveau" and c not in ("foi", "fatigue")]
    registres = voix["registres"]
    seuils = aveu["seuils_de_comportement"]

    mots_nombres = set()
    for groupe in ("unites", "dizaines", "multiplicateurs"):
        mots_nombres |= set(prose["nombres_en_lettres"][groupe])
    mots_nombres -= set(prose["nombres_en_lettres"]["articles_ambigus"])

    noms_vus = {}

    for fid, (chemin, fig) in figures.items():
        ou = chemin.name

        # G1 — chargement : champs obligatoires, aucun champ inconnu, format connu.
        manquants = CHAMPS_OBLIGATOIRES - set(fig)
        inconnus = set(fig) - CHAMPS_OBLIGATOIRES - CHAMPS_FACULTATIFS
        if manquants:
            erreur(ou, f"champs obligatoires absents : {', '.join(sorted(manquants))}",
                   "ajoutez-les ; aucun n'a de valeur par défaut")
        if inconnus:
            erreur(ou, f"champs inconnus : {', '.join(sorted(inconnus))}",
                   "un champ sans consommateur ne doit pas exister ; retirez-le ou déclarez-le dans le format")
        if fig.get("format") != 1:
            erreur(ou, f"format vaut {fig.get('format')}", "le seul format connu est 1")
        if manquants:
            continue

        # G2 — le nom de fichier est l'identifiant.
        if fig["id"] != chemin.stem:
            erreur(ou, f"id « {fig['id']} » et nom de fichier « {chemin.stem} » diffèrent",
                   "l'identifiant est immuable : renommez le fichier, jamais l'id")
        if not re.fullmatch(r"[a-z0-9-]+", fig["id"]):
            erreur(ou, f"id « {fig['id']} » hors jeu de caractères",
                   "minuscules, chiffres et tirets uniquement")

        # G3 — genre grammatical.
        if fig["genre"] not in GENRES:
            erreur(ou, f"genre « {fig['genre']} » inconnu",
                   f"valeurs admises : {', '.join(sorted(GENRES))}")

        # G4 — le registre existe.
        if fig["registre"] not in registres:
            erreur(ou, f"registre « {fig['registre']} » absent de reglages/voix.json",
                   f"registres déclarés : {', '.join(sorted(registres))}")

        # G5 — aptitude.
        apt = fig["aptitude"]
        for cle in ("majeure", "mineure"):
            if apt.get(cle) not in competences:
                erreur(ou, f"aptitude.{cle} « {apt.get(cle)} » n'est pas une compétence",
                       f"compétences déclarées par monde.json : {', '.join(competences)}")
        if apt.get("majeure") == apt.get("mineure"):
            erreur(ou, "aptitude majeure et mineure identiques",
                   "une aptitude nomme deux compétences distinctes, sinon le plafond mineur est inutile")

        # G6 — bornes des enveloppes.
        env = fig["enveloppes"]
        if set(env) != set(TRAITS):
            erreur(ou, f"enveloppes : traits attendus {TRAITS}, trouvés {sorted(env)}",
                   "les cinq traits sont obligatoires, aucun autre n'existe")
            continue
        borne_cassee = False
        for t in TRAITS:
            bas, haut = env[t]
            if not all(isinstance(v, int) for v in (bas, haut)):
                erreur(ou, f"{t} : bornes non entières", "les traits sont entiers de 0 à 100")
                borne_cassee = True
            elif not (0 <= bas <= haut <= 100):
                erreur(ou, f"{t} : bornes [{bas}, {haut}] invalides",
                       "il faut 0 <= bas <= haut <= 100")
                borne_cassee = True
        if borne_cassee:
            continue

        largeurs = {t: env[t][1] - env[t][0] for t in TRAITS}
        somme = sum(largeurs.values())

        # G7 — plancher de doute.
        if somme < PLANCHER_DE_DOUTE:
            manque = PLANCHER_DE_DOUTE - somme
            erreur(ou, f"somme des largeurs = {somme}, sous le plancher de doute de {PLANCHER_DE_DOUTE}",
                   f"élargissez de {manque} points, par exemple en passant une enveloppe au cran supérieur")

        # G8 — la franchise couvre au moins deux paliers d'aveu, seuils effectifs du registre.
        # Un registre marqué surcharge le coût d'aveu de chaque fait, donc il déplace les
        # seuils qui décident du tri. La règle se vérifie contre les seuils que cette
        # figure rencontrera réellement, jamais contre les seuils nus.
        franchise = env["franchise"]
        surcharge = registres.get(fig["registre"], {}).get("omission", {}).get("surcharge_aveu", 0)
        seuils_effectifs = [s + surcharge for s in seuils]
        traverses = [s for s in seuils_effectifs if franchise[0] < s <= franchise[1]]
        if largeurs["franchise"] == 0:
            erreur(ou, "franchise exacte",
                   "l'enveloppe de franchise ne peut pas être exacte : tous les rapports deviendraient prévisibles")
        elif not traverses:
            detail = (f"seuils {seuils_effectifs}, surchargés de {surcharge} par le registre "
                      f"« {fig['registre']} »") if surcharge else f"seuils {seuils_effectifs}"
            erreur(ou, f"franchise [{franchise[0]}, {franchise[1]}] ne traverse aucun seuil d'aveu ({detail})",
                   "déplacez ou élargissez la plage pour qu'elle contienne un seuil : sinon la figure trie toujours ses faits de la même façon")

        # G9 — crans du barème (avertissement : les figures livrées ne sont pas tenues par les crans).
        for t in TRAITS:
            if largeurs[t] not in CRANS:
                avertit(ou, f"{t} : largeur {largeurs[t]} hors barème",
                        f"crans disponibles : {', '.join(f'{v} ({n})' for v, n in sorted(CRANS.items()))}")

        # G10 — une présentation ne cite un nombre que si l'enveloppe correspondante est exacte.
        mots = set(re.findall(r"[\w'-]+", sans_accents(fig["presentation"])))
        cites = sorted(m for m in mots_nombres if sans_accents(m) in mots)
        if cites and not any(largeurs[t] == 0 for t in TRAITS):
            erreur(ou, f"la présentation cite un nombre ({', '.join(cites)}) alors qu'aucune enveloppe n'est exacte",
                   "une présentation n'annonce une valeur que si la figure la garantit ; sinon écrivez une tendance")

        # G11 — unicité du nom affiché.
        if fig["nom"] in noms_vus:
            erreur(ou, f"nom « {fig['nom']} » déjà porté par {noms_vus[fig['nom']]}",
                   "deux figures homonymes sont indiscernables dans la salle du conseil")
        noms_vus[fig["nom"]] = ou

        # Information : plafond de compétence.
        garanti = [t for t in TRAITS if env[t][0] >= SEUIL_EXTREME]
        possible = [t for t in TRAITS if env[t][1] >= SEUIL_EXTREME]
        if garanti:
            etat = f"plafond levé à coup sûr ({', '.join(garanti)})"
        elif possible:
            etat = f"plafond levé selon le tirage ({', '.join(possible)})"
        else:
            etat = "PLAFONNÉE À VIE : aucun trait ne peut atteindre 80"
        infos.append((ou, somme, etat))

    # Hiérarchie : existence, absence de cycle, profondeur.
    for fid, (chemin, fig) in figures.items():
        sup = fig.get("superieur_par_defaut")
        if sup is None:
            continue
        if sup not in figures:
            erreur(chemin.name, f"superieur_par_defaut « {sup} » n'est pas une figure",
                   "citez l'identifiant d'un fichier de contenu/figures/")
            continue
        vus, courant, profondeur = {fid}, sup, 1
        while courant is not None:
            if courant in vus:
                erreur(chemin.name, f"cycle de hiérarchie passant par « {courant} »",
                       "une chaîne de commandement remonte toujours au joueur")
                break
            vus.add(courant)
            profondeur += 1
            courant = figures[courant][1].get("superieur_par_defaut")
        if profondeur > 3:
            avertit(chemin.name, f"profondeur hiérarchique {profondeur}",
                    "chaque niveau ajoute sa marge d'interprétation ; au-delà de trois, un ordre n'arrive plus reconnaissable")

    return figures


def regression_exemple_chiffre(racine, figures):
    """L'exemple chiffré du game design doit rester un tirage légal des figures livrées."""
    attendus = {
        "yldra": {"zele": 90, "cruaute": 75, "initiative": 80, "discretion": 20, "franchise": 40},
        "corvin": {"zele": 35, "cruaute": 20, "initiative": 45, "discretion": 85, "franchise": 85},
    }
    ok = True
    for fid, valeurs in attendus.items():
        if fid not in figures:
            erreur("exemple chiffré", f"la figure « {fid} » de l'exemple du village n'existe pas", "")
            ok = False
            continue
        env = figures[fid][1]["enveloppes"]
        for t, v in valeurs.items():
            if not (env[t][0] <= v <= env[t][1]):
                erreur(f"{fid}.json", f"la valeur {t} = {v} de l'exemple chiffré est hors de l'enveloppe {env[t]}",
                       "l'exemple du village est un test de régression : soit l'enveloppe le couvre, soit l'exemple est réécrit")
                ok = False
    return ok


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    figures = verifie(racine)
    regression_exemple_chiffre(racine, figures)

    print(f"{len(figures)} figures lues dans {racine / 'contenu/figures'}\n")
    print("  figure            doute   plafond de compétence")
    for ou, somme, etat in sorted(infos):
        print(f"  {ou:<18}{somme:>5}   {etat}")

    for titre, lot in (("AVERTISSEMENTS", avertissements), ("ERREURS", erreurs)):
        if lot:
            print(f"\n{titre} ({len(lot)})")
            for ou, quoi, faire in lot:
                print(f"  {ou}\n    {quoi}\n    → {faire}")

    if not erreurs:
        print("\nAucune erreur bloquante.")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
