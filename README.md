# TEMPO ESS : dynamic ESS for EDF TEMPO

This code is for French Users that have an installation
with Multiplus-II, ESS, Battery AND have access to EDF TEMPO 
electricity contract.

Since this mostly for French users only the rest of the doc is only
in French

*French only*

Ce code permet de régler de façon semi dynamique votre installation
Victron Energy avec un (ou des) Multiplus-II, ESS et EDF TEMPO (ou 
équivalent ex EDF ZenFlex, à voir si les jours ZenFlex correspondent
au jours rouges de TEMPO).

*ATTENTION*: Code en cours de developpement.

## Installation

Vous avez besoin d'un installation qui fonctionne avec :

- Victron Energy Multiplus-II
- Batterie correctement configurée
- Des panneaux solaires (pas nécessaire mais ça aide a passer quand il y a du soleil)
- Un GX quelconque (soit intégré, soit Gerbo, soit home made)
- Une machine Linux/FreeBSD (l'installation sur le Venus OS sera a *vos propres risques*).

## Trucs en plus

- Un EcoDevice v1 (pas le RT2, pas conseillé)

Cet outil permet de trouver les informations de téléinformation de 
façon indépendante de l'internet.

- Un compte prowl pour envoyer les notifications de changement de tarifs

A noter que le code se basant sur l'API EDF et/ou Enedis *n'est pas* fini.

## Fonctionnement / Idée

Dans tempo nous avons 3 type de jours où les Heure Pleines qui sont de 6h à 22h
sont variablement plus ou moins chères (a voir s'il existe des abo TEMPO où
les heures pleines sont en dehors de la plage horaire 6h -> 22h).

L'idée est d'utiliser le chargeur du Multiplus pour recharger la batterie et
utiliser l'ESS associé pour moins manger d'heures pleines dans les plages
BLANCHES et ROUGES.

### Jour BLEU

C'est le tarif moins cher donc on est en mode "openbar" :

- Recharge de la batterie si SOC < 80% en heure creuse (nécessite un schedule 0 dans le GX)
- Battery Life : On, car lorsque la batterie n'est pas rechargée souvent il y a une charge lente qui peux arriver
- Min Soc : 30% (configurable)


### Jour BLANC

Le tarifs est un peu plus cher en heures pleines donc on vas limiter la conso 
le matin (machine a café, grille pain,...)

- Recharge de la batterie à 90% sur schedule 0
- Batterie Life : On
- Min Soc : 30%

Pareil que les jours blanc, j'ai dans la todo d'ajouter un plage horaire
où on peux fermer un relais, pour informer ma pompe à chaleur dois passer
sur le backup Gaz pour la préchauffe du circuit d'eau chauffage.
*Pour l'instant*: le code en question n'existe pas.

### Jour ROUGE

- Recharge de la batterie à 100% sur schedule 0
- Batterie Life : Off
- Min Soc : 25%

Dans ce avoir la batterie à 100% avec battery life off, permet de
rester sur batterie jusqu'au SoC Minimal. En pratique sans soleil
chez moi, je suis de 6h à 16h sans toucher un seul kWh HP rouge.
S'il y a du soleil, j'arrive largement à rester toute les HP sans consommer 
du réseau.

TODO: PAC OFF en HP ROUGE

