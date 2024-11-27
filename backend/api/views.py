from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilterSet, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (
    FavoriteRecipeSerializer, FollowSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeSerializer, ShoppingCartSerializer,
    TagSerializer, UpdateAvatarSerializer, UsersSerializer,
)
from api.shopping_list_formatter import format_shopping_list
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Tag,
)
from users.models import User


class UsersViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    @action(
        methods=('get',),
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Метод для получения данных текущего пользователя."""
        return super().me(request)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthorAdminOrReadOnly],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Метод для обновления аватара пользователя."""
        user = self.request.user
        serializer = UpdateAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = self.request.user
        user.avatar.delete()
        user.save()
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthorAdminOrReadOnly]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя с рецептами."""
        page = self.paginate_queryset(request.user.following.all())
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        following = get_object_or_404(User, id=id)
        serializer = FollowSerializer(
            data={'user': user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        user = self.request.user
        following = get_object_or_404(User, id=id)
        deleted, _ = user.following.filter(following=following).delete()
        if not deleted:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Успешная отписка'}, status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет Тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет Рецептов."""
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            return (IsAuthenticated(),)
        elif self.action in ['partial_update', 'destroy']:
            return (IsAuthorAdminOrReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        """Переопределение queryset с предвыборкой избранных и корзины."""
        user = self.request.user
        queryset = Recipe.objects.all()
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )
        return queryset

    @action(methods=['get'], detail=True, url_path='get-link')
    def short_url(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_url = recipe.short_link_code
        full_url = request.build_absolute_uri(f'/s/{short_url}/')
        return Response({'short-link': full_url}, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthorAdminOrReadOnly]
    )
    def download_shopping_cart(self, request):
        ingredients = (
            Ingredient.objects
            .filter(recipes__shopping_carts__user=request.user)
            .values('name', 'measurement_unit')
            .annotate(amount=Sum(F('recipe_ingredients__amount')))
            .order_by('name')
        )
        content = format_shopping_list(ingredients)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в корзину."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingCartSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        deleted, _ = user.shopping_carts.filter(recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не найден в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Рецепт успешно удален из корзины.'},
            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteRecipeSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        deleted, _ = user.favorite_recipes.filter(recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Рецепт успешно удален из избранного.'},
            status=status.HTTP_204_NO_CONTENT)


def redirect_short_url(request, short_link):
    """Перенаправление по короткой ссылке на рецепт."""
    recipe = get_object_or_404(Recipe, short_link_code=short_link)
    return redirect(f'/recipes/{recipe.id}/')
