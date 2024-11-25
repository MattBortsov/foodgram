from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


def handle_recipe_action(
    request, pk, action_type, related_manager_name, serializer_class,
    success_message, error_message
):
    """
    Обрабатывает добавление или удаление рецепта в/из корзины
    или избранного через сериализатор.
    """
    user = request.user
    recipe = get_object_or_404(Recipe, id=pk)
    related_manager = getattr(user, related_manager_name)
    if action_type == 'add':
        serializer = serializer_class(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    elif action_type == 'remove':
        deleted, _ = related_manager.filter(recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': success_message},
            status=status.HTTP_204_NO_CONTENT)
