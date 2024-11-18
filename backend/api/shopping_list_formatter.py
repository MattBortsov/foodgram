from datetime import datetime


def format_shopping_list(ingredients):
    """Функция для форматирования списка покупок."""
    shopping_list = []
    shopping_list.append('== Ваш список покупок ==\n')
    for ingredient in ingredients:
        shopping_list.append(
            '{:<20} {:<10} {:>5}'.format(
                ingredient['name'],
                f"({ingredient['measurement_unit']})",
                ingredient['amount'],
            )
        )
    shopping_list.append(
        f"Список создан: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    return '\n'.join(shopping_list)
