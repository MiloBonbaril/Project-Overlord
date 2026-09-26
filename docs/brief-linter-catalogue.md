# Brief de production — linter du catalogue

Statut : prêt à déléguer  
Dépendances : `contenu/reglages/monde.json`, `contenu/reglages/ampleurs.json`, `contenu/reglages/etiquettes.json`, `contenu/reglages/bruit.json`, `contenu/reglages/prose.json`  
Propriétaire fonctionnel : Milo  
Recommandation : déléguer à un développeur Python familiarisé avec les validateurs JSON ; garder la revue fonctionnelle et les tests d’acceptation côté direction de projet.

## Objectif

Construire le linter qui transforme le format du catalogue en contrat exécutable. Il doit refuser toute situation qui serait soit impossible à tirer, soit capable de révéler une information cachée, soit ambiguë pour le moteur. Le linter ne rééquilibre pas les situations et ne réécrit pas leur prose.

Commande cible :

```text
python3 outils/verifie-catalogue.py contenu/catalogue [--reglages contenu/reglages]
```

Sortie : code `0` si le catalogue est valide, code `1` si au moins une erreur bloquante est trouvée, code `2` si les fichiers de réglage ou le catalogue sont illisibles. Chaque erreur doit tenir en trois lignes : où, quoi, quoi faire.

## Périmètre bloquant

Le premier lot doit couvrir les douze règles R du format déjà arrêté :

1. chargement JSON, encodage et racine attendue ;
2. identifiant de situation unique et nom lisible ;
3. présence et type des champs obligatoires ;
4. étiquettes connues, sans doublon ni étiquette vide ;
5. chemins de condition résolus dans `monde.json` ;
6. opérateurs compatibles avec le type et l’échelle ciblés ;
7. valeurs d’échelle et d’énumération connues ;
8. références de rôle et de cible résolues ;
9. grandeurs d’effet inscriptibles et amplitudes connues ;
10. refus des champs en lecture seule et des cibles interdites ;
11. clauses cohérentes avec les étiquettes qu’elles interdisent ;
12. prose ne déclarant pas de quantité simulée interdite (nombres en chiffres ou en lettres, avec le lexique et les groupes de grandeurs de `prose.json`).

Les refus de fuite doivent produire un message métier explicite. Exemples : un trait de serviteur, le nombre de pairs, l’archétype du monde ou la cause d’une anomalie ne sont pas de simples « champs inconnus » ; ils sont interdits parce qu’ils permettent au contenu de révéler l’information cachée.

## Ordre d’implémentation recommandé

1. chargeur et diagnostic commun ;
2. résolution des chemins et du schéma ;
3. validation des conditions ;
4. validation des effets et des cibles ;
5. règles de non-fuite ;
6. analyse de prose ;
7. CLI, codes de sortie et tests de régression.

Cet ordre permet d’obtenir rapidement des messages utiles : une erreur de chemin ne doit pas être masquée par une erreur secondaire de type.

## Critères d’acceptation

- L’exemple canonique du format passe les douze règles. S’il échoue, la règle est considérée fausse jusqu’à correction.
- Un jeu de tests contient au minimum un cas valide et un cas invalide par règle ; chaque cas vérifie le code de sortie et le message utile.
- Les chemins sont vérifiés contre le schéma, jamais contre une liste recopiée dans le linter.
- Les grandeurs d’effet sont dérivées du schéma et de la lecture seule ; aucune seconde liste manuelle ne doit diverger.
- Le linter ne lit jamais les valeurs numériques des figures ou des réglages de décision pour juger la validité narrative d’une situation.
- Ajouter une situation valide ne demande aucune modification du code du linter.

## Hors périmètre du premier lot

Pas de génération procédurale, pas d’équilibrage statistique, pas de validation stylistique du français, pas de test du moteur de résolution des choix et pas de correction automatique des fichiers. Ces sujets viendront après le contrat de format.

## Décision de pilotage

La prochaine action recommandée est une sous-tâche dédiée de deux à trois jours : « Implémenter le linter du catalogue et ses tests ». Elle doit livrer l’outil, son jeu de tests, un fichier d’exemple canonique et un court rapport listant toute ambiguïté découverte dans le format. Le rapport est obligatoire : comme pour le GDD, chaque modification du contrat doit être traçable avant l’écriture des situations.
