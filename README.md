FOODGRAM

1. python manage.py makemigrations users
2. python manage.py makemigrations recipes
3. python manage.py migrate
4. python manage.py load_ingredients

Фудграм

Описание проекта:
«Фудграм» — это сайт для публикации рецептов, добавления понравившихся рецептов в избранное и подписки на других авторов. Пользователи также могут воспользоваться функцией «Список покупок», которая помогает составить список продуктов, необходимых для выбранных блюд.

Технологии:
Python 3.9
Django==3.2.16
djangorestframework==3.12.4
nginx
djoser==2.1.0
Postgres

Что cделано:
В проекте Foodgram настроен запуск в контейнерах и автоматизация CI/CD через GitHub Actions. При каждом пуше в ветку master запускаются тестирование и деплой проекта, а по завершении деплоя в Telegram отправляется уведомление. Реализованы:

интеграция Python-приложения с внешними API-сервисами;
собственный API на Django;
подключение SPA к бэкенду Django через API;
создание образов и запуск контейнеров Docker;
развертывание многоконтейнерных приложений на сервере;
практическое закрепление основ DevOps, включая CI/CD.
Стек: #python #JSON #YAML #Django #React #Telegram #API #Docker #Nginx #PostgreSQL #Gunicorn #JWT #Postman