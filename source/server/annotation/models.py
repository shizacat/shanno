import random
import string
import logging
from enum import Enum

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


PROJECT_TYPE = (
    ("text_label", "Text Labeling"),
    ("document_classificaton", "Document classification")
)

PROJECT_ROLES = (
    ("view", "Only view"),
    ("change", "Full access")
)


class Projects(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Project owner"
    )
    name = models.CharField("Project name", max_length=100)
    description = models.TextField(
        "Project description", default="", blank=True
    )
    type = models.CharField(
        "Project type",
        choices=(PROJECT_TYPE),
        max_length=50,
        # help_text="Project type"
    )


class ProjectsPermission(models.Model):
    project = models.ForeignKey(
        Projects, related_name='permissions', on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    role = models.CharField(max_length=50, choices=(PROJECT_ROLES))


class Documents(models.Model):
    """A document consists from a set of sequences"""
    project = models.ForeignKey(
        Projects, related_name='documents', on_delete=models.CASCADE
    )
    # Metadata of file
    meta = models.TextField(default='{}')
    # File name, from which the document was loaded
    file_name = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # if True this document is complete
    approved = models.BooleanField(default=False)

    # def __str__(self):
    #     return self.text[:50]

    def get_labels(self) -> list:
        """Get all labels for the whole doc

        Return:
            [
                {
                    "id": int,
                    "name": "",
                    "value: 0/1,
                }
            ]
        """
        result = []

        labels_all = TlLabels.objects.filter(
            project=self.project
        ).order_by('name')
        for label in labels_all:
            obj = None
            try:
                obj = DCDocLabel.objects.get(label=label, document=self)
            except DCDocLabel.DoesNotExist:
                pass
            value = 0
            if obj is not None:
                value = 1
            r = {
                "id": label.id,
                "name": label.name,
                "value": value
            }
            result.append(r)
        return result
    
    def labels_del(self):
        """Delete all labels"""
        try:
            DCDocLabel.objects.filter(document=self).delete()
        except DCDocLabel.DoesNotExist:
            pass


class Sequence(models.Model):
    document = models.ForeignKey(
        Documents, related_name='sequences', on_delete=models.CASCADE
    )
    text = models.TextField()
    meta = models.TextField(default='{}')
    # Sequence order in a document
    order = models.IntegerField(null=False, db_index=True, default=0)  # !!! delete default


# text_label
# Object label and for document_classificaton
class TlLabels(models.Model):
    """Contains a list of labels"""
    PREFIX_KEYS = (
        ('ctrl', 'ctrl'),
        ('shift', 'shift'),
    )
    SUFFIX_KEYS = tuple(
        (c, c) for c in string.ascii_lowercase
    )

    project = models.ForeignKey(
        Projects, related_name='labels', on_delete=models.CASCADE
    )
    # Name of label
    name = models.CharField(max_length=100)
    color_background = models.CharField(
        max_length=7,
        default='#209cee',
        validators=[
            RegexValidator(r'^#[0-9a-fA-F]{6}$')
        ]
    )
    color_text = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[
            RegexValidator(r'^#[0-9a-fA-F]{6}$')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prefix_key = models.CharField(
        max_length=10, blank=True, choices=PREFIX_KEYS
    )
    suffix_key = models.CharField(
        "Short key. If not specified than will be take free later.",
        max_length=1, blank=True, choices=SUFFIX_KEYS
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.suffix_key:
            pk = set(TlLabels.objects.filter(
                project=self.project).values_list("suffix_key", flat=True))
            keys = set(string.ascii_lowercase).difference(pk)
            if len(keys) > 0:
                self.suffix_key = keys.pop()
        # if not self.prefix_key:
        #     self.prefix_key = "ctrl"
        # Setup color
        if self.color_background == "#209cee":
            self.color_background = self._get_new_color_bg()
            self.color_text = self._get_new_color_text(self.color_background)

        super().save(*args, **kwargs)

    class Meta:
        unique_together = (
            ('project', 'name'),
            ('project', 'prefix_key', 'suffix_key'),
        )
    
    def _get_new_color_bg(self) -> str:
        """New color for background"""
        color = "#{:06x}".format(round(random.random() * 0xFFFFFF)).upper()
        return color
    
    def _get_new_color_text(self, color_bg: str) -> str:
        """New color for text on background color"""
        red = int(color_bg[1:3], 16)
        green = int(color_bg[3:5], 16)
        blue = int(color_bg[5:7], 16)
        
        if (((red * 299) + (green * 587) + (blue * 114)) / 1000) < 128:
            color = "#ffffff"
        else:
            color = "#000000"
        return color


class TlSeqLabel(models.Model):
    """Contains label position in sequence"""
    sequence = models.ForeignKey(
        Sequence, related_name='seqlabel1', on_delete=models.CASCADE
    )
    label = models.ForeignKey(
        TlLabels, related_name='seqlabel2', on_delete=models.CASCADE
    )
    offset_start = models.IntegerField(null=False, db_index=True)
    offset_stop = models.IntegerField(null=False)


# document_classificaton
class DCDocLabel(models.Model):
    """Contains label of documents"""
    document = models.ForeignKey(
        Documents, related_name='dl_doc', on_delete=models.CASCADE
    )
    label = models.ForeignKey(
        TlLabels, related_name='dl_label', on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (
            ('document', 'label'),
        )
