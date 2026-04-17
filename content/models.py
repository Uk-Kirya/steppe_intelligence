import os
from pathlib import Path
from uuid import uuid4

from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def path_to_variables_icons(instance, filename):
    ext = Path(filename).suffix
    filename = f"{uuid4()}{ext}"
    return os.path.join('variables', 'icons', filename)


def path_to_variables_images(instance, filename):
    filename = f"{uuid4()}.webp"
    return os.path.join('variables', 'images', filename)


def path_to_pages_images(instance, filename):
    filename = f"{uuid4()}.webp"
    return os.path.join('pages', filename)


def path_to_cards_icons(instance, filename):
    ext = Path(filename).suffix
    filename = f"{uuid4()}{ext}"
    return os.path.join('cards', filename)


def path_to_articles_images(instance, filename):
    filename = f"{uuid4()}.webp"
    return os.path.join('articles', filename)


class Variable(models.Model):
    class Meta:
        verbose_name = 'Переменная'
        verbose_name_plural = 'Переменные'
        ordering = ['order']

    title = models.CharField(max_length=255, blank=False, verbose_name='Имя переменной')
    text_1 = models.CharField(max_length=500, blank=True, verbose_name='Текст 1')
    text_2 = models.TextField(blank=True, verbose_name='Текст 2')
    text_3 = RichTextUploadingField(blank=True, verbose_name='Текст 3')
    icon = models.FileField(upload_to=path_to_variables_icons, blank=True, verbose_name='Иконка')
    image = models.ImageField(upload_to=path_to_variables_images, blank=True, verbose_name='Картинка')
    is_active = models.BooleanField(default=True, verbose_name='Активная?')
    order = models.IntegerField(default=0, blank=True, verbose_name='Порядковый номер')
    name = models.CharField(max_length=255, blank=False, verbose_name='Имя переменной')

    def __str__(self):
        return self.title if self.title else f'Переменная #{self.pk}'

    def save(self, *args, **kwargs):
        if self.pk:
            current_variable = Variable.objects.get(pk=self.pk)

            if self.icon:
                try:
                    if current_variable.icon and current_variable.icon != self.icon:
                        icon_path = Path(current_variable.icon.path)
                        if icon_path.exists():
                            icon_path.unlink()
                except Variable.DoesNotExist:
                    pass

            if self.image:
                try:
                    if current_variable.image and current_variable.image != self.image:
                        image_path = Path(current_variable.image.path)
                        if image_path.exists():
                            image_path.unlink()
                except Variable.DoesNotExist:
                    pass

        super().save(*args, **kwargs)


class Page(models.Model):
    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = 'order',

    TYPE = [
        ('text', 'Текстовая'),
        ('about', 'О компании'),
        ('services', 'Услуги'),
        ('sb', 'Steppe Brief'),
        ('researches', 'Исследования'),
        ('learning', 'Обучение'),
        ('contacts', 'Контакты'),
        ('register', 'Стать экспертом'),
        ('auth', 'Авторизация'),
    ]

    title = models.CharField(max_length=500, blank=False, verbose_name='Заголовок')
    title_h1 = models.CharField(max_length=500, blank=False, verbose_name='Заголовок H1')
    type = models.CharField(max_length=100, default='text', choices=TYPE, verbose_name='Шаблон страницы')
    image = models.ImageField(upload_to=path_to_pages_images, blank=True, verbose_name='Картинка')
    text = RichTextUploadingField(blank=True, verbose_name='Текст')
    keywords = models.TextField(blank=True, verbose_name='Keywords')
    description = models.TextField(blank=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Активная?')
    is_dedicated = models.BooleanField(default=False, verbose_name='Выделенный пункт?')
    header_menu = models.BooleanField(default=False, verbose_name='Отображать в основном меню?')
    footer_menu = models.BooleanField(default=False, verbose_name='Отображать в подвале?')
    order = models.IntegerField(default=0, blank=True, verbose_name='Порядковый номер')
    slug = models.SlugField(max_length=255, blank=True, verbose_name='Slug')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.pk:
            current_page = Page.objects.get(pk=self.pk)

            if self.image:
                try:
                    if current_page.image and current_page.image != self.image:
                        image_path = Path(current_page.image.path)
                        if image_path.exists():
                            image_path.unlink()
                except Page.DoesNotExist:
                    pass

        super().save(*args, **kwargs)


class Card(models.Model):
    class Meta:
        verbose_name = 'Карточка'
        verbose_name_plural = 'Карточки'
        ordering = ['order']

    TYPE_CHOICES = (
        ("type_1", "Чем мы занимаемся"),
        ("type_2", "Почему Steppe Intelligence"),
        ("type_3", "О компании (Эксперты)"),
        ("type_4", "Услуги (Steppe Brief)"),
        ("type_5", "Что включено в каждый выпуск"),
        ("type_6", "Для кого"),
        ("type_7", "Кому подойдут наши программы"),
        ("type_8", "Как проходит обучение"),
        ("type_9", "Как начать?"),
    )

    title = models.CharField(max_length=500, blank=True, verbose_name='Заголовок')
    type = models.CharField(max_length=500, default="type_1", choices=TYPE_CHOICES, verbose_name='Тип карточки')
    text = models.TextField(blank=True, verbose_name='Текст')
    icon = models.FileField(upload_to=path_to_cards_icons, blank=True, verbose_name='Иконка')
    is_active = models.BooleanField(default=True, verbose_name='Активная?')
    order = models.IntegerField(default=0, blank=True, verbose_name='Порядковый номер')

    def __str__(self):
        return self.title if self.title else f'Карточка #{self.pk}'

    def save(self, *args, **kwargs):
        if self.pk:
            current_card = Card.objects.get(pk=self.pk)

            if self.icon:
                try:
                    if current_card.icon and current_card.icon != self.icon:
                        icon_path = Path(current_card.icon.path)
                        if icon_path.exists():
                            icon_path.unlink()
                except Card.DoesNotExist:
                    pass

        super().save(*args, **kwargs)


class Application(models.Model):
    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['created_at']

    subject = models.CharField(max_length=255, blank=False, verbose_name='Тема сообщения')
    name = models.CharField(max_length=500, blank=False, verbose_name='Имя')
    phone = models.CharField(max_length=50, blank=False, verbose_name='Телефон')
    email = models.CharField(max_length=500, blank=False, verbose_name='E-mail')
    message = models.TextField(blank=True, verbose_name='Сообщение')
    post = models.CharField(max_length=500, blank=True, verbose_name='Должность')
    status = models.BooleanField(default=False, verbose_name='Обработанная?')
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Заявка от {self.name} с темой {self.subject}'


class Plain(models.Model):
    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    title = models.CharField(max_length=255, blank=False, verbose_name='Заголовок')
    price = models.CharField(max_length=255, blank=False, verbose_name='Цена')
    text = models.CharField(max_length=500, blank=False, verbose_name='Текст')
    link = models.CharField(max_length=255, blank=True, verbose_name='Ссылка на описание')
    is_active = models.BooleanField(default=True, verbose_name='Активный?')
    order = models.IntegerField(default=0, blank=False, verbose_name='Порядковый номер')

    def __str__(self):
        return f'Тариф {self.title}'


class Country(models.Model):
    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    title = models.CharField(max_length=255, blank=False, verbose_name='Заголовок')
    is_active = models.BooleanField(default=True, verbose_name='Активный?')
    order = models.IntegerField(default=0, blank=False, verbose_name='Порядковый номер')

    def __str__(self):
        return self.title


class Expertise(models.Model):
    class Meta:
        verbose_name = 'Экспертиза'
        verbose_name_plural = 'Сферы экспертизы'

    title = models.CharField(max_length=255, blank=False, verbose_name='Заголовок')
    is_active = models.BooleanField(default=True, verbose_name='Активная?')
    order = models.IntegerField(default=0, blank=False, verbose_name='Порядковый номер')

    def __str__(self):
        return self.title


class PublicationType(models.Model):
    class Meta:
        verbose_name = 'Тип публикации'
        verbose_name_plural = 'Тип публикаций'

    title = models.CharField(max_length=255, blank=False, verbose_name='Заголовок')
    is_active = models.BooleanField(default=True, verbose_name='Активный?')
    order = models.IntegerField(default=0, blank=False, verbose_name='Порядковый номер')

    def __str__(self):
        return self.title


class Article(models.Model):
    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = 'order',

    title = models.CharField(max_length=500, blank=False, verbose_name='Заголовок')
    title_h1 = models.CharField(max_length=500, blank=False, verbose_name='Заголовок H1')
    date = models.DateField(auto_now_add=False, blank=False, verbose_name='Дата публикации')
    image = models.ImageField(upload_to=path_to_articles_images, blank=False, verbose_name='Картинка')
    short_text = models.TextField(blank=False, verbose_name='Анонс')
    text = RichTextUploadingField(blank=False, verbose_name='Текст')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    types = models.ManyToManyField(PublicationType, blank=True, verbose_name='Тип публикации')
    countries = models.ManyToManyField(Country, blank=True, verbose_name='Страна')
    expertises = models.ManyToManyField(Expertise, blank=True, verbose_name='Экспертизы')
    slug = models.SlugField(max_length=500, blank=False, verbose_name='Slug')
    by_subscription = models.BooleanField(default=False, verbose_name='По подписке')
    is_active = models.BooleanField(default=True, verbose_name='Активная?')
    order = models.PositiveIntegerField(default=0, blank=True, verbose_name='Порядок')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('content:article_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.pk:
            current_image = Article.objects.get(pk=self.pk)

            if self.image:
                try:
                    if current_image.image and current_image.image != self.image:
                        image_path = Path(current_image.image.path)
                        if image_path.exists():
                            image_path.unlink()
                except Article.DoesNotExist:
                    pass

        super().save(*args, **kwargs)
