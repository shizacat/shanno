import string
from enum import Enum

from django.db import models
from django.conf import settings


PROJECT_TYPE = (
    ("text_label", "Text Labeling"),
)

PROJECT_ROLES = (
    ("view", "Only view"),
    ("change", "Full access")
)


class Projects(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(default="", blank=True)
    type = models.CharField(
        choices=(PROJECT_TYPE),
        max_length=20
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


class Sequence(models.Model):
    document = models.ForeignKey(
        Documents, related_name='sequences', on_delete=models.CASCADE
    )
    text = models.TextField()
    meta = models.TextField(default='{}')
    # Sequence order in a document
    order = models.IntegerField(null=False, db_index=True, default=0)  # !!! delete default


# text_label
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
    color_background = models.CharField(max_length=7, default='#209cee')
    color_text = models.CharField(max_length=7, default='#ffffff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prefix_key = models.CharField(
        max_length=10, blank=True, choices=PREFIX_KEYS
    )
    suffix_key = models.CharField(
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
        super().save(*args, **kwargs)

    class Meta:
        unique_together = (
            ('project', 'name'),
            ('project', 'prefix_key', 'suffix_key'),
        )


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
