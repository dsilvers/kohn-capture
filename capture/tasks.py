import os
import subprocess

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from pathlib import Path
import shutil
import cv2

# from capture.models import KohnImage


@shared_task(bind=True, ignore_result=True, queue="messages")
def log_message(self, pk=None, message=None, level="info"):
    print(f"{pk} - {level} - {message}")

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("capture_kohn", {"type": "chat.message", "level": level, "message": message, "pk": pk })


@shared_task(ignore_result=True, queue="capture")
def capture_negative(ki_pk, image_raw_dest, image_jpg_dest):
    # log_message.delay(pk=ki_pk, message=f"Starting negative capture")
    output = subprocess.getoutput("sudo gphoto2 --auto-detect")
    if settings.NEGATIVE_CAMERA_NAME not in output:
        raise Exception(f"{settings.NEGATIVE_CAMERA_NAME} does not appear to be connected")

    tmp_path = f"/tmp/{ki_pk}"

    subprocess.getoutput(f'mkdir -p {tmp_path}; cd "{tmp_path}"; sudo gphoto2 -D && sudo gphoto2 --capture-image-and-download')

    jpg_file = f"{tmp_path}/capt0000.jpg"
    raw_file = f"{tmp_path}/capt0001.arw"

    if not os.path.isfile(jpg_file):
        raise Exception(f"{jpg_file} does not exist")

    if not os.path.isfile(raw_file):
        raise Exception(f"{raw_file} does not exist")

    # RAW should be retained
    shutil.copy(raw_file, image_raw_dest)
    os.remove(raw_file)

    # JPG shouold be inverted/flipped
    img = cv2.imread(jpg_file)
    img_inverted = cv2.bitwise_not(img)  # invert image
    img_normal = cv2.flip(img_inverted, 1)  # mirror image
    cv2.imwrite(image_jpg_dest, img_normal)
    os.remove(jpg_file)

    try:
        os.rmdir(tmp_path)
    except OSError:
        pass
