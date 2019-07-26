from enum import Enum

from django.db import models


PROJECT_TYPE = (
    ("text_label", "Text Labeling"),
)


class Projects(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default="")
    type = models.CharField(
        choices=(PROJECT_TYPE),
        max_length=20
    )
