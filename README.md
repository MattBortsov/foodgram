# Foodgram
Домен на котором развернут проект - foodgram-maui.hopto.org

## Описание проекта:
**Foodgram** — это сайт для публикации рецептов, добавления понравившихся рецептов в избранное и подписки на других авторов. Пользователи также могут воспользоваться функцией «Список покупок», которая помогает составить список продуктов, необходимых для выбранных блюд.

---
## Подготовка проекта:

### Установить и активировать виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Запустить проект в Docker container
```bash
cd foodgram
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py load_ingredients # загрузка ингредиентов в БД.
```
---

## Технологии:
- **Python** 3.9  
- **Django** 3.2.16  
- **Django REST Framework** 3.12.4  
- **Nginx**  
- **Djoser** 2.1.0  
- **PostgreSQL**  

---

## Как открыть ReDoc
```bash
cd foodgram/infra_test
docker compose up
```

При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для фронтенд-приложения, а затем прекратит свою работу. 
По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

---

## Пример запросов и ответов:

### Получение списка рецептов:
#### Запрос:
GET /api/recipes/
#### Ответ:
```json
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

### Создание рецепта:
#### Запрос
POST /api/recipes/
```json
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```
#### Ответ:
```json
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "http://foodgram.example.org/media/users/image.png"
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.png",
  "text": "string",
  "cooking_time": 1
}
```

---

## Что сделано:
В проекте **Foodgram** настроен запуск в контейнерах и автоматизация CI/CD через **GitHub Actions**. При каждом пуше в ветку `master` запускаются тестирование и деплой проекта. После завершения деплоя в **Telegram** отправляется уведомление. Реализованы:  

- интеграция Python-приложения с внешними API-сервисами;  
- собственный API на **Django**;  
- подключение SPA к бэкенду через API;  
- создание образов и запуск контейнеров **Docker**;  
- развертывание многоконтейнерных приложений на сервере;  
- внедрение CI/CD процессов с использованием **GitHub Actions**.

---

Автор: Борцов Матвей
LinkedIn: https://www.linkedin.com/in/matt-bortsov/