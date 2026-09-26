# Spec — écart de résolution du serviteur

**Statut :** validée par l'utilisateur le 26/09/2026 ; prête à être découpée pour implémentation
**Source :** observation BON-13, partie jouable de la Tranche 3

## Intention

Faire sentir le serviteur dans la boucle conseil → ordre → conséquence : le
joueur garde le dernier mot, mais un ordre très éloigné de la lecture du
serviteur coûte en efficacité. L'émotion visée est le doute stratégique :
« est-ce que je suis son conseil, ou est-ce que la situation m'oblige à le
contredire ? »

## Règle proposée

Pour chaque tour, le moteur calcule les scores déterministes de toutes les
options, avant bruit. Soit `Smax` le meilleur score admissible après prise en
compte des clauses, et `Schoisie` le score de l'ordre choisi par le joueur.

`écart = Smax - Schoisie`, arrondi uniquement pour l'affichage. Le moteur
compare la valeur réelle.

| Écart réel | État de résolution | Effet de chaque effet choisi |
| ---: | --- | --- |
| `0 ≤ écart ≤ 8` | adhésion | ampleur prévue dans le catalogue |
| `8 < écart ≤ 20` | réserve | ampleur réduite d'un palier |
| `écart > 20` | résistance | ampleur réduite de deux paliers |

Les paliers sont `nul < faible < moyen < fort < total`. Une réduction est
bornée à `nul`. L'ordre choisi reste toujours l'ordre exécuté : le serviteur
ne remplace jamais la décision du joueur par son option préférée.

Les clauses sont appliquées avant le calcul de `Smax`. Une option interdite
ne peut donc pas devenir une « résistance » : elle reste invalide, comme dans
la tranche actuelle.

## Indice joueur

Après la sélection, avant la résolution, le journal affiche une ligne courte :

- `Adhésion probable` pour 0–8 ;
- `Réserve probable` pour 8–20 ;
- `Résistance probable` au-delà de 20.

Le joueur voit aussi l'écart numérique (`écart 14,7`) dans le mode de test,
mais l'interface de jeu n'affiche que le libellé. Le résultat et le rapport
révèlent ensuite la réduction effective. Le libellé est un indice, pas une
promesse : l'intention est de rendre la personnalité lisible sans exposer ses
traits ni supprimer l'incertitude des enveloppes.

## Cas limites

- Deux options ex æquo : `Smax` est leur score commun ; choisir l'une ou
  l'autre donne `adhésion`.
- Une seule option admissible : `écart = 0`, même si son score est bas.
- Une clause rend l'option préférée invalide : `Smax` est recalculé parmi les
  options restantes ; le joueur n'est pas puni pour une option interdite qui
  n'est plus disponible.
- Une option avec plusieurs effets : la réduction s'applique à chacun, sans
  dépasser `nul`.
- Effet déjà `nul` : il reste `nul`.
- Choix répété ou choix sans `chosen` en mode JSON : comportement actuel
  conservé ; le moteur choisit automatiquement pour les scripts de test et
  calcule alors un écart nul ou quasi nul selon les clauses.
- En mode testeur, conserver `score_max`, `score_choisi`, `ecart` et les
  ampleurs avant/après dans `journal_testeur`. La vue joueur ne doit pas
  exposer les états cachés.

## Plage de test

Les premiers essais utilisent les seuils `[8, 20]`. Vera doit couvrir au
minimum des écarts de `0`, `5`, `10`, `20` et `25`, sur les deux compositions
`yldra,corvin` et `orine,tessia`, avec la même seed et la même situation.

Critère de sensation : sur cinq décisions, l'utilisateur doit pouvoir citer
au moins une conséquence qu'il attribue au serviteur plutôt qu'à la seule
option choisie. Critère de système : à situation et option identiques, deux
serviteurs doivent produire au moins deux états de résolution distincts dans
la matrice de test. Si ce n'est pas le cas, tester `[5, 15]` puis `[10, 25]`
avant toute nouvelle mécanique.

## Critères d'acceptation pour Kit

1. Une même situation, option et seed produisent un effet différent lorsque
   l'écart du serviteur change de tranche.
2. L'ordre choisi n'est jamais remplacé automatiquement.
3. Les clauses, les effets à `nul` et les effets multiples respectent les cas
   limites ci-dessus.
4. Le journal testeur contient les quatre valeurs de diagnostic ; le journal
   joueur n'expose ni trait ni fait caché.
5. Les tests existants de déterminisme, de choix et de brouillard passent.

## Coût et coupe

Estimation : faible, environ 3 à 5 heures de Kit, car la table réutilise le
score déjà calculé et les cinq paliers existants. Pour tenir le coût, on coupe
pour cette tranche la variation de texte du rapport selon l'état et toute
animation ou jauge dédiée. On ne touche ni à la génération procédurale, ni aux
traits, ni au catalogue.

Cette spec est une hypothèse de plaisir, pas une preuve : le verdict revient
au playtest utilisateur. La génération procédurale reste en attente de ce
test.

## Décision de validation

L'utilisateur valide l'hypothèse et les seuils `8/20`. La convention retenue
est donc : `écart ≤ 8` = effet complet, `8 < écart ≤ 20` = réduction d'un
palier, `écart > 20` = réduction de deux paliers. Milo doit découper
l'implémentation de cette règle pour Kit avant le rejeu Vera.
