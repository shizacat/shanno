# Development

Django application structure folder:

- annotation - main application for annotation
- server - settings project
- templates - the base templates project

A set of used tools and library:

- Django
- Buefy (Bulma for Vue) v0.8.20 (only js and custom scheme)
  - For CSS used scheme: [flatly](https://unpkg.com/bulmaswatch@0.8.1/flatly/bulmaswatch.min.css)
- Vue 2.6.10
- Vue Router 3.1.3
- axios 0.19.0
- Font Awesome 5.10.2

## Translation

Dependens: package **gettext**

```bash
# root folder
# create po file
python3 manage.py makemessages -l ru
# create mo file
python3 manage.py compilemessages
```

## Run dev container

First, you need to download git repository.

```bash
git clone https://github.com/shizacat/shanno.git
```

Branches:
- master - this current stable version;
- dev - development branch. It contains current new future.

Then from root directory you create docker image and run him.

```bash
# Or use option 'f': -f contribute/compose-dev/docker-compose.yml
cd contribute/compose-dev/
docker-compose build
docker-compose run web migrate
docker-compose run web ensure_adminuser \
	--username admin \
	--password admin \
	--email admin@admin
docker-compose up -d
sudo docker-compose ps
```
