from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.models import Follow

User = get_user_model()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов в сокращенном виде."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UsersSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(
        default=False, read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Выявляем подписан ли текущий пользователь на просматриваемого."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.followers.filter(following=obj).exists()
        )


class UpdateAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор обновления Аватара."""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """Обновляем Аватар."""
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class UserRecipeSerializer(UsersSerializer):
    """Сериализатор модели Пользователь."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True, source='recipes.count'
    )

    class Meta:
        model = User
        fields = UsersSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', None)
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор модели Подписчики."""
    class Meta:
        model = Follow
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def validate(self, attrs):
        if self.context['request'].user == attrs.get('following'):
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return attrs

    def to_representation(self, instance):
        """Представление рецептов подписчика в ответе."""
        return UserRecipeSerializer(
            instance.following, context=self.context
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор представления количества ингредиента."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов с количеством для рецепта."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов."""
    tags = TagSerializer(many=True)
    author = UsersSerializer()
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('author', 'is_favorited', 'is_in_shopping_cart')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_image(self, value):
        """Проверяем наличие картинки."""
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать изображение.'
            )
        return value

    def validate(self, data):
        """Проверка уникальности тегов и ингредиентов и их минимум один."""
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Необходимо выбрать минимум один тег.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо выбрать минимум один ингредиент.')
        ingredient_ids = (
            [ingredient['ingredient'].id for ingredient in ingredients]
        )
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        return data

    def create(self, validated_data):
        """Сохраняем рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_tags_ingredients_to_recipe(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляем рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_tags_ingredients_to_recipe(instance, tags, ingredients)
        super().update(instance, validated_data)
        return instance

    @staticmethod
    def add_tags_ingredients_to_recipe(recipe, tags, ingredients):
        """Добавляем теги и ингредиенты в рецепт."""
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def to_representation(self, instance):
        """Представление рецепта в ответе."""
        return RecipeSerializer(instance, context=self.context).data


class ShoppingCartFavoriteSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для добавления рецептов в корзину или избранное."""

    class Meta:
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=None,
                fields=['user', 'recipe'],
                message='Вы уже добавили этот рецепт.'
            )
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.validators[0].queryset = self.get_queryset()

    def to_representation(self, instance):
        """Представление рецепта в ответе."""
        return RecipeShortSerializer(
            instance.recipe, context=self.context).data


class ShoppingCartSerializer(ShoppingCartFavoriteSerializer):
    """Сериализатор для списка покупок."""
    class Meta(ShoppingCartFavoriteSerializer.Meta):
        model = ShoppingCart

    def get_queryset(self):
        return ShoppingCart.objects.all()


class FavoriteRecipeSerializer(ShoppingCartFavoriteSerializer):
    """Сериализатор для подписчиков."""
    class Meta(ShoppingCartFavoriteSerializer.Meta):
        model = FavoriteRecipe

    def get_queryset(self):
        return FavoriteRecipe.objects.all()
