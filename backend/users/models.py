from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q

from core.constants import LENGTH_NAME


class User(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(unique=True)
    username = models.CharField(
        'Имя пользователя',
        max_length=LENGTH_NAME,
        unique=True,
        validators=[UnicodeUsernameValidator]
    )
    first_name = models.CharField(
        'Имя',
        max_length=LENGTH_NAME
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LENGTH_NAME
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True, null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Промежуточная модель Подписчиков."""
    user = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE
    )

    class Meta:
        """Исключаем повторную подписку и подписку на самого себя."""
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following'
            ),
            models.CheckConstraint(
                check=~Q(user=F('following')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} следит за {self.following}'
