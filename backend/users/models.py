from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from core.constants import LENGTH_EMAIL, LENGTH_NAME
from users.validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField(unique=True, max_length=LENGTH_EMAIL)
    username = models.CharField(
        'Имя пользователя',
        max_length=LENGTH_NAME,
        unique=True,
        validators=[validate_username]
    )
    first_name = models.CharField(
        'Имя',
        max_length=LENGTH_NAME, blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LENGTH_NAME, blank=False
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True, null=True
    )
    role = models.CharField(
        'Роль',
        max_length=LENGTH_NAME,
        choices=Role.choices,
        default=Role.USER
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return (
            self.role == self.Role.ADMIN
            or self.is_superuser
            or self.is_staff
        )


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
