from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.html import format_html

from content.models import Variable, Page, Card, Application, Plain, Country, Expertise, PublicationType, Article


@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'is_active')
    list_display_links = ('title',)
    list_editable = ('is_active',)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'slug', 'header_menu', 'footer_menu', 'is_active', 'order')
    list_display_links = ('title',)
    prepopulated_fields = {"slug": ('title',)}
    search_fields = ('title',)
    list_editable = ('header_menu', 'footer_menu', 'order', 'is_active')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_icon', 'type', 'is_active', 'order')
    list_display_links = ('get_icon', 'title')
    list_editable = ('is_active', 'order')
    ordering = ('type', 'order')

    list_filter = [
        'type'
    ]

    search_fields = [
        'title',
        'text'
    ]

    def get_icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" height="100" width="100" style="object-fit: cover;">', obj.icon.url)
        else:
            return "Иконка не загружена или не нужна"

    get_icon.short_description = 'Иконка'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'phone', 'email', 'status', 'created_at')
    list_display_links = ('subject', 'name')
    ordering = ('name', 'phone', 'created_at')
    list_editable = ('status',)

    search_fields = [
        'name',
        'phone',
        'email'
    ]

    list_filter = [
        'subject'
    ]


@admin.register(Plain)
class PlainAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_active', 'order')
    list_display_links = ('title', 'price')
    list_editable = ('order', 'is_active')

    search_fields = [
        'title',
        'text',
        'price'
    ]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_display_links = ('title',)
    list_editable = ('order', 'is_active')

    search_fields = [
        'title',
    ]


@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_display_links = ('title',)
    list_editable = ('order', 'is_active')

    search_fields = [
        'title',
    ]


@admin.register(PublicationType)
class PublicationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_display_links = ('title',)
    list_editable = ('order', 'is_active')

    search_fields = [
        'title',
    ]


@admin.register(Article)
class ArticleAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('get_image', 'title', 'date', 'author', 'is_active', 'by_subscription', 'order')
    list_display_links = ('get_image', 'title')
    prepopulated_fields = {"slug": ('title',)}
    list_editable = ('is_active', 'order')

    search_fields = [
        'title',
        'text',
        'short_text'
    ]

    list_filter = [
        'is_active',
        'by_subscription'
    ]

    readonly_fields = ('author',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_image(self, obj):
        return format_html('<img src="{}" height="60" width="100" style="object-fit: cover; border-radius: .3rem;">', obj.image.url)

    get_image.short_description = 'Картинка'

