from modeltranslation.translator import register, TranslationOptions
from .models import Email, EmailCategory

@register(EmailCategory)
class EmailCategoryTranslationOptions(TranslationOptions):
    fields = ("display_name", "description")