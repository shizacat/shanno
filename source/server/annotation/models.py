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
    document = models.ForeignKey(
        Documents, related_name='sequences', on_delete=models.CASCADE
    )
    text = models.TextField()
    meta = models.TextField(default='{}')
    # Порядок последовательностей в документе
    order = models.IntegerField(null=False, db_index=True, default=0)  # !!! delete default


# text_label
class TlLabels(models.Model):
    """Содержит список меток"""
    project = models.ForeignKey(
        Projects, related_name='labels', on_delete=models.CASCADE
    )
    # Название метки
    name = models.CharField(max_length=100)
    color_background = models.CharField(max_length=7, default='#209cee')
    color_text = models.CharField(max_length=7, default='#ffffff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (
            ('project', 'name'),
        )


class TlSeqLabel(models.Model):
    """Содержит позицию метки в последовательности"""
    sequence = models.ForeignKey(
        Sequence, related_name='seqlabel1', on_delete=models.CASCADE
    )
    label = models.ForeignKey(
        TlLabels, related_name='seqlabel2', on_delete=models.CASCADE
    )
    offset_start = models.IntegerField(null=False, db_index=True)
    offset_stop = models.IntegerField(null=False)
