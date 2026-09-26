#!/usr/bin/env python3
"""Vérification des trois réglages de décision : étiquettes, ampleurs, bruit.

Même statut que verifie-figures.py : ce n'est pas le linter du catalogue, c'est
le jeu de règles propre aux fichiers de réglage, exécutable aujourd'hui et
destiné à être repris tel quel dans l'outil définitif. Les règles portent les
identifiants E (étiquettes), A (ampleurs) et B (bruit), faits pour cohabiter
avec les G des figures et les R du catalogue.

L'essentiel de ce que fait cet outil n'est pas de vérifier des formes : c'est de
rendre exécutables les dérivations écrites dans les fichiers. Un nombre dérivé
dont la dérivation n'est vérifiée par personne redevient un nombre inventé au
premier rééquilibrage.

Usage : python3 outils/verifie-reglages.py [racine]
Sortie : 0 si aucune erreur bloquante, 1 sinon.
"""

import json
import math
import random
import sys
from pathlib import Path

TRAITS = ["zele", "cruaute", "initiative", "discretion", "franchise"]
AMPLEURS = ["infime", "legere", "notable", "grande", "majeure"]
TIRAGES = 40000
GRAINE = 20260925

# L'exemple chiffré du village, game design, section « Exemple chiffré : le village ».
YLDRA = {"zele": 90, "cruaute": 75, "initiative": 80, "discretion": 20, "franchise": 40}
CORVIN = {"zele": 35, "cruaute": 20, "initiative": 45, "discretion": 85, "franchise": 85}
OPTIONS_VILLAGE = [
    ("massacre", ["violence", "demonstration"]),
    ("discret", ["violence", "discretion"]),
    ("repousser", ["patience"]),
    ("payer", ["ruse", "generosite"]),
]
SCORES_ATTENDUS = {
    "yldra": {"massacre": 79, "discret": 54, "repousser": 23, "payer": 37},
    "corvin": {"massacre": 26, "discret": 48, "repousser": 62, "payer": 65},
}
MARGES_ATTENDUES = {
    "yldra sans clause": 0.95,
    "corvin sans clause": 0.675,
    "yldra sous clause": 0.633,
    "corvin sous clause": 0.45,
}
# Sensibilités maximales par trait, game design, section « En dessous de quinze
# points, une enveloppe ne fait rien ». Elles décident du barème d'amplitudes.
DELTAS_ATTENDUS = {"cruaute": 1.00, "initiative": 1.00, "zele": 0.83, "discretion": 0.83, "franchise": 0.00}
DELTA_TYPIQUE = 0.4  # deux options à deux étiquettes, cas normal du catalogue

erreurs = []
avertissements = []
lignes = []


def erreur(ou, quoi, faire):
    erreurs.append((ou, quoi, faire))


def avertit(ou, quoi, faire):
    avertissements.append((ou, quoi, faire))


def charge(racine):
    def lis(nom):
        return json.loads((racine / "contenu/reglages" / nom).read_text(encoding="utf-8"))
    return lis("etiquettes.json"), lis("ampleurs.json"), lis("bruit.json"), lis("monde.json")


# --------------------------------------------------------------------------
# Étiquettes
# --------------------------------------------------------------------------

def score(tags, traits, etiq):
    """Score déterministe d'une option, tel que le définit etiquettes.json."""
    conf = etiq["score"]
    x = {t: (traits[t] - conf["centre"]) / conf["amplitude"] for t in TRAITS}
    total = sum(etiq["etiquettes"][g]["poids"][t] * x[t] for g in tags for t in TRAITS)
    return conf["centre"] + conf["amplitude"] / (conf["poids_max_par_etiquette"] * len(tags)) * total


def sensibilite(tags, trait, etiq):
    """De combien de points de score un point de trait déplace cette option."""
    conf = etiq["score"]
    moyenne = sum(etiq["etiquettes"][g]["poids"][trait] for g in tags) / len(tags)
    return moyenne / conf["poids_max_par_etiquette"]


def verifie_etiquettes(etiq):
    ou = "etiquettes.json"
    plafond = etiq["score"]["poids_max_par_etiquette"]

    if etiq["traits"] != TRAITS:
        erreur(ou, f"traits déclarés {etiq['traits']}", f"les cinq traits sont {TRAITS}, dans cet ordre")
        return False

    for nom, e in etiq["etiquettes"].items():
        # E1 — forme.
        if not e.get("qualifie"):
            erreur(ou, f"étiquette « {nom} » sans définition",
                   "le champ qualifie n'est pas un commentaire : sans lui, deux auteurs posent la même "
                   "étiquette sur deux choses différentes et le désaccord ne se voit qu'à l'équilibrage")
        manquants = set(TRAITS) - set(e["poids"])
        surplus = set(e["poids"]) - set(TRAITS)
        if manquants or surplus:
            erreur(ou, f"étiquette « {nom} » : poids manquants {sorted(manquants)}, inconnus {sorted(surplus)}",
                   "une étiquette porte un poids par trait, les cinq, explicitement — un poids nul s'écrit 0")
            continue
        # E2 — domaine des poids.
        for t, p in e["poids"].items():
            if not isinstance(p, int) or abs(p) > 3:
                erreur(ou, f"étiquette « {nom} », trait {t} : poids {p}",
                       "les poids sont des entiers de -3 à +3")
        # E3 — contrainte de somme.
        somme = sum(abs(p) for p in e["poids"].values())
        if somme > plafond:
            erreur(ou, f"étiquette « {nom} » : somme des poids absolus = {somme}",
                   f"le plafond est {plafond}. C'est lui qui garantit un score dans [0, 100] sans "
                   f"écrêtage : retirez {somme - plafond} point(s) ailleurs sur la ligne")
        elif somme == plafond:
            lignes.append(f"  {nom:<14} somme {somme} — saturée, plus un point disponible sur cette ligne")

    # E4 — la colonne franchise est nulle.
    coupables = [n for n, e in etiq["etiquettes"].items() if e["poids"].get("franchise")]
    if coupables:
        erreur(ou, f"la colonne franchise n'est pas nulle : {', '.join(coupables)}",
               "la franchise ne décide jamais de ce qu'un serviteur fait, seulement de ce qu'il en "
               "raconte. Un poids non nul ici ferait d'un menteur un homme d'action différent")

    # E5 — l'intervalle de score, mesuré et non supposé : une option d'une à trois
    # étiquettes, sur des traits aux deux extrêmes, doit rester dans [0, 100].
    pire_haut, pire_bas = 50.0, 50.0
    for nom, e in etiq["etiquettes"].items():
        hauts = {t: 100 if e["poids"][t] > 0 else 0 for t in TRAITS}
        bas = {t: 0 if e["poids"][t] > 0 else 100 for t in TRAITS}
        pire_haut = max(pire_haut, score([nom], hauts, etiq))
        pire_bas = min(pire_bas, score([nom], bas, etiq))
    if pire_haut > 100.001 or pire_bas < -0.001:
        erreur(ou, f"le score sort de l'intervalle : de {pire_bas:.1f} à {pire_haut:.1f}",
               "c'est la contrainte de somme qui garantit l'intervalle. Une étiquette la dépasse, "
               "ou le plafond a été relevé sans relire la formule")
    return True


def verifie_exemple_scores(etiq):
    """E6 — les huit scores de l'exemple chiffré du village."""
    ok = True
    for nom, traits in (("yldra", YLDRA), ("corvin", CORVIN)):
        for opt, tags in OPTIONS_VILLAGE:
            # Arrondi au plus proche, la moitié vers le haut. L'arrondi bancaire de Python
            # afficherait 22 là où le document affiche 23 : le score exact vaut 22,5.
            calcule = math.floor(score(tags, traits, etiq) + 0.5)
            attendu = SCORES_ATTENDUS[nom][opt]
            if calcule != attendu:
                erreur("etiquettes.json",
                       f"exemple du village, {nom} / {opt} : la table donne {calcule}, le document dit {attendu}",
                       "l'exemple est un test de régression sur le scoring. Soit la retouche de la table "
                       "est involontaire, soit l'exemple du game design est à recalculer et à réécrire")
                ok = False
    return ok


def verifie_sensibilites(etiq):
    """E7 — les sensibilités maximales, dont dépend le barème d'amplitudes."""
    for trait, attendu in DELTAS_ATTENDUS.items():
        poids = [e["poids"][trait] for e in etiq["etiquettes"].values()]
        delta = (max(poids) - min(poids)) / etiq["score"]["poids_max_par_etiquette"]
        if abs(delta - attendu) > 0.01:
            erreur("etiquettes.json",
                   f"sensibilité maximale en {trait} : {delta:.2f}, le game design annonce {attendu:.2f}",
                   "cette valeur fixe la largeur minimale utile d'une enveloppe de traits. La changer "
                   "sans relire le barème d'amplitudes produit des enveloppes qui ne font plus rien")


# --------------------------------------------------------------------------
# Ampleurs
# --------------------------------------------------------------------------

def grandeurs_inscriptibles(monde):
    """L'ensemble exact des grandeurs qu'une situation a le droit d'écrire."""
    trouvees = set()
    for spec in monde["types"].values():
        ro = set(spec.get("lecture_seule") or [])
        for champ, t in spec["champs"].items():
            if t.startswith("echelle:") and champ not in ro:
                trouvees.add(champ)
    for nom, rel in monde["relations"].items():
        if not rel.get("lecture_seule"):
            trouvees.add(nom)
    return trouvees


def echelle_de(nom, monde):
    for spec in monde["types"].values():
        t = spec["champs"].get(nom)
        if t and t.startswith("echelle:"):
            return t.split(":", 1)[1]
    rel = monde["relations"].get(nom)
    return rel["echelle"] if rel else None


def verifie_ampleurs(amp, monde, bruit):
    ou = "ampleurs.json"
    defaut = amp["defaut"]
    par_grandeur = {k: v for k, v in amp["par_grandeur"].items() if k != "note"}

    if amp["ampleurs"] != AMPLEURS:
        erreur(ou, f"ampleurs déclarées {amp['ampleurs']}",
               f"le format en fixe cinq, dans cet ordre : {AMPLEURS}")
        return

    # A1 — chaque barème est complet et strictement monotone dans le bon sens.
    for nom, bareme in [("defaut", defaut)] + sorted(par_grandeur.items()):
        vals = bareme["valeurs"]
        if sorted(vals) != sorted(AMPLEURS):
            erreur(ou, f"barème « {nom} » : ampleurs {sorted(vals)}",
                   f"les cinq ampleurs sont obligatoires : {AMPLEURS}")
            continue
        suite = [vals[a] for a in AMPLEURS]
        croissant = bareme["unite"] == "points"
        ordonne = all(b > a for a, b in zip(suite, suite[1:])) if croissant \
            else all(b < a for a, b in zip(suite, suite[1:]))
        if not ordonne:
            erreur(ou, f"barème « {nom} » : {suite} n'est pas monotone",
                   "infime < legere < notable < grande < majeure en points, l'inverse en facteur. "
                   "Sans monotonie, une ampleur plus forte peut produire un effet plus faible")
        if croissant and any(v <= 0 for v in suite):
            erreur(ou, f"barème « {nom} » : valeur nulle ou négative", "une ampleur est un écart, le sens vient de l'effet")
        if not croissant and any(not 0 < v < 1 for v in suite):
            erreur(ou, f"barème « {nom} » : facteur hors de ]0, 1[",
                   "un facteur s'écrit toujours en baisse ; la hausse est son inverse")

    # A2 — le domaine est exactement celui de monde.json.
    attendu = grandeurs_inscriptibles(monde)
    declare = set(amp["domaine"]["attendu"])
    if declare != attendu:
        erreur(ou, f"domaine déclaré : en trop {sorted(declare - attendu)}, manquant {sorted(attendu - declare)}",
               "le domaine est exactement l'ensemble des champs echelle: non listés en lecture_seule, "
               "plus les relations inscriptibles. Une entrée en trop est un barème inutilisable ; une "
               "entrée manquante est une situation légale que le moteur ne saura pas appliquer")

    # A3 — toute grandeur dont la projection n'est pas niveau a son propre barème.
    for g in sorted(attendu):
        ech = echelle_de(g, monde)
        if ech != defaut["echelle"] and g not in par_grandeur:
            erreur(ou, f"« {g} » est projetée sur l'échelle {ech}, pas sur {defaut['echelle']}",
                   "elle ne peut pas hériter du barème par défaut : un écart en points n'a pas de "
                   "sens sur une autre grandeur interne. Donnez-lui son barème")
        if g in par_grandeur and par_grandeur[g]["echelle"] != ech:
            erreur(ou, f"« {g} » : barème sur l'échelle {par_grandeur[g]['echelle']}, schéma sur {ech}", "alignez les deux")

    # A4 — indices_sur_joueur reste sous le cran.
    cran = largeur_de_cran(monde, defaut["echelle"])
    if "indices_sur_joueur" in par_grandeur:
        pire = max(par_grandeur["indices_sur_joueur"]["valeurs"].values())
        if pire >= cran:
            erreur(ou, f"indices_sur_joueur : ampleur maximale {pire}, cran de l'échelle {cran}",
                   "toutes les valeurs doivent rester strictement sous la largeur d'un cran, sinon une "
                   "situation seule fait monter d'un cran ce qu'une faction a déduit — et une déduction "
                   "qui tient à une seule scène court-circuite le graphe de rumeurs")

    # A5 — le barème par défaut est bien celui que sa dérivation annonce.
    v = defaut["valeurs"]
    if v["notable"] >= cran:
        erreur(ou, f"notable = {v['notable']} atteint le cran de {cran}",
               "notable est l'ampleur ordinaire : son effet se sent sans être garanti visible. "
               "Au-dessus du cran, elle fait le travail de grande")
    if v["grande"] < cran:
        erreur(ou, f"grande = {v['grande']} sous le cran de {cran}",
               "grande est définie comme la première ampleur qui change toujours le cran affiché")
    if v["majeure"] < 2 * cran:
        erreur(ou, f"majeure = {v['majeure']} sous deux crans ({2 * cran})",
               "majeure est « s'effondre » : l'exemple du village lui fait traverser deux crans de "
               "loyauté d'un coup. En dessous, l'exemple ne dit plus ce qu'il dit")
    if v["infime"] != bruit["bruit"]["amplitude"]:
        erreur(ou, f"infime = {v['infime']}, amplitude du bruit = {bruit['bruit']['amplitude']}",
               "infime est défini comme le plus petit mouvement que le jeu admette, donc comme "
               "l'amplitude du bruit. Les deux se déplacent ensemble")


def largeur_de_cran(monde, echelle):
    bornes = monde["projections"][echelle]["bornes"]
    ecarts = [b - a for a, b in zip(bornes, bornes[1:])]
    return min(ecarts) if ecarts else 0


# --------------------------------------------------------------------------
# Bruit
# --------------------------------------------------------------------------

def marge(P, Z, bruit):
    m = bruit["marge"]
    return (1 - P) * (m["plancher"] + m["poids_zele"] * Z / 100)


def tirage(traits, options, M, etiq, bruit, alea):
    """Une décision complète : élagage, puis bruit, puis audace."""
    det = {nom: score(tags, traits, etiq) for nom, tags in options}
    meilleur = max(det.values())
    seuil = meilleur - bruit["elagage"]["ecart"]
    amp = bruit["bruit"]["amplitude"]
    T = bruit["audace"]["temperature"]["base"] + bruit["audace"]["temperature"]["pente"] * M
    bruites = {n: v + alea.uniform(-amp, amp) for n, v in det.items() if v >= seuil}
    haut = max(bruites.values())
    poids = {n: math.exp((v - haut) / T) for n, v in bruites.items()}
    total = sum(poids.values())
    r = alea.random() * total
    cumul = 0.0
    for n, p in poids.items():
        cumul += p
        if r <= cumul:
            return n
    return n


def verifie_bruit(etiq, bruit):
    ou = "bruit.json"
    alea = random.Random(GRAINE)

    # B1 — l'amplitude du bruit et le premier cran du barème d'amplitudes sont couplés.
    amp = bruit["bruit"]["amplitude"]
    premier_cran = 2 * amp / DELTA_TYPIQUE
    if abs(premier_cran - 15) > 0.5:
        erreur(ou, f"amplitude {amp} : la largeur minimale utile devient {premier_cran:.0f} points, le "
                   f"barème d'amplitudes commence à 15",
               "la largeur minimale utile vaut deux fois l'amplitude du bruit divisée par la "
               "sensibilité. Doubler le bruit double le premier cran : les deux se règlent ensemble "
               "ou pas du tout, et le barème du game design est à réécrire")

    # B2 — l'élagage tient dans la fenêtre que l'exemple chiffré laisse ouverte.
    ecart = bruit["elagage"]["ecart"]
    sous_clause = [o for o in OPTIONS_VILLAGE if "demonstration" not in o[1]]
    det_y = {n: score(t, YLDRA, etiq) for n, t in sous_clause}
    plancher_haut = max(det_y.values()) - min(det_y.values())
    det_c = {n: score(t, CORVIN, etiq) for n, t in OPTIONS_VILLAGE}
    plafond_bas = max(det_c.values()) - det_c["massacre"]
    if not plancher_haut < ecart < plafond_bas:
        erreur(ou, f"écart d'élagage {ecart} hors de la fenêtre ]{plancher_haut:.0f}, {plafond_bas:.0f}[",
               "sous cette fenêtre, la clause rend Yldra déterministe ; au-dessus, Corvin massacre "
               "parfois. L'exemple du village dit les deux choses et elles se contredisent alors")

    # B3 — les marges de l'exemple.
    calculees = {
        "yldra sans clause": marge(0, YLDRA["zele"], bruit),
        "corvin sans clause": marge(0, CORVIN["zele"], bruit),
        "yldra sous clause": marge(1 / 3, YLDRA["zele"], bruit),
        "corvin sous clause": marge(1 / 3, CORVIN["zele"], bruit),
    }
    for cas, attendu in MARGES_ATTENDUES.items():
        if abs(calculees[cas] - attendu) > 0.005:
            erreur(ou, f"marge, {cas} : {calculees[cas]:.3f} au lieu de {attendu:.3f}",
                   "les quatre marges sont citées dans le game design. Les changer change ce que "
                   "l'exemple enseigne sur les clauses")

    # B4 à B6 — les quatre décisions de l'exemple, tirées pour de bon.
    cas = [
        ("Yldra sans clause", YLDRA, OPTIONS_VILLAGE, calculees["yldra sans clause"]),
        ("Corvin sans clause", CORVIN, OPTIONS_VILLAGE, calculees["corvin sans clause"]),
        ("Yldra sous clause", YLDRA, sous_clause, calculees["yldra sous clause"]),
        ("Corvin sous clause", CORVIN, sous_clause, calculees["corvin sous clause"]),
    ]
    predictibilites = []
    for nom, traits, options, M in cas:
        det = {n: score(t, traits, etiq) for n, t in options}
        favori = max(det, key=det.get)
        compte = {n: 0 for n in det}
        for _ in range(TIRAGES):
            compte[tirage(traits, options, M, etiq, bruit, alea)] += 1
        part = {n: c / TIRAGES for n, c in compte.items()}
        predictibilites.append(part[favori])
        detail = ", ".join(f"{n} {part[n]:.0%}" for n in sorted(part, key=lambda k: -part[k]))
        lignes.append(f"  {nom:<20} M={M:.3f}  T={bruit['audace']['temperature']['base'] + bruit['audace']['temperature']['pente'] * M:5.2f}  {detail}")

        # B4 — ce que le serviteur ne fera jamais, il ne le fait jamais.
        for n, p in part.items():
            if det[n] < max(det.values()) - bruit["elagage"]["ecart"] and p > 0:
                erreur(ou, f"{nom} : « {n} » est élaguée et sort pourtant {p:.1%} du temps",
                       "l'élagage se fait sur le score déterministe, avant le bruit. Un choix "
                       "inexplicable une fois sur mille est pire qu'un choix jamais fait")

    # B5 — la prédictibilité visée.
    cible = bruit["cibles"]["predictibilite"]
    moyenne = sum(predictibilites) / len(predictibilites)
    lignes.append(f"  {'prédictibilité moyenne':<20} {moyenne:.3f}  (cible {cible['valeur']} ± {cible['tolerance']})")
    if abs(moyenne - cible["valeur"]) > cible["tolerance"]:
        erreur(ou, f"prédictibilité moyenne {moyenne:.3f}, cible {cible['valeur']} ± {cible['tolerance']}",
               "au-dessus, le système n'est qu'une table de correspondance ; en dessous, le joueur "
               "se sent trahi par un dé. Le réglage est la pente de la température")

    # B6 — le grand écart se renverse, rarement.
    cible_ge = bruit["cibles"]["renversement_grand_ecart"]
    det = {n: score(t, YLDRA, etiq) for n, t in OPTIONS_VILLAGE}
    favori = max(det, key=det.get)
    ecart_reel = det[favori] - sorted(det.values())[-2]
    renverse = 1 - predictibilites[0]
    if abs(ecart_reel - cible_ge["ecart"]) > 1.5:
        avertit(ou, f"l'écart de l'exemple vaut {ecart_reel:.0f} points, la cible parle de {cible_ge['ecart']}",
                "la cible de renversement est écrite pour l'exemple du village ; si l'écart bouge, elle mesure autre chose")
    if renverse > cible_ge["maximum"]:
        erreur(ou, f"un écart de {ecart_reel:.0f} points se renverse {renverse:.1%} du temps, "
                   f"maximum admis {cible_ge['maximum']:.0%}",
               "au-delà, la surprise n'est plus une surprise, c'est un serviteur qu'on ne connaît "
               "pas. Baissez la pente de la température")


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        etiq, amp, bruit, monde = charge(racine)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"chargement impossible : {exc}")
        return 1

    if verifie_etiquettes(etiq):
        verifie_exemple_scores(etiq)
        verifie_sensibilites(etiq)
    verifie_ampleurs(amp, monde, bruit)
    verifie_bruit(etiq, bruit)

    print(f"réglages lus dans {racine / 'contenu/reglages'}\n")
    for ligne in lignes:
        print(ligne)

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
