from rest_framework import permissions


class IsAuthorAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Разрешает только безопасные методы для всех пользователей.
    И проверяет кто делает запрос: автор/админ.
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_anonymous
                and request.method in permissions.SAFE_METHODS
                or (request.user == obj.author or request.user.is_admin)
                )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает безопасные методы для всех пользователей,
    и проверяет права администратора.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
            or request.method in permissions.SAFE_METHODS
        )
