from django.core.management.base import BaseCommand
from django.conf import settings
import json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    def handle(self, *args, **options):
        from ocrmac import ocrmac

        for filename in options["filename"]:
            envelope_jpg = f"{settings.KOHN_IMAGE_PATH_JPG}/{filename}"

            # OCR that image using the mac chip photos magic
            annotations = ocrmac.OCR(envelope_jpg, language_preference=['en-US'], recognition_level="accurate").recognize()

            print(json.dumps(annotations))
