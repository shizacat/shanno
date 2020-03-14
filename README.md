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


# Translation

```bash
# create po file
python3 manage.py makemessages -l ru
# create mo file
python3 manage.py compilemessages
```