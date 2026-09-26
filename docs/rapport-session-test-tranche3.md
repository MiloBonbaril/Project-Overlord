# Rapport de test — Tranche 3

**Date :** 26 septembre 2026  
**Verdict :** échec pour la décision « lancer la génération procédurale ». Le
prototype est exécutable et déterministe, mais ne permet pas encore de tester
la boucle de jeu promise : le joueur ne choisit ni l'ordre ni la composition.

## Périmètre et commandes

Exécuté depuis la racine, sur un état propre du prototype Python :

```sh
python3 outils/teste-suite.py
python3 outils/joue-partie.py --seed 20260926 --json
python3 outils/joue-partie.py --seed 1 --json
python3 outils/joue-partie.py --seed 42 --json
python3 outils/joue-partie.py --seed 1337 --json
python3 outils/joue-partie.py --seed 20260926 --clause terreur --json
```

La comparaison de deux exécutions de `--seed 42 --json` est identique octet à
octet. La suite de validation passe (16 tests). Les quatre parties finissent
en huit tours sans exception.

## Échantillon reproductible

Chaque seed contient les huit figures : aucune composition différente ne peut
être sélectionnée par la CLI actuelle. Les deux compositions demandées ne sont
donc pas testables ; c'est un écart fonctionnel, pas une donnée manquante du
test.

| Seed | Yldra | Corvin | Orine | Tessia | Omissions signalées |
| --- | --- | --- | --- | --- | --- |
| 20260926 | `interdire` (messe) | `remettre` (tribut) | `nommer` (frontière) | `publier` (lettre) | 3 / 8 |
| 1 | `interdire` (messe) | `ouvrir` (col) | `publier` (lettre) | `remettre` (tribut) | 5 / 8 |
| 42 | `prelever` (tribut) | `negocier` (mines) | `interdire` (messe) | `fortifier` (col) | 1 / 8 |
| 1337 | `securiser` (mines) | `remettre` (tribut) | `publier` (lettre) | `reconnaitre` (serment) | 3 / 8 |

Soit 12 messages d'omission sur 32 tours (37,5 %). La régression
Yldra/Corvin est couverte sur quatre seeds et les cas brouillard
Orine/Tessia aussi. La clause `terreur` modifie bien le tour 3 de la seed
20260926 : `interdire` devient `tolerer`.

## Mesures et ressenti

| Axe | Observation | Mesure / verdict |
| --- | --- | --- |
| Compréhension des ordres | Les deux options, leurs scores et l'action finale sont lisibles dans le journal, mais l'action est automatique. | 0 décision joueur sur 32 tours. Non mesurable comme jeu. |
| Brouillard | La phrase « Une part du rapport reste soigneusement tue » apparaît, mais tous les effets sont imprimés juste après dans `Faits`. | 12 / 32 signaux, 0 fait effectivement inconnu : pas de tension informationnelle. |
| Rapports | La seule variation est la dernière phrase ; le registre de la figure ne modifie pas le texte. | Lisible, mais répétitif et sans indice actionnable. |
| Surprise | Les changements d'action entre seeds existent (par exemple Tessia `fortifier` seed 42, `reconnaitre` seed 1337), mais le joueur ne les provoque ni ne les interprète. | Surprise observée dans le log, pas vécue. |
| Envie de relancer | Une seconde seed change l'ordre des situations et les actions, mais l'absence de contrôle ne donne aucun objectif de comparaison. | Faible. |

**Note de ressenti :** la sortie est réactive et se lit bien pour un outil de
diagnostic. Elle ressemble à un simulateur de batch, pas encore à une session
de conseil : il n'y a aucune interaction entre « conseil » et « résolution ».

## Relecture ciblée et constats actionnables

Le diff relu est le commit `ad2dd56`, principalement
`outils/joue-partie.py` et `docs/vertical-slice.md`. Aucun crash n'a été
observé sur les chemins testés.

1. **Bloquant — ordre automatiquement imposé.** `outils/joue-partie.py:98-99`
   calcule `auto`, puis la CLI appelle `play` sans `chosen` à la ligne 119.
   Le GDD, section 3, étape 2, exige que le joueur choisisse une option et une
   clause. Reproduction : lancer toute commande indiquée ci-dessus ; chaque
   tour affiche directement `Action` sans invite. Attendu : sélectionner un
   ordre avant résolution. Actuel : 0 choix sur 32 tours.
2. **Bloquant — aucune composition de serviteurs.** La CLI ne déclare que
   `--seed`, `--tours`, `--clause` et `--json` (`outils/joue-partie.py:113-117`)
   et charge systématiquement tous les JSON de `contenu/figures/` (ligne 77).
   Reproduction : `python3 outils/joue-partie.py --help`; aucune option de
   vivier/composition. Attendu : au moins deux viviers testables. Actuel : les
   huit figures sont toujours chargées.
3. **Majeur — brouillard annulé par l'affichage des faits.** La branche
   d'omission produit seulement une phrase générique (lignes 62-69), puis la
   boucle imprime tous les effets dans `faits` (lignes 102-108, 127). Exemple :
   seed 20260926, tour 3, Yldra dit qu'une part est tue mais le fait est quand
   même affiché. Attendu selon GDD §5 : rapport partiel avec une information à
   interpréter. Actuel : signal d'omission sans information masquée.

## Recommandation de décision

Ne pas lancer la génération procédurale. Aucun réglage numérique n'est proposé
ou modifié : l'obstacle est structurel et les observations ne permettent pas de
conclure sur les valeurs de bruit, effets ou franchise.

Avant une seconde session, fournir dans le vertical slice :

1. une sélection explicite de l'option (et clause) par tour ;
2. un paramètre de vivier pour rejouer deux compositions, dont
   Yldra/Corvin et Orine/Tessia ;
3. une vue joueur où un fait omis n'est pas affiché comme fait certain, tout en
   conservant le journal complet pour le testeur.

Ces trois points permettront alors de mesurer le plaisir plutôt que seulement
la stabilité du simulateur.
