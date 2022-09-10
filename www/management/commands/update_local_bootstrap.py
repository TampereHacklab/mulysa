import os
import pprint
from urllib.parse import urlparse

from django.apps import apps
from django.core.management.base import BaseCommand

import requests
from bootstrap4 import bootstrap


class Command(BaseCommand):
    help = "Fetch bootstrap files as local static files"

    localurlbase = "/static/www/bootstrap4/"
    appbase = apps.get_app_config("www").path
    localfolder = f"{appbase}{localurlbase}"

    def handle(self, *args, **options):
        print(f"Fetching bootstrap4 files into folder: {self.localfolder}")
        newsettings = dict()
        for item in bootstrap.BOOTSTRAP4_DEFAULTS.items():
            key = item[0]
            # not interested in other settings
            if "_url" not in key:
                continue

            # some of them are empty
            val = item[1]
            if not val:
                continue

            # some have url and some href, handle both cases
            url = val.get("url")
            if url:
                filename = self._fetch_and_save(url)
                # build the settings section for it
                newsettings[key] = f"{self.localurlbase}{filename}"

            href = val.get("href")
            if href:
                filename = self._fetch_and_save(href)
                # build the settings section for it
                newsettings[key] = f"{self.localurlbase}{filename}"

        print("Done, now you can update your settings_local to use these files:")
        print("BOOTSTRAP4 = ")
        pprint.pprint(newsettings)

    def _fetch_and_save(self, url):
        """
        Fetch and save the file into target, return the saved filename
        """
        print(f"Fetching from url: {url}")
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        r = requests.get(url)
        with open(f"{self.localfolder}{filename}", "wb") as f:
            f.write(r.content)

        return filename
