# Tranche 2 — vertical slice jouable

Le slice est une exécution Python sans Godot. Il charge le catalogue, tire les
valeurs des huit figures dans un vivier déterministe, puis joue la boucle :

1. conseil (scores lisibles par option) ;
2. choix automatique déterministe ;
3. résolution des effets ;
4. faits et rapport du serviteur ;
5. conseil suivant.

## Lancer une partie

Depuis la racine :

```sh
python3 outils/joue-partie.py --seed 20260926
python3 outils/joue-partie.py --seed 20260926 --clause terreur --json > journal.json
```

La même seed produit le même journal. `--clause` est répétable et applique une
clause existante du catalogue ; l'exemple `messe-sans-temoin` contient une
option explicitement interdite par `terreur`.

Le journal conserve la seed, les huit identifiants du vivier, les scores de
conseil, l'action retenue, les faits, le rapport et l'état avant/après. Les
effets de niveau sont persistants d'un tour au suivant : c'est la conséquence
durable minimale testée dans cette tranche.

## Côté utilisateur et Godot

Pour cette tranche, il suffit d'installer Python 3.10+ et de lancer la
commande ci-dessus. Godot n'est pas nécessaire : il apporterait l'interface,
les scènes et l'export desktop plus tard, mais ralentirait la validation du
plaisir central. Une future intégration Godot pourra appeler le même moteur ou
rejouer ce journal JSON ; elle ne doit pas déplacer les règles dans les scènes.

La validation des données reste :

```sh
python3 outils/teste-suite.py
```
