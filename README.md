# TP DevOps S8 - Ansible

Projet de deploiement Ansible pour le TP2 DevOps S8.
Le depot automatise l'installation d'une petite application web Python, d'une base PostgreSQL et d'un reverse proxy nginx.

## Application deployee

L'application choisie est `DevOps Quote API`, une API HTTP minimaliste ecrite avec Flask.
Elle expose :

- `/` pour afficher un message de presentation et le nombre de citations en base
- `/health` pour verifier que l'application repond
- `/db-health` pour verifier la connexion PostgreSQL

L'application est lancee via `gunicorn` comme service systemd, puis exposee par `nginx`.

## Membres

- A completer

## Bonus implementes

- Aucun pour le moment

## Structure du projet

```text
.
├── ansible.cfg
├── collections/
│   └── requirements.yml
├── group_vars/
│   ├── all.yml
│   ├── api.yml
│   ├── database.yml
│   └── devops_dev/
│       └── vars.yml
├── hosts/
│   └── hosts_dev
├── molecule/
│   └── default/
├── playbook_install.yml
├── roles/
│   ├── app/
│   ├── database/
│   ├── runtime/
│   ├── webserver/
│   └── requirements.yml
└── venv.sh
```

## Roles implementes

- `runtime` : installe Python, `pip` et `venv`
- `database` : installe PostgreSQL, cree l'utilisateur et la base applicative
- `app` : deploie le code Flask, installe les dependances Python, genere le fichier d'environnement et le service systemd
- `webserver` : installe nginx et genere la configuration de reverse proxy depuis un template Jinja2

## Mise en place locale

### 1. Activer l'environnement Python

```bash
source venv.sh
```

Le script gere maintenant aussi les chemins avec espaces et retombe sur `python3 -m venv` si `virtualenv` n'est pas installe.

### 2. Installer les roles et collections Galaxy

```bash
download_galaxy
```

### 3. Lancer un test de syntaxe

```bash
ansible-playbook -i hosts/hosts_dev playbook_install.yml --syntax-check
```

### 4. Lancer les linters

```bash
ansible-lint -c .ansible-lint.yml
flake8
```

## Tests Molecule

Commandes utiles :

```bash
molecule create
molecule converge
molecule verify
molecule test
```

Le scenario Molecule utilise Vagrant + VirtualBox et l'inventaire `hosts/hosts_dev`.

## Deploiement manuel de l'application seule

Pour lancer l'application manuellement hors Ansible :

1. Installer PostgreSQL et creer une base `devops_quotes` avec un utilisateur `devops_api`.
2. Installer les dependances Python :

```bash
python3 -m venv .tmp-app-venv
source .tmp-app-venv/bin/activate
pip install -r roles/app/files/devops_api/requirements.txt
```

3. Exporter les variables d'environnement :

```bash
export APP_NAME=devops_quote_api
export APP_MESSAGE="API de demonstration deployee avec Ansible"
export APP_QUOTE_SEED="Infrastructure as code, livree proprement."
export DATABASE_URL="postgresql://devops_api:devops_api_password@127.0.0.1:5432/devops_quotes"
```

4. Demarrer l'application :

```bash
python roles/app/files/devops_api/app.py
```

L'application ecoutera alors sur `127.0.0.1:5000`.

## Variables principales

Les variables du projet sont centralisees dans `group_vars/` :

- `group_vars/all.yml` : nom de l'application, ports, chemins, identifiants de base
- `group_vars/api.yml` : endpoints de verification
- `group_vars/database.yml` : paquets PostgreSQL
- `group_vars/devops_dev/vars.yml` : surcharge specifique a l'environnement de test

## Etat actuel

Le projet couvre le travail obligatoire suivant :

- runtime Python
- deploiement applicatif
- base de donnees PostgreSQL
- template Jinja2 pour nginx
- tests Testinfra/Molecule pour nginx, l'API et la base
- verification `ansible-lint`, `flake8` et `--syntax-check`

## Remarques

- Aucun secret n'est chiffre avec Ansible Vault pour l'instant
- Si VirtualBox est installe mais que les VMs ne demarrent pas, il peut etre necessaire de recharger le module noyau avec `sudo /sbin/vboxconfig`
- Si `vagrant` n'est pas installe, `molecule test` ne pourra pas lancer la VM de test
