import re

from django.core.exceptions import ValidationError

from core.constants import RESTRICTED_USERNAME


def validate_username(value):
    if value.lower() in RESTRICTED_USERNAME:
        raise ValidationError('Имя пользователя зарезервировано.')
    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError('Имя содержит недопустимые символы.')
