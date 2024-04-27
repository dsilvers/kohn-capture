import cv2
from django.conf import settings
from celery import shared_task


@shared_task(queue="darwin")
def ocr_image(filename):
    from ocrmac import ocrmac

    envelope_jpg = f"{settings.KOHN_IMAGE_PATH_JPG}/{filename}"

    # OCR that image using the mac chip photos magic
    annotations = ocrmac.OCR(envelope_jpg, language_preference=['en-US'], recognition_level="accurate").recognize()

    return annotations