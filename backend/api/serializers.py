from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from core.constants import COOKING_MIN_TIME, RESTRICTED_USERNAME
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from users.models import Follow

User = get_user_model()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов в сокращенном виде."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UpdateAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор обновления Аватара."""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """Обновляем Аватар."""
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        """Проверка правильности текущего пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный.")
        return value

    def validate_new_password(self, value):
        """Валидация нового пароля с использованием правил Django."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """Проверка, что новый пароль не совпадает с текущим."""
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        if current_password == new_password:
            raise serializers.ValidationError(
                "Новый пароль не должен совпадать с текущим.")
        return attrs


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, obj):
        """Проверяем введеные данные."""
        if self.initial_data.get('username') in RESTRICTED_USERNAME:
            raise serializers.ValidationError(
                {'username': 'Имя пользователя зарезервировано.'}
            )
        return obj

    def create(self, validated_data):
        """Создаем пользователя."""
        user = User.objects.create_user(**validated_data)
        return user


class UserRecipeSerializer(UserSerializer):
    """Сериализатор модели Пользователь."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True, source='recipes.count'
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', None)
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_is_subscribed(self, obj):
        """Выявляем подписан ли текущий пользователь на просматриваемого."""
        user = self.context.get('request').user
        if user is None or user.is_anonymous or user == obj:
            return False
        return user.followers.filter(following=obj).exists()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор модели Подписчики."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def save(self, **kwargs):
        """Сохраняем подписку."""
        user = self.context['request'].user
        following = self.context['following']
        instance = super().save(user=user, following=following, **kwargs)
        return instance

    def to_representation(self, instance):
        """Представление рецептов подписчика в ответе."""
        return UserRecipeSerializer(
            instance.following, context=self.context).data


class UsersSerializer(UserSerializer):
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
        user = self.context.get('request').user
        if user is None or user.is_anonymous or user == obj:
            return False
        return user.followers.filter(following=obj).exists()


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

    def validate_cooking_time(self, value):
        """Проверяем введеное время приготовления."""
        if value is None or value < COOKING_MIN_TIME:
            raise serializers.ValidationError(
                'Время приготовления (в минутах) должно быть в рецепте.'
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
        tag_ids = [tag.id for tag in tags]
        existing_tags = Tag.objects.filter(id__in=tag_ids)
        if len(existing_tags) != len(tag_ids):
            raise serializers.ValidationError('Некоторые теги не существуют.')
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
        recipe, tags, ingredients = self.get_data(validated_data)
        self.add_tags_ingredients_to_recipe(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляем рецепт."""
        recipe, tags, ingredients = self.get_data(validated_data, instance)
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_tags_ingredients_to_recipe(recipe, tags, ingredients)
        super().update(instance, validated_data)
        return instance

    def get_data(self, validated_data, instance=None):
        """Получаем данные рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        if instance is None:
            recipe = Recipe.objects.create(author=author, **validated_data)
        else:
            recipe = instance
        return recipe, tags, ingredients

    def add_tags_ingredients_to_recipe(self, recipe, tags, ingredients):
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


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=['user', 'recipe'],
                message='Вы уже добавили этот рецепт в корзину.'
            )
        ]


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписчиков."""
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=['user', 'recipe'],
                message='Вы уже добавили этот рецепт в избранное.'
            )
        ]


class RecipeShortLink(serializers.ModelSerializer):
    """Сериализатор для короткой ссылки."""
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Формируем короткую ссылку с текущим хостом."""
        request = self.context.get('request')
        if request:
            host = request.get_host()
        else:
            host = settings.BASE_URL
        if host in settings.ALLOWED_HOSTS:
            return f'http://{host}/s/{obj.short_link_code}'
