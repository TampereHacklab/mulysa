from django.core.management.base import BaseCommand
from emails.models import EmailCategory
from emails.models import STATIC_CATEGORIES

class Command(BaseCommand):
    help = 'Sync static email categories with database'

    def handle(self, *args, **options):
        for category_data in STATIC_CATEGORIES.values():
            category, created = EmailCategory.objects.update_or_create(
                name=category_data['name'],
                defaults={
                    'display_name': str(category_data['display_name']),
                    'display_name_en': str(category_data['display_name_en']),
                    'display_name_fi': str(category_data['display_name_fi']),
                    'description': str(category_data['description']),
                    'description_en': str(category_data['description_en']),
                    'description_fi': str(category_data['description_fi']),
                    'user_configurable': category_data['user_configurable'],
                    'default_enabled': category_data['default_enabled'],
                    'sort_priority': category_data['sort_priority'],
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} category: {category.display_name}')
            )
