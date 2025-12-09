"""Merge migration to resolve conflicting leaf nodes

This migration depends on both the new 0220_add_access_permissions migration
and the existing 0031_customuser_is_instructor migration so Django's
migration graph has a single leaf for the `users` app.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0031_customuser_is_instructor"),
        ("users", "0220_add_access_permissions"),
    ]

    operations = []
