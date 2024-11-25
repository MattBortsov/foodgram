from rest_framework import permissions


class IsAuthorAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Разрешает только безопасные методы для всех пользователей.
    И проверяет кто делает запрос: автор/админ.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and (request.user == obj.author or request.user.is_superuser)
        )
