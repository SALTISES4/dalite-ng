# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import re

import bs4
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from peerinst.models import SaltiseMember


class Command(BaseCommand):
    help = (
        "Populate Saltise members from"
        " https://www.saltise.ca/community/saltise-innovators/"
    )

    def handle(self, *args, **kwargs):
        print("[*] Getting list of Saltise members", end="\r")
        resp = requests.get(
            "https://www.saltise.ca/community/saltise-innovators/"
        )
        soup = bs4.BeautifulSoup(resp.text, "html.parser")
        member_elements = [elem.a for elem in soup.find_all(class_="member")]
        members = [
            {
                "name": elem.span.text,
                "picture_link": "https://www.saltise.ca"
                + re.match(
                    r"^background-image: url\((.+)\);$", elem["style"]
                ).group(1),
            }
            for elem in member_elements
        ]
        n = len(members)
        for i, member in enumerate(members):
            print(
                "[*] Downloading Saltise member info ({{:>{}}}/{{}})".format(
                    len(str(n))
                )
                .format(i + 1, n)
                .ljust(80),
                end="\r",
            )
            if not SaltiseMember.objects.filter(name=member["name"]).exists():
                member_ = SaltiseMember.objects.create(name=member["name"])
                if "placehoder" not in member["picture_link"]:
                    resp = requests.get(member["picture_link"])
                    content = ContentFile(resp.content)
                    member_.picture.save(
                        os.path.basename(member["picture_link"]),
                        content,
                        save=True,
                    )
        print("[+] Populated db with Saltise members".ljust(80))
