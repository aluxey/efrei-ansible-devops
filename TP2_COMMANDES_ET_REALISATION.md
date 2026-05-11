# TP2 DevOps S8 - Commandes et realisation

Ce document resume les commandes utiles pour lancer et verifier le projet, puis explique ce qui a ete fait pour chaque partie obligatoire du TP.

## 1. Prerequis

Verifier les outils necessaires :

```bash
python3 --version
vagrant --version
vboxmanage --version
```

Le TP utilise :

- Python pour Ansible, Molecule et les tests
- Vagrant + VirtualBox pour lancer la VM Molecule
- Ansible pour configurer l'infrastructure
- Molecule + Testinfra pour tester le deploiement

## 2. Installation de l'environnement local

Depuis la racine du depot :

```bash
source venv.sh
```

Cette commande cree ou active l'environnement virtuel Python du projet et installe les dependances de `requirements.txt` si besoin.

Pour reconstruire completement l'environnement :

```bash
rebuild_env
```

Installer les roles et collections Ansible :

```bash
download_galaxy
```

Equivalent manuel :

```bash
ansible-galaxy role install -r roles/requirements.yml -p .ansible/roles --force
ansible-galaxy collection install -r collections/requirements.yml -p .ansible/collections --force
```

## 3. Commandes de verification

Verifier la syntaxe du playbook :

```bash
ansible-playbook -i hosts/hosts_dev playbook_install.yml --syntax-check
```

Lancer le linter Ansible :

```bash
ansible-lint -c .ansible-lint.yml
```

Lancer le linter Python :

```bash
flake8 -v
```

Verifier l'etat Git avant rendu :

```bash
git status --short
```

## 4. Lancer le projet avec Molecule

Le scenario Molecule utilise Vagrant + VirtualBox pour creer une VM Ubuntu, puis applique le playbook Ansible.

Creer la VM :

```bash
molecule create
```

Appliquer le playbook sur la VM :

```bash
molecule converge
```

Lancer les tests Testinfra :

```bash
molecule verify
```

Lancer le cycle complet, avec test d'idempotence :

```bash
molecule test
```

Se connecter a la VM si besoin :

```bash
molecule login -h devops-dev-1
```

Supprimer la VM :

```bash
molecule destroy
```

## 5. Lancer le playbook Ansible directement

Pour un deploiement sur une vraie machine, adapter d'abord `hosts/hosts_dev` avec l'adresse de la machine cible et les parametres SSH.

Puis lancer :

```bash
ansible-playbook -i hosts/hosts_dev playbook_install.yml
```

Avec un utilisateur SSH specifique :

```bash
ansible-playbook -i hosts/hosts_dev -u devops playbook_install.yml
```

Avec demande du mot de passe sudo :

```bash
ansible-playbook -i hosts/hosts_dev -u devops --ask-become-pass playbook_install.yml
```

## 6. Lancer l'application seule, hors Ansible

Cette partie sert seulement a tester l'application Flask localement. Il faut avoir une base PostgreSQL disponible avec une base `devops_quotes` et un utilisateur `devops_api`.

Creer un virtualenv temporaire :

```bash
python3 -m venv .tmp-app-venv
source .tmp-app-venv/bin/activate
```

Installer les dependances applicatives :

```bash
pip install -r roles/app/files/devops_api/requirements.txt
```

Exporter la configuration :

```bash
export APP_NAME=devops_quote_api
export APP_MESSAGE="API de demonstration deployee avec Ansible"
export APP_QUOTE_SEED="Infrastructure as code, livree proprement."
export DATABASE_URL="postgresql://devops_api:devops_api_password@127.0.0.1:5432/devops_quotes"
```

Demarrer l'application :

```bash
python roles/app/files/devops_api/app.py
```

Tester les endpoints :

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/db-health
curl http://127.0.0.1:5000/
```

## 7. Travail obligatoire realise

### 7.1 Choix de l'application a deployer

L'application choisie est `DevOps Quote API`.

C'est une API HTTP minimaliste ecrite avec Flask. Elle utilise PostgreSQL pour stocker une table `quotes` et expose trois routes :

- `/` : retourne le nom du service, un message et le nombre de citations en base
- `/health` : verifie que l'API repond
- `/db-health` : verifie que la connexion PostgreSQL fonctionne avec un `SELECT 1`

Le code source est dans :

```text
roles/app/files/devops_api/app.py
```

L'application est lancee en production par `gunicorn`, via un service systemd.

### 7.2 Structure du projet Ansible

Le projet est structure en roles Ansible, avec une responsabilite par role :

```text
roles/
|-- runtime/
|-- app/
|-- webserver/
`-- database/
```

Les variables sont separees par contexte :

```text
group_vars/
|-- all.yml
|-- api.yml
|-- database.yml
`-- devops_dev/
    `-- vars.yml
```

Le playbook principal est :

```text
playbook_install.yml
```

Il applique les roles dans cet ordre :

1. `database` sur le groupe `database`
2. `runtime` et `app` sur le groupe `api`
3. `webserver` sur le groupe `nginx`

### 7.3 Role/Task : runtime applicatif

Le role `runtime` installe les paquets systeme necessaires pour executer une application Python :

```text
roles/runtime/tasks/main.yml
```

Il installe :

- `python3`
- `python3-pip`
- `python3-venv`

Ce role prepare donc l'interpreteur, le gestionnaire de paquets Python et la possibilite de creer un environnement virtuel.

### 7.4 Role/Task : deploiement de l'application

Le role `app` deploie et configure l'application :

```text
roles/app/tasks/main.yml
```

Il realise les actions suivantes :

- creation d'un groupe systeme dedie
- creation d'un utilisateur systeme dedie `devopsapp`
- creation des dossiers applicatifs dans `/opt/devops_quote_api`
- copie du code source Flask dans `/opt/devops_quote_api/current`
- installation des dependances Python dans un virtualenv
- generation du fichier d'environnement depuis un template Jinja2
- generation du service systemd depuis un template Jinja2
- activation et demarrage du service `devops_quote_api`

Les templates utilises sont :

```text
roles/app/templates/app.env.j2
roles/app/templates/app.service.j2
```

Le service lance l'application avec `gunicorn` sur `127.0.0.1:5000`.

### 7.5 Role/Task : serveur web nginx

Le role `webserver` configure nginx comme reverse proxy devant l'application :

```text
roles/webserver/tasks/main.yml
```

Il realise les actions suivantes :

- installation du paquet `nginx`
- suppression du site nginx par defaut
- generation du vhost applicatif depuis un template Jinja2
- activation du vhost dans `sites-enabled`
- verification de la configuration avec `nginx -t`
- activation et demarrage du service nginx

Le template Jinja2 est :

```text
roles/webserver/templates/app.conf.j2
```

Il utilise des variables pour rendre la configuration adaptable :

- `app_public_port` : port public nginx, actuellement `80`
- `nginx_server_name` : nom de domaine ou serveur, actuellement `_`
- `nginx_client_max_body_size` : taille maximale des requetes
- `app_bind_host` : adresse interne de l'application, actuellement `127.0.0.1`
- `app_port` : port interne de l'application, actuellement `5000`

Nginx ecoute donc sur le port `80` et redirige vers Gunicorn sur `127.0.0.1:5000`.

### 7.6 Role : base de donnees

Le role `database` installe et configure PostgreSQL :

```text
roles/database/tasks/main.yml
```

PostgreSQL a ete choisi car l'application Flask utilise la bibliotheque `psycopg` pour se connecter a une base relationnelle.

Le role realise les actions suivantes :

- installation des paquets PostgreSQL
- installation du paquet Python systeme necessaire aux modules Ansible PostgreSQL
- activation et demarrage du service `postgresql`
- creation de l'utilisateur applicatif `devops_api`
- creation de la base `devops_quotes`
- attribution de la base a l'utilisateur applicatif

Les modules utilises sont ceux de la collection maintenue `community.postgresql` :

- `community.postgresql.postgresql_user`
- `community.postgresql.postgresql_db`

Le mot de passe est masque dans les logs Ansible avec `no_log: true`.

### 7.7 Tests Molecule

Les tests sont ecrits avec Testinfra dans :

```text
molecule/default/tests/test_app.py
```

Ils verifient :

- que nginx est actif et active au demarrage
- que PostgreSQL est actif et active au demarrage
- que le service `devops_quote_api` est actif et active au demarrage
- que nginx ecoute sur le port `80`
- que l'application ecoute sur `127.0.0.1:5000`
- que `/health` repond correctement via nginx
- que `/db-health` valide la connexion PostgreSQL
- que la base `devops_quotes` existe

Commande principale :

```bash
molecule test
```

Cette commande lance le cycle complet : creation de la VM, converge, verification de l'idempotence, tests et destruction.

### 7.8 Qualite du code : ansible-lint et flake8

Le projet est verifie avec `ansible-lint` :

```bash
ansible-lint -c .ansible-lint.yml
```

Resultat obtenu :

```text
Passed: 0 failure(s), 0 warning(s)
```

Le code Python est verifie avec `flake8` :

```bash
flake8 -v
```

Resultat obtenu :

```text
Found a total of 0 violations and reported 0
```

Les tasks Ansible utilisent les FQCN, par exemple :

- `ansible.builtin.apt`
- `ansible.builtin.file`
- `ansible.builtin.template`
- `ansible.builtin.systemd_service`
- `community.postgresql.postgresql_user`
- `community.postgresql.postgresql_db`

## 8. Etat actuel hors bonus

Le travail obligatoire est couvert :

- application HTTP choisie et documentee
- structure en roles
- runtime Python installe
- application Flask deployee avec systemd
- nginx configure avec un template Jinja2
- PostgreSQL installe et configure
- tests Molecule/Testinfra ajoutes
- linters `ansible-lint` et `flake8` valides

Les bonus ne sont pas traites dans ce document.
