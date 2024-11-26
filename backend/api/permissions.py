from rest_framework import permissions


class IsAuthorAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Разрешает только безопасные методы для всех пользователей.
    И проверяет кто делает запрос: автор/админ.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user == obj.author
        )
