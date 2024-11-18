from django_filters import (
    CharFilter, FilterSet, ModelMultipleChoiceFilter, NumberFilter,
)

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтр выборки рецепта по определенным полям."""
    author = NumberFilter(field_name='author__id')
    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация рецептов в избранном у текущего пользователя."""
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(favorite_recipes__user=user)
        elif value == 0:
            return queryset.exclude(favorite_recipes__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов в корзине у текущего пользователя."""
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(shopping_carts__user=user)
        elif value == 0:
            return queryset.exclude(shopping_carts__user=user)
        return queryset


class IngredientFilterSet(FilterSet):
    """Фильтр для Ингредиентов."""
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
