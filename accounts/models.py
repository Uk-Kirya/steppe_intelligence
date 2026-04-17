import os
import uuid

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .validators import validate_image_format
from content.models import Country, Expertise

from datetime import timedelta
from django.utils import timezone


def user_directory_path_ava(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('user', instance.user.username, filename)


class Profile(models.Model):
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    PROFILE_STATUS = [
        ('pending_email', 'Ожидает подтверждение E-mail'),
        ('pending_review', 'Ожидает подтверждения модератора'),
        ('active', 'Активный'),
        ('deactivated', 'Деактивированный')
    ]

    ROLES = [
        ('expert', 'Эксперт'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=100, blank=False, verbose_name='Имя')
    lastname = models.CharField(max_length=100, blank=False, verbose_name='Фамилия')
    phone = models.CharField(max_length=100, blank=True, verbose_name='Телефон')
    photo = models.FileField(upload_to=user_directory_path_ava, blank=True, null=True, verbose_name='Фото профиля',
                             validators=[validate_image_format])
    country = models.ForeignKey(Country, blank=False, on_delete=models.CASCADE, verbose_name='Страна')
    expertises = models.ManyToManyField(Expertise, verbose_name='Экспертизы')
    bio = RichTextUploadingField(blank=True, verbose_name='Биография')
    experience = RichTextUploadingField(blank=True, verbose_name='Описание опыта')
    post = models.CharField(max_length=500, blank=True, verbose_name='Должность')
    linkedin = models.CharField(max_length=500, blank=True, verbose_name='LinkedIn')
    role = models.CharField(choices=ROLES, default='expert', blank=False, max_length=255, verbose_name='Роль')
    status = models.CharField(choices=PROFILE_STATUS, default='pending_email', blank=False, max_length=255, verbose_name='Статус')
    deactivated_message = models.TextField(blank=True, verbose_name='Причина блокировки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    def save(self, *args, **kwargs):
        # Проверяем, есть ли уже загруженное фото
        if self.photo:
            try:
                # Получаем текущий объект из базы данных
                current_profile = Profile.objects.get(pk=self.pk)
                # Проверяем, отличается ли новое фото от старого
                if current_profile.photo != self.photo:
                    # Удаляем старое фото
                    if current_profile.photo:
                        if os.path.isfile(current_profile.photo.path):
                            os.remove(current_profile.photo.path)
                else:
                    # Если фото не изменилось, не обрабатываем его
                    super().save(*args, **kwargs)
                    return
            except Profile.DoesNotExist:
                # Если объект не существует, ничего не делаем
                pass

        if self.status == 'deactivated':
            subject = 'Деактивация аккаунта на сайте Steppe Intelligence'

            message_template = render_to_string('messages/deactivate.html', {
                'name': self.name,
                'subject': subject,
                'deactivated_message': self.deactivated_message
            })

            send_mail(
                subject,
                message_template,
                settings.EMAIL_HOST_USER,
                [self.user.email],
                html_message=message_template,
                fail_silently=False
            )

        if self.status == 'active':
            subject = 'Активация аккаунта на сайте Steppe Intelligence'

            message_template = render_to_string('messages/active.html', {
                'name': self.name,
                'subject': subject
            })

            send_mail(
                subject,
                message_template,
                settings.EMAIL_HOST_USER,
                [self.user.email],
                html_message=message_template,
                fail_silently=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.user.username


class EmailVerificationToken(models.Model):
    class Meta:
        verbose_name = 'Токен верификации email'
        verbose_name_plural = 'Токены верификации email'

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='Токен')
    is_used = models.BooleanField(default=False, verbose_name='Использован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"Token for {self.user.email} - {'Used' if self.is_used else 'Active'}"

    def is_expired(self):
        # Токен действителен 30 дней
        expiration_date = self.created_at + timedelta(days=30)
        return timezone.now() > expiration_date
