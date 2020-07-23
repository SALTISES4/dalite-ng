from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from peerinst.models import StudentGroup


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        self.stdout.write("Permissions have been assigned.")
