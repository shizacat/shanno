# Разработка

Django application structure folder:
- annotation - основное приложение для анотирования.
- server - настройки проекта
- templates - базовые шаблоны проекта

Набор используемых инструментов и библиотек:
- Django
- Buefy (Bulma for Vue) v0.8.8
- Vue 2.6.10
- Vue Router 3.1.3
- axios 0.19.0
- Font Awesome 5.10.2


## Translation

```bash
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
- dev - development branch. He contants current new future.

Then from root directory you create docker image and run him.

```bash
docker-compose -f contribute/compose-dev/docker-compose.yml build
docker-compose -f contribute/compose-dev/docker-compose.yml run web migrate
docker-compose -f contribute/compose-dev/docker-compose.yml run web \
  ensure_adminuser --username admin --password admin --email admin@admin
docker-compose -f contribute/compose-dev/docker-compose.yml up -d
sudo docker-compose -f contribute/compose-dev/docker-compose.yml ps
```

