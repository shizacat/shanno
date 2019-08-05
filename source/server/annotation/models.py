from enum import Enum

from django.db import models


PROJECT_TYPE = (
    ("text_label", "Text Labeling"),
)


class Projects(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default="", blank=True)
    type = models.CharField(
        choices=(PROJECT_TYPE),
        max_length=20
    )


class Documents(models.Model):
    """Документ состоит из набора последовательностей"""
    project = models.ForeignKey(
        Projects, related_name='documents', on_delete=models.CASCADE
    )
    # Мета данные файла
    meta = models.TextField(default='{}')
    # Имя файла, из которого был загружен документ
    file_name = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return self.text[:50]


class Sequence(models.Model):
    text = models.TextField()
    document = models.ForeignKey(
        Documents, related_name='sequences', on_delete=models.CASCADE
    )
    meta = models.TextField(default='{}')
