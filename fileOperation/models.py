from django.db import models
from embed_video.fields import EmbedVideoField


class KO(models.Model):
    category1 = models.TextField()
    category2 = models.TextField()
    ko_number = models.CharField(max_length=50)
    description = models.TextField()


class QandA(models.Model):
    type = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()


class Item(models.Model):
    video = EmbedVideoField()
