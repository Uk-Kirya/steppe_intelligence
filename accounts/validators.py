from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_image_format(value):
    import os
    ext = os.path.splitext(value.name)[1]  # Получаем расширение файла
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Unsupported file extension. Supported formats are: JPG, JPEG, PNG.'))
