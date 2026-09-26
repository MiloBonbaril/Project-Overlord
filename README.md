# Project Overlord

Jeu de stratégie narrative, de diplomatie et de gestion de serviteurs, inspiré par les jeux de pouvoir, d'espionnage et de combat de l'œuvre *Overlord*.

Le joueur dirige un territoire depuis une salle du conseil. Il est puissant, mais mal informé : il choisit qui peut se présenter devant lui et donne des ordres, sans contrôler exactement les personnalités, les informations ni les conséquences qui en découlent.

## Lire le projet

Le document de référence est le [Game Design Document](docs/GDD.md). Il présente la vision, les piliers, la boucle de jeu, les serviteurs, le format du catalogue et la stratégie de génération procédurale.

La [feuille de route de production](docs/plan-suite-production.md) détaille le séquencement actuel. La [tranche jouable](docs/vertical-slice.md) décrit le prototype Python qui sert à tester la boucle centrale avant l'intégration d'une interface Godot.

## Organisation

```
contenu/
  catalogue/   Situations écrites et exemple canonique
  figures/     Figures et enveloppes de traits
  reglages/    Contrats numériques et lexiques normatifs
docs/
  GDD.md       Document de Game Design de référence
  ...          Rapports, brief et plans de production
outils/        Vérificateurs, tests et prototype de partie
```

## Pré-requis

- Python 3.10 ou plus récent
- aucune dépendance externe pour la validation ou le vertical slice

## Valider le dépôt

Depuis la racine du dépôt :

```sh
python3 outils/teste-suite.py
```

Cette commande valide les réglages, les 8 figures et le catalogue canonique. Elle retourne un code non nul dès qu'un contrat de données ou un cas de non-régression casse ; c'est la commande à utiliser en CI.

## Jouer le vertical slice

```sh
python3 outils/joue-partie.py --seed 20260926
python3 outils/joue-partie.py --seed 20260926 --clause terreur --json > journal.json
```

La même seed produit le même journal. Godot n'est pas nécessaire pour cette tranche.

## État du projet

Le concept est stabilisé et le socle de validation est en place. La prochaine étape est de mesurer le plaisir de la boucle sur 6 à 10 situations, puis de tester plusieurs seeds avant d'implémenter la génération procédurale complète.

## Licence

Projet privé de Bonbaril corp. — tous droits réservés.
