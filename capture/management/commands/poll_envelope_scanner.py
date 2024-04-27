from django.core.management.base import BaseCommand
from time import sleep

import os
import subprocess
import uuid

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from pathlib import Path

from processing.models import KohnImage
from capture.tasks import capture_negative
from processing.tasks import ocr_image

import cv2
import shutil
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            sleep(0.2)
            scan_envelope()


def websocket_data(group=None, data={}):
    channel_layer = get_channel_layer()
    print(f"{group} - {data}")
    async_to_sync(channel_layer.group_send)("capture_kohn", {"type": "chat.message", "group": group, "data": data })


def scan_envelope():
    envelope_path = "/tmp/envelopes"
    random_uuid = str(uuid.uuid4())
    output_tiff = f"{envelope_path}/envelope-{random_uuid}.tiff"

    # Create temporary directory if one does not already exist
    Path(envelope_path).mkdir(parents=True, exist_ok=True)

    # Attempt to scan the image
    scanimage_result = subprocess.getoutput(f"sudo scanimage -d 'fujitsu:ScanSnap iX1400:1716779' --prepick On  --mode Color --resolution 600 --format tiff --ald=yes --swcrop=yes -o {output_tiff}")

    if "Document feeder out of documents" in scanimage_result:
        print("Nothing to scan")
        pass
    elif "open of device fujitsu" in scanimage_result:  # "failed"
        print("Scanner not found")
        pass
    else:
        print(f"Scan complete - {output_tiff}")

        websocket_data("clear", "please")

        process_kohn_image(output_tiff)


def process_kohn_image(envelope_scanned_tiff):
    ki = KohnImage.objects.create()

    Path(settings.KOHN_IMAGE_PATH_RAW).mkdir(parents=True, exist_ok=True)
    Path(settings.KOHN_IMAGE_PATH_JPG).mkdir(parents=True, exist_ok=True)

    envelope_jpg = f"{settings.KOHN_IMAGE_PATH_JPG}/{ki.pk}-envelope.jpg"
    negative_jpg = f"{settings.KOHN_IMAGE_PATH_JPG}/{ki.pk}-image.jpg"

    negative_raw = f"{settings.KOHN_IMAGE_PATH_RAW}/{ki.pk}-negative.arw"
    envelope_tiff = f"{settings.KOHN_IMAGE_PATH_RAW}/{ki.pk}-envelope.tiff"

    # Envelope
    # Copy TIFF to a JPG
    # Resize TIFF to a smaller JPG
    resize_envelope(envelope_scanned_tiff, envelope_jpg, envelope_tiff)
    print(envelope_jpg)

    websocket_data("envelope", f"{ki.pk}-envelope.jpg")

    # Capture negative
    capture_negative(ki.pk, negative_raw, negative_jpg)
    print(negative_raw)
    print(negative_jpg)

    websocket_data("image", f"{ki.pk}-image.jpg")

    # Do OCR on mac
    envelope_ocr_str = subprocess.getoutput(f"ssh kohn@{settings.HOST_IP} 'cd Projects/kohn; /Users/kohn/Projects/kohn/.direnv/python-3.12/bin/python ./manage.py ocr_image {ki.pk}-envelope.jpg' ")
    ki.envelope_ocr = json.loads(envelope_ocr_str)
    ki.envelope_ocr_completed = True

    #negative_ocr_str = subprocess.getoutput(f"ssh kohn@{settings.HOST_IP} 'cd Projects/kohn; /Users/kohn/Projects/kohn/.direnv/python-3.12/bin/python ./manage.py ocr_image {ki.pk}-image.jpg' ")
    #ki.negative_ocr = json.loads(negative_ocr_str)
    #ki.negative_ocr_completed = True

    ki.save()

    print(ki.envelope_ocr)
    # print(ki.negative_ocr)

    text_annotations = []
    for annotation in ki.envelope_ocr:
        text_annotations.append(annotation[0])
    websocket_data(group="annotations", data={"text": text_annotations})

    print("done")


def resize_envelope(envelope_scanned_tiff, envelope_jpg, envelope_tiff):
    image = cv2.imread(envelope_scanned_tiff)

    # height = image.shape[0]
    # width = image.shape[1]

    resize_to_width = 1600

    scale_factor = resize_to_width / image.shape[1]
    new_height = int(image.shape[0] * scale_factor)
    new_width = resize_to_width
    dimensions = (new_width, new_height)

    new_image = cv2.resize(image, dimensions, interpolation=cv2.INTER_AREA)  # INTER_AREA for smaller
    cv2.imwrite(envelope_jpg, new_image)

    shutil.copy(envelope_scanned_tiff, envelope_tiff)
    os.remove(envelope_scanned_tiff)