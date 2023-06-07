from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        blank=False,
        null=False,
        max_length=254,
    )
    username = models.CharField(
        'Имя пользователя',
        unique=True,
        blank=False,
        null=False,
        max_length=150,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        'Имя',
        blank=False,
        null=False,
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        blank=False,
        null=False,
        max_length=150,
    )
    password = models.CharField(
        'Пароль',
        blank=False,
        null=False,
        max_length=150,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписчика."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
