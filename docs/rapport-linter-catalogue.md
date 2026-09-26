# Rapport d’implémentation du linter de catalogue

Commande reproductible :

```sh
python3 -m unittest outils/tests-verifie-catalogue.py
python3 outils/verifie-catalogue.py contenu/catalogue --reglages contenu/reglages
```

Le linter charge uniquement les réglages normatifs, dérive les chemins, types,
valeurs, champs en lecture seule et grandeurs inscriptibles de `monde.json`, puis
applique R0 à R12. Chaque diagnostic est strictement formé de trois lignes :
emplacement, problème et correction.

## Ambiguïtés constatées

Le brief ne donne ni exemple de structure JSON de situation, ni liste littérale
des champs obligatoires et messages annoncés comme « exacts ». L’implémentation
rend donc explicite, sans changer les règles de jeu, le plus petit contrat
compatible avec les douze règles : `id`, `nom`, `roles`, `conditions`, `options` ;
une option porte `id`, `nom`, `etiquettes`, `effets`, `prose` et éventuellement
`interdit_par`. Une condition porte `chemin`, `operateur`, `valeur`, un effet
porte `cible`, `sens`, `ampleur`. Cette convention doit être confirmée par Milo
avant production d’un catalogue étendu.
