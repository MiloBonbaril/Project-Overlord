# Spec — interface lisible de la première partie

**Tranche :** 5 — lisibilité de l’interface et brouillard  
**Statut :** contrat de présentation pour l’implémentation existante  
**Périmètre :** présenter la boucle conseil → ordre → résolution → rapport, sans nouvelle mécanique.

## Intention et boucle cœur

Le joueur doit pouvoir répondre à la question « que m’a conseillé ce serviteur,
qu’ai-je ordonné et qu’est-ce que je sais réellement ? » en moins de 10 secondes
par tour. La boucle cœur est : **lire deux conseils, choisir un ordre, mesurer
l’écart entre intention et résultat, puis décider quoi croire au tour suivant**.

Émotion visée (MDA) : **mécanique** — choix explicite et rapport partiel ;
**dynamique** — interprétation sous incertitude ; **esthétique** — autorité
calme, doute et responsabilité. Le brouillard est une information absente,
jamais une information fausse.

## Contrat d’écran

La présentation doit rester utilisable sans ouvrir `contenu/` ni lire le journal
testeur. Les données de `journal_testeur`, `score_max`, `score_choisi`, `ecart`,
`etat_avant`, `etat_apres` et `ampleurs` sont interdites dans la vue joueur.

| Zone | Contenu visible | Hiérarchie / règle |
|---|---|---|
| En-tête | `Tour n/8`, seed, composition du vivier | état global, toujours visible ; la seed est copiable pour relancer |
| Conseil | situation, nom du serviteur, 2+ cartes d’options avec libellé et score arrondi | le libellé est primaire ; score secondaire ; option interdite grisée et étiquetée « interdite par la clause » |
| Ordre | boutons d’option, clauses disponibles, bouton `Résoudre` | aucun ordre implicite ; `Résoudre` désactivé tant qu’une option valide n’est pas choisie |
| Résolution | action retenue, état verbal (`adhésion`, `réserve`, `résistance`) | une seule carte de résultat ; ne pas afficher le score caché ni l’écart numérique |
| Rapport | texte du serviteur, faits connus ou bandeau « non établi dans le rapport » | les faits omis ne doivent pas apparaître ailleurs dans ce tour |
| Monde connu | uniquement les états exposés par le rapport | mise à jour après résolution ; une omission ne modifie pas l’état connu |
| Actions de session | `Relancer la même seed`, `Nouvelle seed`, `Quitter` | visibles en fin de partie et dans le menu pause ; la relance conserve la composition choisie |

Lisibilité (contrainte de direction artistique) : fond sombre uni, panneaux
rectangulaires, une couleur d’accent pour l’action sélectionnée, une couleur
d’alerte pour l’interdit, une couleur de réserve pour l’information incomplète.
Pas d’illustration originale requise : silhouettes, icônes texte et formes
géométriques suffisent. Contraste cible : texte normal ≥ 4,5:1 ; alerte et
sélection ne reposent jamais sur la couleur seule.

## États et transitions

1. **Début** — afficher seed, vivier, `Lancer la partie`. Aucun fait de la
   partie n’est encore visible. Une seed manquante prend la seed par défaut
   existante ; elle doit rester affichée.
2. **Conseil / tour** — afficher la situation et toutes les options légales.
   Le joueur choisit exactement une option et zéro ou plusieurs clauses
   autorisées. Double-clic ou clic répété : aucun effet supplémentaire.
3. **Résolution** — verrouiller les contrôles pendant la résolution ; afficher
   l’action retenue et le libellé de résolution. Durée cible : 300–600 ms,
   puis passage manuel à `Voir le rapport`.
4. **Rapport** — afficher le texte et les faits connus. Si `fait_omis=true`,
   afficher seulement la couture narrative déjà produite et
   « Fait non établi dans ce rapport » ; ne jamais afficher le fait testeur.
   Le bouton `Conseil suivant` devient actif après lecture de la carte.
5. **Fin** — après 8 tours ou absence de situation, afficher le résumé des
   décisions visibles, la seed et deux actions : rejouer la même seed ou
   relancer avec une nouvelle seed. Aucun état testeur ne doit être injecté
   dans le résumé.
6. **Relance** — confirmer la perte de la partie courante, puis réinitialiser
   le monde connu, les tours et les rapports. La même seed doit produire le
   même journal pour les mêmes choix ; une nouvelle seed doit être visible.

## Mapping des données vers la vue

La sortie actuelle de `outils/joue-partie.py` fournit déjà le contrat minimal :
`journal` pour la vue joueur et `journal_testeur` pour l’outillage de test.
L’adaptateur de scène ne consomme que :

```text
seed, tours, figures_du_vivier, monde,
journal[].tour, situation, serviteur, conseil, clauses, action,
journal[].resolution_probable, journal[].rapport, journal[].faits,
etat_final
```

Il doit refuser ou ignorer explicitement les champs testeur plutôt que les
afficher par défaut. Le texte `faits=[]` est ambigu pour une omission : la vue
doit utiliser la présence de la couture dans `rapport` et afficher
« non établis dans le rapport », jamais « aucun effet ».

## Critères d’acceptation

- Un joueur peut lancer une partie, choisir une option et une clause, résoudre
  8 tours et relancer une seed sans consulter les fichiers de données.
- À chaque tour, l’option sélectionnée, l’action résolue et le rapport sont
  distinguables en un regard ; aucun bouton ne déclenche une résolution deux
  fois.
- Une option interdite est non sélectionnable et sa raison est visible.
- Une omission apparaît comme information incomplète : le fait n’est ni dans
  la carte joueur, ni dans le résumé, ni dans l’état connu.
- Les champs `score_max`, `score_choisi`, `ecart`, `ampleurs`, `etat_avant`,
  `etat_apres` et `fait_omis` n’apparaissent jamais dans la vue joueur.
- Même seed + mêmes choix = même suite visible ; `Relancer la même seed` remet
  l’état initial et la composition, sans conserver un rapport précédent.
- La commande de non-régression `python3 outils/teste-suite.py` et les 7 tests
  ciblés de `outils/tests-joue-partie.py` passent.

## Frictions et décisions de portée

- **Constat vérifié :** la boucle Python interactive et la séparation joueur /
  testeur sont déjà présentes ; les tests ciblés passent (7/7) et la suite
  complète passe (16 tests catalogue, réglages et figures).
- **Friction de présentation :** le CLI affiche actuellement des identifiants
  techniques (`situation`, ids d’options) et mélange conseil, clause, action et
  rapport dans un flux texte. L’adaptateur doit les regrouper selon les zones
  ci-dessus ; ce n’est pas une nouvelle règle.
- **Coupe explicite :** pas de portraits, animation originale, carte du monde,
  journal historique riche ni nouveaux indicateurs. Leur coût est visuel/UI et
  ils dilueraient le brouillard ; placeholders et formes simples suffisent.
- **Prochaine action :** Kit intègre ce contrat dans la scène choisie par le
  plan technique, puis Vera exécute le test utilisateur de lisibilité sur les
  deux compositions `yldra,corvin` et `orine,tessia`.
