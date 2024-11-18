from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Раздел пользователей в админке."""

    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_display_links = ('username',)


admin.site.empty_value_display = 'Не задано'
