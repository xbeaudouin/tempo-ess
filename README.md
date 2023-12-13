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

- Recharge de la batterie si SOC < 80% en heure creuse (nécessite un schedule 1 dans le GX)
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

Le Battery Life à Off évite aussi de "charger lentement la batterie" quand
on est à Battery Life à On.


## Configuration du GX

Je ne vais pas expliquer comment configurer un Multiplus avec un GX en ESS mais les points
*IMPORTANT* a mettre en place.

### Activer le broker MQTT sur GX

Dans Settings -> Services, activez MQTT on LAN (SSL), _puis_ MQTT on LAN (Plaintext) :

![MQTT Settings](/img/gx-mqtt.png)

Pour l'instant le code ne prévois pas de se connecter en MQTT over SSL.

### Activer un schedule 1 sur le GX

Utilisé pour recharger les batteries en heures creuse, la valeur de recharge sera modifiée
selon les jours Bleu, Blanc et Rouge.

*Si vous ne voulez pas utiliser cette feature* il _suffit juste_ de laisser ce schedule a inactif.

Dans Settings -> ESS -> Scheduled charge levels -> Schedule 1 (capture prise en veille de jour Blanc) :

![Schedule 1](/img/schedule1.png)

![Schedule 1 Settings](/img/schedule1-settings.png)

## Configuration du code 

### Prerequis 

Il vous faut trouver les points suivants :

- L'ip ou le nom de votre eco device
- L'ip ou le nom de votre GX
- Le numéro de série du GX

*NOTE IMPORTANTE*: le code API EDF n'est pas encore fonctionnel. 

Sur les deux premier points, vous avez ces informations sur votre routeur, box, ou ailleurs. 
Je ne détaillerais pas comment retrouver ces point.

Pour le numéro de série c'est assez facile a coup de MQTT Explorer, vous le trouverez dans l'arbre `N/`, le
première serie de numeros est le numéro de série de votre GX.

### Configuration

Copiez le fichier `secret.py.exemple` en `secret.py` et remplissez les variables présentes.

### Ajout des modules python nécessaires

Le code a besoin des modules python suivants :

- urllib3
- json
- paho.mqtt.client
- time
- pyprowl
- datetime

Cette partie est a voir avec votre distribution linux.

## Comment faire un test ?

C'est assez simple vu tout se configure via MQTT, au lieu de mettre votre GX dans la varible `gx`de `secret.py`
utilisez un mosquitto de test pour voir si les valeur sont celles attendus. 
Une fois que vous êtes sûr alors vous pouvez mettre en crontab le fonctionnemnt de code.

Exemple :
```
#
# EDF TEMPO
#
# Lors de la recup jour demain
5	20	*	1-3,9-12	*	test -x $HOME/git/tempo-ess/tempo-ess-dynamic.py && $HOME/git/tempo-ess/tempo-ess-dynamic.py
# Lors du passage HC
2	22	*	1-3,9-12	*	test -x $HOME/git/tempo-ess/tempo-ess-dynamic.py && $HOME/git/tempo-ess/tempo-ess-dynamic.py
```

Donc le code est executé 2 fois: 
- une fois a 20:05, pour récuperer la couleur du lendemain et la valeur du Schedule 1
- une fois a 22:02, pour éventuellement changer la valeur du Min Soc et si on active/desactive Battery Life


