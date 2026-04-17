from modeltranslation.translator import register, TranslationOptions

from .models import (
    Page,
    Plain,
    Card,
    Variable,
    Country,
    Expertise,
    PublicationType,
    Article
)


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ('title_h1', 'text', 'keywords', 'description')


@register(Plain)
class PlainTranslationOptions(TranslationOptions):
    fields = ('title', 'price', 'text')


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


@register(Variable)
class VariableTranslationOptions(TranslationOptions):
    fields = ('title', 'text_1', 'text_2', 'text_3')


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Expertise)
class ExpertiseTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(PublicationType)
class PublicationTypeTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('title_h1', 'text', 'short_text')
