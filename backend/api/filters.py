from django_filters import (
    CharFilter, FilterSet, AllValuesMultipleFilter, NumberFilter, BooleanFilter
)

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтр выборки рецепта по определенным полям."""
    author = NumberFilter(field_name='author__id')
    is_favorited = BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')


class IngredientFilterSet(FilterSet):
    """Фильтр для Ингредиентов."""
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
