import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.constants import (
    COOKING_MIN_TIME, INGREDIENT_LENGTH, MEASUREMENT_LENGTH, RECIPE_LENGTH,
    SHORT_LINK_LENGTH, TAG_NAME,
)
from users.models import User


class Ingredient(models.Model):
    """Модель Ингредиента."""
    name = models.CharField(
        'Название',
        max_length=INGREDIENT_LENGTH, blank=False
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_LENGTH, blank=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Модель Тэга."""
    name = models.CharField(
        'Название',
        max_length=TAG_NAME,
        unique=True, blank=False)
    slug = models.SlugField(
        max_length=TAG_NAME, unique=True,
        blank=True, null=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель Рецепта."""
    name = models.CharField('Название', max_length=RECIPE_LENGTH, blank=False)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
        blank=False, null=False
    )
    text = models.TextField('Описание', blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(COOKING_MIN_TIME)],
        help_text='Укажите время приготовления в минутах',
        blank=False, null=False
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_LENGTH,
        blank=True, null=True, unique=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def generate_short_link(self):
        """Генерация короткой ссылки для рецепта."""
        base_url = settings.BASE_URL
        max_attempts = 5
        for attempt in range(max_attempts):
            short_code = uuid.uuid4().hex[:3]
            short_link = f'{base_url}/s/{short_code}'
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link
        while True:
            short_code = uuid.uuid4().hex[:4]
            short_link = f'{base_url}/s/{short_code}'
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, *args, **kwargs):
        """Сохранение короткой ссылки для рецепта в модели."""
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель Ингредиентов рецепта."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} — {self.amount}'
            f'{self.ingredient.measurement_unit}'
        )


class FavoriteRecipe(models.Model):
    """Промежуточная модель Избранного рецепта."""
    user = models.ForeignKey(
        User,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    """Промежуточная модель Корзины покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
