# Tranche 2 — vertical slice jouable

Le slice est une exécution Python sans Godot. Il charge le catalogue, tire les
valeurs des huit figures dans un vivier déterministe, puis joue la boucle :

1. conseil (scores lisibles par option) ;
2. choix explicite de l'option et des clauses par le joueur ;
3. résolution des effets ;
4. faits et rapport du serviteur ;
5. conseil suivant.

## Lancer une partie

Depuis la racine :

```sh
python3 outils/joue-partie.py --seed 20260926
python3 outils/joue-partie.py --seed 20260926 --clause terreur --json > journal.json
python3 outils/joue-partie.py --seed 20260926 --composition yldra,corvin
python3 outils/joue-partie.py --seed 20260926 --composition orine,tessia
```

Sans `--json`, la commande demande l'option et les clauses à chaque tour.
`--choix` et `--clause-tour` (répétables, dans l'ordre des tours) permettent de
scripter les mêmes décisions. `--clause` reste compatible et applique une
clause globale ; l'exemple `messe-sans-temoin` contient une option explicitement
interdite par `terreur`. `--composition` limite le vivier aux identifiants
séparés par des virgules. Les compositions de test minimales sont
`yldra,corvin` et `orine,tessia`.

La même seed et les mêmes entrées produisent le même journal. En JSON,
`journal` est strictement la vue joueur : un fait omis n'y apparaît pas comme
certain. `journal_testeur` conserve les faits complets, le marqueur `fait_omis`
et les états avant/après résolution. Les deux conservent la seed, le vivier,
les scores de conseil, les clauses, l'action retenue et le rapport. Les
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
