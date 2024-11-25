from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    """Inline модель для ингредиентов рецепта."""
    model = RecipeIngredient
    extra = 1
    min_num = 1
    fields = ('ingredient', 'amount')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Раздел Ингредиента в админке."""
    list_display = ('name', 'measurement_unit')
    list_editable = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Раздел Тэга в админке."""
    list_display = ('name', 'slug')
    list_editable = ('slug',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Раздел Рецепта в админке."""
    list_display = ('name', 'author', 'get_favorite_count')
    list_editable = ('author',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]

    @admin.display(description='Сохранений')
    def get_favorite_count(self, obj):
        return obj.favorite_recipes.count()
