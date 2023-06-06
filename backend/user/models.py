from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.mail import send_mail


class User(AbstractUser):
    """Кастомная модель пользователя"""
    role = models.CharField(
        'Роль',
        max_length=50,
        choices=settings.USER_ROLE_CHOICES,
        default=settings.USER,
        blank=True,
        null=True
    )

    username = models.CharField(
        verbose_name='Логин',
        max_length=settings.MAX_LEN_USER_FIELD,
        unique=True)
    email = models.EmailField(
        verbose_name='Email',
        max_length=settings.MAX_LEN_USER_EMAIL,
        unique=False)
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.MAX_LEN_USER_FIELD, )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=settings.MAX_LEN_USER_FIELD)
    password = models.CharField(
        verbose_name='Пароль',
        max_length=settings.MAX_LEN_USER_FIELD)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username}, {self.email}'

    @property
    def is_user(self):
        return self.role == User.USER

    @property
    def is_admin(self):
        return self.role == User.ADMIN

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription')]

    def __str__(self):
        return (f'Пользователь: {self.user.username},'
                f' автор: {self.author.username}')
