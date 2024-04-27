from django.db import models


class KohnImage(models.Model):
    negative_ocr = models.JSONField(default=list)
    negative_ocr_completed = models.BooleanField(default=False)
    envelope_ocr = models.JSONField(default=list)
    envelope_ocr_completed = models.BooleanField(default=False)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
