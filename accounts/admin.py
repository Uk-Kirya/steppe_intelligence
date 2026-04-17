from django.contrib import admin
from django.utils.html import format_html
from django.templatetags.static import static

from accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_photo', 'get_name', 'role', 'get_email', 'status', 'created_at')
    list_display_links = ('get_name',)
    readonly_fields = ('user',)

    list_filter = [
        'role',
        'status'
    ]

    search_fields = [
        'name',
        'lastname'
    ]

    def get_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" height="64" width="64" style="object-fit: cover; border-radius: 100%;">', obj.photo.url)
        else:
            fav_url = static('fav.png')
            return format_html(f'<img src="{fav_url}" height="64" width="64" style="object-fit: cover;">')

    get_photo.short_description = 'Фотография'

    def get_name(self, obj):
        return f'{obj.name} {obj.lastname}'

    get_name.short_description = 'Имя'

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'E-mail'
