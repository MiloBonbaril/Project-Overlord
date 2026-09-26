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
- Godot 4.x pour l’interface (aucune dépendance externe pour la validation ou le vertical slice Python)

## Valider le dépôt

Depuis la racine du dépôt :

```sh
python3 outils/teste-suite.py
```

Cette commande valide les réglages, les 8 figures et le catalogue canonique. Elle retourne un code non nul dès qu'un contrat de données ou un cas de non-régression casse ; c'est la commande à utiliser en CI.

## Jouer

Interface Godot, depuis la racine du dépôt :

```sh
godot4 --editor project.godot
# ou directement
godot4 --path .
```

Saisissez une seed puis utilisez **Lancer**. Chaque tour affiche le conseil et
les ordres, accepte les clauses séparées par des virgules, puis présente la
résolution, les faits autorisés et le rapport. **Rejouer la même seed** remet la
partie à zéro ; avec les mêmes ordres et clauses, son journal est identique.

La scène exécute `outils/joue-partie.py`, unique source des règles, et lit le
catalogue dans `contenu/`. Les données restent dans le dépôt. Limites connues :
Python doit accompagner le projet (pas encore d’export desktop autonome), la
composition du vivier et l’index de monde ne sont pas exposés dans l’interface,
et l’habillage est provisoire.

Validation ciblée du pont :

```sh
python3 outils/tests-integration-godot.py
```

Le vertical slice en terminal reste disponible :

```sh
python3 outils/joue-partie.py --seed 20260926
python3 outils/joue-partie.py --seed 20260926 --clause terreur --json > journal.json
```

La même seed et les mêmes entrées produisent le même journal.

## État du projet

Le concept est stabilisé et le socle de validation est en place. La prochaine étape est de mesurer le plaisir de la boucle sur 6 à 10 situations, puis de tester plusieurs seeds avant d'implémenter la génération procédurale complète.

## Licence

Projet privé de Bonbaril corp. — tous droits réservés.
