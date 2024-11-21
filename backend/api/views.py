from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilterSet, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (
    CreateUserSerializer, FavoriteRecipeSerializer, FollowSerializer,
    IngredientSerializer, PasswordSerializer, RecipeCreateSerializer,
    RecipeSerializer, RecipeShortSerializer, ShoppingCartSerializer,
    TagSerializer, UpdateAvatarSerializer, UserRecipeSerializer,
    UsersSerializer, RecipeShortLink
)
from api.shopping_list_formatter import format_shopping_list
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Tag,
)
from users.models import Follow, User


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UsersSerializer
        return CreateUserSerializer

    def get_user(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        """Метод для создания пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        User.objects.create_user(**serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Метод для получения данных текущего пользователя."""
        user = self.get_user()
        serializer = UsersSerializer(
            instance=user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=(IsAuthorAdminOrReadOnly,),
        url_path='me/avatar')
    def avatar(self, request):
        """Метод для обновления или удаления аватара пользователя."""
        user = self.get_user()
        if request.method == 'DELETE':
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(
                {'detail': 'Аватар успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
            )
        elif request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'error': 'Поле avatar обязательно'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UpdateAvatarSerializer(
                user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {'detail': 'Метод не поддерживается.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        methods=['post'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        user = self.get_user()
        serializer = PasswordSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(
                {'detail': 'Пароль успешно изменен'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthorAdminOrReadOnly,)
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя с рецептами."""
        page = self.paginate_queryset(request.user.following.all())
        if page:
            serializer = FollowSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(
            request.user.following.all(),
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        serializer_class=FollowSerializer,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        user = self.get_user()
        following = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            if user.following.filter(following=following).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == following:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, following=following)
            user_serializer = UserRecipeSerializer(
                following,
                context={'request': request}
            )
            return Response(
                user_serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            deleted, _ = user.following.filter(following=following).delete()
            if deleted == 0:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'detail': 'Успешная отписка'},
                status=status.HTTP_204_NO_CONTENT
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

    @action(
        methods=('get',),
        detail=True,
        permission_classes=(AllowAny,),
        url_path='short-link'
    )
    def get_short_link(self, request, *args, **kwargs):
        """Получение короткой ссылки для рецепта."""
        recipe = self.get_object()
        serializer = RecipeShortLink(recipe)
        return Response({'short_link': serializer.data['short_link']})

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
        methods=['post', 'delete'],
        detail=True,
        serializer_class=ShoppingCartSerializer,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт из корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        is_in_cart = user.shopping_carts.filter(recipe=recipe).exists()
        if request.method == 'POST':
            if is_in_cart:
                return Response(
                    {'detail': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not is_in_cart:
                return Response(
                    {'detail': 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.shopping_carts.filter(recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из корзины.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        methods=['post', 'delete'],
        detail=True,
        serializer_class=FavoriteRecipeSerializer,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        is_in_favorites = user.favorite_recipes.filter(recipe=recipe).exists()
        if request.method == 'POST':
            if is_in_favorites:
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not is_in_favorites:
                return Response(
                    {'detail': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.favorite_recipes.filter(recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT
            )
