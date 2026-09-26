# Plan de suite — Project Overlord

## Décision de séquencement

Le concept est suffisamment stabilisé pour commencer la production. La prochaine tranche ne doit pas ajouter de systèmes : elle doit prouver que le format, les figures et la boucle de décision produisent une partie lisible.

## Tranche 1 — verrou technique du socle

Objectif : obtenir une base reproductible avant d'écrire davantage de contenu.

- Diagnostiquer et rendre exploitable la suite `outils/tests-verifie-reglages.py`, qui dépasse actuellement le délai de vérification.
- Ajouter une commande de validation unique couvrant réglages, figures et catalogue.
- Conserver le catalogue canonique comme test de non-régression.
- Documenter la version de Python et la commande de test utilisée en CI.

Sortie attendue : une validation locale et CI qui échoue clairement lorsqu'un contrat de données est cassé.

## Tranche 2 — vertical slice jouable

Objectif : tester le plaisir central sur une partie complète mais minimale.

- Écrire 6 à 10 situations du catalogue, avec au moins un conflit de rapport, une clause et une conséquence durable.
- Utiliser les 8 figures livrées et le vivier généré, sans ajouter de nouveau mécanisme.
- Implémenter uniquement la boucle conseil → choix d'une action → résolution → faits/rapports → conseil suivant.
- Produire un journal de partie déterministe à seed fixe pour faciliter le débogage.

Critère de sortie : une partie courte peut être jouée de bout en bout, et les décisions des serviteurs restent compréhensibles sans lire les fichiers de données.

## Tranche 3 — première session de test

Objectif : mesurer le concept, pas optimiser le contenu.

- Faire jouer plusieurs seeds et au moins deux compositions de serviteurs.
- Mesurer : compréhension des ordres, intérêt du brouillard, lisibilité des rapports, fréquence des choix surprenants et envie de relancer une partie.
- Tester explicitement Yldra/Corvin comme cas de régression et Orine/Tessia comme cas de brouillard.
- Réviser les réglages uniquement à partir des observations ; consigner chaque changement dans un rapport.

## Tranche 4 — génération procédurale

Cette tranche vient après la preuve d'intérêt d'une partie unique. Elle implémente les couches déjà définies dans le GDD : squelette, tissu politique, puis distribution des secrets. Elle doit varier les règles et les relations cachées, pas seulement les noms et la géographie.

## Prochaine action recommandée

Créer une sous-tâche de production pour la Tranche 1 : **« Stabiliser la validation du socle et la commande de test unique »**. Une fois terminée, créer la sous-tâche du vertical slice. Il est inutile de lancer la génération procédurale ou d'écrire un grand catalogue avant ces deux preuves.

## Décisions à préserver

- Le monde sans pair reste un réglage de test, autour d'une partie sur six ou sept, et non une promesse immuable.
- Le joueur compose le pool de serviteurs ; les valeurs effectives restent tirées par partie.
- Les compétences achètent des capacités, jamais des traits.
- Toute modification de conception ou de réglage reçoit un rapport dédié.
