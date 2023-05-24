
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import (SET_NULL, CharField, EmailField, ForeignKey,
                              ManyToManyField, PositiveSmallIntegerField,
                              SlugField, TextField)

from .validators import validate_username, validate_year
class User(AbstractUser):

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    USER_ROLE_CHOICES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Админ'),
    )

    role = models.PositiveSmallIntegerField(
        'Роль',
        choices=USER_ROLE_CHOICES,
        default=USER,
        blank=True,
        null=True
    )
    username = models.CharField(
        'Никнейм',
        validators=(validate_username,),
        max_length=150,
        unique=True,
        blank=False,
        null=False
    )

    email = EmailField(
        'Почт@',
        max_length=254,
        null=False,
        blank=False,
        unique=True,
    )

    first_name = CharField(
        'Имя',
        max_length=150,
        blank=True
    )

    middle_name = CharField(
        'Отчество',
        max_length=20,
        null=True,
        blank=True,
    )

    last_name = CharField(
        'Фамилия',
        max_length=150,
        blank=True
        # интересный факт самая длинная
        # фамилия в мире состоит из 35 букв
    )

    bio = models.TextField(
        'Биография',
        null=True,
        blank=True,
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=True
    )
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=254,
        null=True,
        blank=False,
        default='XXXX'
    )

    @property
    def is_user(self):
        return self.role == User.USER

    @property
    def is_admin(self):
        return self.role == User.ADMIN

    @property
    def is_moderator(self):
        return self.role == User.MODERATOR

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username


