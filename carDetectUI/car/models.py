from django.db import models

import os

from django.db import models
from django.utils.translation import gettext_lazy as _


class ImageModel(models.Model):
    image = models.ImageField(_("image"), upload_to='images')
    result_image = models.ImageField(_("Result Image"), upload_to='results', blank=True, null=True)
    
    detected_classes = models.JSONField(null=True, blank=True)
    class_counts = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def __str__(self):
        return str(os.path.split(self.image.path)[-1])
    


    

class VideoModel(models.Model):
    title = models.CharField(max_length=100)
    video = models.FileField(upload_to='videos/')
