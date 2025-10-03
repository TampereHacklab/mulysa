from modeltranslation.translator import register, TranslationOptions
from .models import MemberService

# Register the MemberService model fields for translation with modeltranslation
@register(MemberService)
class MemberServiceTranslationOptions(TranslationOptions):
    fields = ("name", "description")