from rest_framework.pagination import PageNumberPagination

from core.constants import DEFAULT_PAGE_SIZE


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация выдачи результатов."""
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
