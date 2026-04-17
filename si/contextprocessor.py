from typing import Any
from django.http import HttpRequest

from content.models import Variable, Page, Card


def context_all(request: HttpRequest) -> dict[str, Any]:
    path_without_lang = request.path.split('/')[2:]
    path_without_lang = '/' + '/'.join(path_without_lang)

    context = {
        "pages": Page.objects.filter(is_active=True),
        "vars": Variable.objects.filter(is_active=True),
        "cards": Card.objects.filter(is_active=True),
        "banner": Variable.objects.get(name='banner').text_1,
        "tarif_text": Variable.objects.get(name='tarif_text').text_1,
        "training_text": Variable.objects.get(name='training_text').text_1,
        "training_text_2": Variable.objects.get(name='training_text_2').text_2,
        "whatsapp": Variable.objects.get(name='whatsapp'),
        "email": Variable.objects.get(name='email').text_1,
        "linkedin": Variable.objects.get(name='linkedin').text_1,
        "path_without_lang": path_without_lang,
    }

    return context
