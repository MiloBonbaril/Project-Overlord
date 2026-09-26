# Game Design Document — Project Overlord

**Révision :** 8
**Statut :** concept stabilisé, prêt pour la production du vertical slice  
**Langue de référence :** français

## 1. Vision

Project Overlord est un jeu de stratégie narrative, de diplomatie et de gestion de serviteurs. Le joueur incarne une puissance invisible qui dirige un territoire depuis une salle du conseil. Il ne contrôle pas directement les personnes : il formule des ordres, compose un cercle de serviteurs et apprend à lire leurs décisions, leurs rapports et leurs omissions.

La fantasy centrale est celle du pouvoir mal informé. Le joueur dispose de la force nécessaire pour agir, mais jamais de toutes les informations nécessaires pour savoir si l'action est sage. Une partie réussie ne consiste donc pas à trouver une solution optimale unique : elle consiste à interpréter des personnalités, des rapports incomplets et des intérêts contradictoires, puis à assumer les conséquences.

## 2. Piliers de design

### 2.1 Le brouillard de puissance

Le joueur est puissant mais mal renseigné. Les secrets, rapports, rumeurs et intentions ne sont pas tous exposés dans l'interface. La découverte d'un monde ou d'une relation cachée doit rester significative d'une partie à l'autre ; la génération procédurale varie donc les règles et les rapports de force, pas seulement les noms et la géographie.

### 2.2 Des serviteurs zélés, pas des unités

Le joueur compose qui peut se présenter devant lui, mais ne fixe jamais la valeur exacte de la personne qui se présente. Les huit figures livrées sont des personnalités reconnaissables dont les traits sont tirés dans des enveloppes à chaque partie. Un joueur peut créer ses propres figures ou utiliser les figures par défaut.

Activer une figure ne la convoque pas automatiquement : cela l'autorise à entrer dans le pool de candidats. Le tirage conserve l'inconnu, avec un plancher de huit candidats générés sur quinze en mode normal. Un mode bac à sable peut lever ce plancher pour tester une composition précise.

### 2.3 Les conséquences sont des faits

Une situation produit des faits, des effets sur le monde et un rapport. Elle ne modifie jamais directement le serviteur qui la traverse. La foi, la fatigue, la réputation et les systèmes de rapport lisent les faits séparément. Cette séparation empêche une situation de devenir un raccourci pour révéler ou réécrire une personnalité.

## 3. Boucle de jeu

Une partie suit cette boucle :

1. le conseil présente une situation et plusieurs options ;
2. le joueur choisit une option et précise éventuellement une clause ;
3. un serviteur interprète l'ordre selon ses traits, son aptitude et sa lecture de la situation ;
4. l'action est résolue avec score, bruit et audace ;
5. le monde reçoit des effets et des faits ;
6. le joueur reçoit un rapport partiel, avec la possibilité d'une omission ;
7. les conséquences modifient les conseils suivants.

Les décisions sont déterministes à seed fixée, mais comportent une part d'incertitude contrôlée. L'élagage empêche un serviteur de renverser un très grand écart par simple bruit ; l'audace permet à un ordre vague d'être interprété avec davantage de liberté. Le réglage de température est T = 2 + 14M, où M est la marge d'interprétation.

## 4. Personnalités et recrutement

Chaque figure possède cinq traits sous forme d'enveloppes : zèle, initiative, cruauté, franchise et un trait de contexte défini par le format. Une enveloppe décrit une plage, pas une valeur connue du joueur. La somme des largeurs des enveloppes ne peut jamais être inférieure à 230 points sur 500. La franchise doit en plus couvrir au moins deux paliers effectifs d'aveu.

Les aptitudes donnent une identité mécanique aux titres : chaque serviteur a une aptitude majeure et une aptitude mineure. Les points de composition achètent des compétences, jamais des traits. Les figures de référence sont Yldra, Corvin, Aldemar, Nesque, Tessia, Vharn, Orine et Brannoc.

Le joueur peut sélectionner les figures qu'il autorise dans le vivier et en créer de nouvelles. Le système choisit ensuite les candidats présentés. La sélection contrôle l'espace des possibles ; elle ne transforme pas le jeu en menu de recrutement parfaitement prévisible.

## 5. Rapports, aveu et couture d'omission

La franchise gouverne les paliers d'aveu. Un registre de voix est payé une fois par figure, jamais par situation, afin de donner une voix identifiable sans multiplier le coût d'écriture du catalogue.

Un registre marqué peut remplacer un fait tu par une couture : une formule creuse qui signale qu'il manque quelque chose sans indiquer quoi. Cette couture n'est pas une preuve, car elle apparaît aussi dans 35 à 50 % des rapports où rien n'a été caché. En contrepartie, une couture ajoute 10 points au coût d'aveu de chaque fait : elle rend l'omission visible mais rend aussi les aveux plus difficiles.

## 6. Situations et format de contenu

Le catalogue sépare strictement les mots des nombres : l'auteur écrit la prose et pose des étiquettes ; le concepteur définit les valeurs numériques dans contenu/reglages/. Une situation décrit ses conditions, ses options, ses clauses, ses effets et ses rapports sans nommer de trait caché.

Les conditions ne peuvent pas cibler les traits des serviteurs, les pairs, l'archétype du monde ou la cause d'une anomalie : une situation ne doit jamais révéler gratuitement ce que le générateur est censé cacher. Les champs en lecture seule sont refusés par le linter. La prose ne doit pas annoncer une quantité simulée, même écrite en toutes lettres.

Le contrat est vérifié par le linter normatif R0 à R12 : chargement, schéma, étiquettes, chemins, opérateurs, valeurs, rôles, effets, lecture seule, clauses et prose chiffrée. L'exemple canonique est le test d'acceptation : s'il échoue, c'est la règle qui doit être corrigée avant l'exemple.

## 7. Génération procédurale

La génération se fait en trois couches :

1. **squelette** — lieux, distances en ticks, nations et ressources ;
2. **tissu politique** — opinions, alliances, tensions et rapports de force ;
3. **distribution du secret** — paires cachées, intentions et anomalies.

La géographie sert principalement de graphe de distances : l'écran principal est la salle du conseil, pas une carte à contempler. Cinq archétypes de monde font varier les règles de distribution. Le monde sans pair doit apparaître environ une partie sur six ou sept (réglage initial : 15 %, sujet aux tests).

Le nombre de pairs est variable et peut être nul. Les noms, les lieux et les situations portent le ton écrit à la main ; la génération porte l'incertitude structurelle qui rend ce ton rejouable.

### 7.1 Invariants de génération

Les valeurs suivantes sont le contrat d'implémentation de la Tranche 4. Elles lèvent les ambiguïtés de l'ancienne formulation sans ajouter de mécanique.

| Invariant | Valeur retenue | Règle opérationnelle |
|---|---:|---|
| Nations | 3 | Les trois nations sont non vides et le graphe des localités est connexe. |
| Lieux frontaliers | 4 | Un lieu est frontalier s'il est adjacent à une localité d'une autre nation. La génération utilise des blocs simples ; elle produit donc 4 lieux frontaliers exactement, avec au moins une connexion entre chaque paire de nations nécessaire à la connexité. |
| Lieux de l'archétype « Terres riches » | 10 | Chaque lieu reçoit entre 1 et 3 instances de ressource inclusivement. |
| Ressources de « Terres riches » | 10 à 30 | Le total est la somme des instances par lieu ; la borne basse est imposée par les 10 lieux et la borne haute par 3 ressources sur chacun. Il n'existe pas de lieu sans ressource dans cet archétype. |
| Quota sans pair | 3 mondes sur 20 | `index_de_monde = 0` pour le premier monde de la session, puis incrément de 1 à chaque monde généré. Le monde est sans pair si `index_de_monde mod 20 ∈ {0, 1, 2}`. La seed de session initialise le générateur, mais ne détermine pas le quota. |

Le choix de 4 lieux frontaliers conserve l'hypothèse de blocs simples : deux lieux ne peuvent pas relier trois blocs non vides tout en donnant à chaque nation une frontière conforme à la définition ci-dessus. Le quota est évalué sur l'index de génération, jamais sur `floor(seed_de_session / 20)` ; sur toute fenêtre alignée de 20 mondes, exactement 3 sont donc sans pair, soit 15 %.

## 8. Première tranche de production

La première tranche ne teste pas encore la rejouabilité. Elle teste si une partie unique est intéressante :

- 6 à 10 situations ;
- les 8 figures livrées et le vivier généré ;
- la boucle conseil → résolution → rapports ;
- une seed reproductible et un journal de partie ;
- validation automatique des réglages, figures et catalogue.

La génération procédurale complète vient après cette preuve de plaisir. Son format de données est toutefois contractuel dès maintenant, afin d'éviter de réécrire le catalogue au moment de l'intégrer.

## 9. Références du dépôt

- [Plan de production](plan-suite-production.md)
- [Tranche jouable](vertical-slice.md)
- [Rapport du linter](rapport-linter-catalogue.md)
- [Brief du linter](brief-linter-catalogue.md)
- [Figures](../contenu/figures/)
- [Réglages normatifs](../contenu/reglages/)
- [Catalogue de situations](../contenu/catalogue/)
