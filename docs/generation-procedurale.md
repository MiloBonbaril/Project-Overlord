# Génération procédurale — invariants d'implémentation

`outils/generation_monde.py` applique le contrat du GDD en trois flux pseudo-aléatoires indépendants, dérivés de la seed : `squelette`, `politique` et `secret`. Une modification d'une couche ne consomme donc pas les tirages des autres. La version du générateur fait partie de la dérivation.

Le squelette est un graphe non orienté connexe, borné en degré et en poids. Les nations occupent des blocs contigus. Chaque archétype possède exactement trois nations et quatre lieux frontaliers. Les cinq archétypes fixent leurs autres cardinalités et distributions propres. La correction BON-18 prévaut : « Terres riches » possède dix lieux ayant chacun une à trois ressources, soit dix à trente instances.

Le tissu politique conserve les scores bruts dans `monde_testeur` et ne publie que leur projection qualitative. Les relations sont stockées une fois par paire non orientée : alliance et guerre déclarée sont exclusives, avec les bornes de tension du GDD.

Les secrets utilisent l'index fourni par l'appelant. `index % 20 in {0, 1, 2}` produit exactement trois mondes sans pair par fenêtre alignée de vingt. Paires, intentions, tensions, puissances, archétype et anomalies non observables sont absents de `monde`; ils ne sont jamais représentés par `null`. `monde_testeur` contient le monde complet.

La boucle conseil → ordre → résolution → faits/rapports reste inchangée. `joue-partie.py` accepte `--index-monde`; le JSON final contient les projections `monde` et `monde_testeur`. La reproductibilité vaut pour une même seed, un même index et une même version.

Vérification : `python3 outils/teste-suite.py`. La suite génère deux fois vingt seeds, impose exactement 3/20 sans pair, vérifie leur distinction canonique, atteint les cinq archétypes et teste la non-fuite ainsi qu'un rejet du validateur.
