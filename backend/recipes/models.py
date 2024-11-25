import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.constants import (
    COOKING_MAX_TIME, COOKING_MIN_TIME, INGREDIENT_LENGTH,
    INGREDIENT_MAX_AMOUNT, INGREDIENT_MIN_AMOUNT, MEASUREMENT_LENGTH,
    RECIPE_LENGTH, SHORT_LINK_CODE_LENGTH, TAG_NAME,
)
from users.models import User


class Ingredient(models.Model):
    """Модель Ингредиента."""
    name = models.CharField(
        'Название',
        max_length=INGREDIENT_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_measurement_unit_to_ingredient'
            )
        ]

    def __str__(self):
        return f'Ингредиент - {self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Модель Тэга."""
    name = models.CharField(
        'Название',
        max_length=TAG_NAME, unique=True
    )
    slug = models.SlugField(
        max_length=TAG_NAME, unique=True,
        blank=True, null=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Тег - {self.name} (slug: {self.slug})'


class Recipe(models.Model):
    """Модель Рецепта."""
    name = models.CharField('Название', max_length=RECIPE_LENGTH)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
        blank=False, null=False
    )
    text = models.TextField('Описание', blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                COOKING_MIN_TIME,
                message=f'Укажите число больше {COOKING_MIN_TIME}'
            ),
            MaxValueValidator(
                COOKING_MAX_TIME,
                message=f'Укажите число меньше {COOKING_MAX_TIME}'
            )
        ],
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
    short_link_code = models.CharField(
        max_length=SHORT_LINK_CODE_LENGTH,
        blank=True, null=True, unique=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def generate_short_link_code(self):
        """Генерация короткого кода для рецепта."""
        existing_codes = set(
            Recipe.objects.values_list('short_link_code', flat=True)
        )
        short_code = uuid.uuid4().hex[:3]
        while short_code in existing_codes:
            short_code = uuid.uuid4().hex[:4]
        return short_code

    def save(self, *args, **kwargs):
        if not self.short_link_code:
            self.short_link_code = self.generate_short_link_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Рецепт - {self.name}'


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
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                COOKING_MIN_TIME,
                message=f'Укажите число больше {INGREDIENT_MIN_AMOUNT}'
            ),
            MaxValueValidator(
                COOKING_MAX_TIME,
                message=f'Укажите число меньше {INGREDIENT_MAX_AMOUNT}'
            )
        ],
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


class AbstractRecipeRelation(models.Model):
    """Абстрактная модель для связи пользователя и рецепта."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class FavoriteRecipe(AbstractRecipeRelation):
    """Промежуточная модель Избранного рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        default_related_name = 'favorite_recipes'
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(AbstractRecipeRelation):
    """Промежуточная модель Корзины покупок."""
    class Meta:
        default_related_name = 'shopping_carts'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]
