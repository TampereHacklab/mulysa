import os
import re
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check that all .po files have no untranslated or fuzzy entries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--require",
            nargs="+",
            metavar="APP",
            default=[],
            help="Apps where incomplete translations are errors (others are warnings)",
        )

    def _list_msgids(self, po_file, flag):
        result = subprocess.run(
            ["msgattrib", flag, str(po_file)],
            capture_output=True,
            text=True,
        )
        msgids = []
        current = None
        for line in result.stdout.splitlines():
            if line.startswith("msgid "):
                current = line[len('msgid "'):-1]
            elif line.startswith('"') and current is not None:
                current += line[1:-1]
            else:
                if current:
                    msgids.append(current[:80])
                current = None
        if current:
            msgids.append(current[:80])
        return msgids

    def handle(self, *args, **options):
        required_apps = set(options["require"])
        base = Path(settings.BASE_DIR)
        po_files = [
            p
            for p in base.rglob("*.po")
            if ".tox" not in p.parts and "site-packages" not in p.parts
        ]

        if not po_files:
            self.stderr.write("No .po files found")
            raise SystemExit(1)

        has_errors = False
        for po_file in sorted(po_files):
            result = subprocess.run(
                ["msgfmt", "--statistics", "-o", os.devnull, str(po_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                rel = po_file.relative_to(base)
                self.stderr.write(
                    self.style.ERROR(f"{rel}: {result.stderr.strip()}")
                )
                raise SystemExit(1)
            stats = result.stderr.strip()
            untranslated = re.search(r"(\d+) untranslated", stats)
            fuzzy = re.search(r"(\d+) fuzzy", stats)
            if not (untranslated or fuzzy):
                continue

            rel = po_file.relative_to(base)
            parts = []
            if fuzzy:
                parts.append(f"{fuzzy.group(1)} fuzzy")
            if untranslated:
                parts.append(f"{untranslated.group(1)} untranslated")

            is_required = not required_apps or rel.parts[0] in required_apps
            style = self.style.ERROR if is_required else self.style.WARNING
            suffix = "" if is_required else " (warning only)"
            self.stderr.write(style(f"{rel}: {', '.join(parts)}{suffix}"))

            if fuzzy:
                for msgid in self._list_msgids(po_file, "--only-fuzzy"):
                    self.stdout.write(f"  fuzzy:        {msgid}")
            if untranslated:
                for msgid in self._list_msgids(po_file, "--untranslated"):
                    self.stdout.write(f"  untranslated: {msgid}")

            if is_required:
                has_errors = True

        if has_errors:
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(f"All {len(po_files)} translation files checked")
        )
