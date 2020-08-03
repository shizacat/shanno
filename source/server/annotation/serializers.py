import json
import logging

from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from rest_framework import serializers

from annotation import models
from libs.files import FilesBase


class ProjectsSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=models.PROJECT_TYPE)

    class Meta:
        model = models.Projects
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "type": {'read_only': True},
            "owner": {'read_only': True},
        }


class DocumentsSerializer(serializers.ModelSerializer):
    sequence_preview = serializers.SerializerMethodField()

    class Meta:
        model = models.Documents
        exclude = ["project"]

    def get_sequence_preview(self, obj):
        text = ""
        seq = models.Sequence.objects.filter(document=obj)[:1]
        if seq:
            text = seq[0].text[:200]
        return text


class DocumentsSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Documents
        exclude = ["project"]


class DocumentSeqSerializer(serializers.ModelSerializer):
    """Full document for annotation"""
    sequences = serializers.SerializerMethodField()
    meta = serializers.SerializerMethodField()

    class Meta:
        model = models.Documents
        exclude = ["project"]
    
    def get_meta(self, obj):
        if obj.meta is None:
            return {}
        return json.loads(obj.meta)

    def get_sequences(self, obj):
        result = []
        seqs = models.Sequence.objects.filter(document=obj).order_by("order")
        if not seqs:
            return result

        for seq in seqs:
            label_obj = models.TlSeqLabel.objects.filter(
                sequence=seq
            ).order_by("offset_start")
            d = model_to_dict(seq, fields=["id", "text", "meta", "order"])
            d.update({
                "labels": label_obj.values(
                    "id", "label", "offset_start", "offset_stop")
            })
            result.append(d)

        return result


class TLLabelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TlLabels
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "created_at": {'read_only': True},
            "updated_at": {'read_only': True},
        }


class TLSeqLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TlSeqLabel
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "created_at": {'read_only': True},
            "updated_at": {'read_only': True},
        }


# === For action
# Utils
def get_all_formats() -> list:
    """Return all formats"""
    formats_choice = set()
    for t in models.PROJECT_TYPE:
        formats_choice = formats_choice.union(
            set([(x[0], x[1]) for x in FilesBase.get_docs(t[0], "import")])
        )
    return list(formats_choice)


class ProjectDSImport(serializers.Serializer):
    files = serializers.FileField(help_text="File for import")
    format = serializers.ChoiceField(
        choices=get_all_formats(),
        help_text="Name format file"
    )


class ProjectsPermission(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=models.PROJECT_ROLES)
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username')

    class Meta:
        model = models.ProjectsPermission
        exclude = ["user", "project"]
        extra_kwargs = {
            "id": {'read_only': True},
        }


class DCDocLabelSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source='label.name', read_only=False, help_text="Name of label")
    value = serializers.ChoiceField(
        choices=[0, 1], help_text="Value label. 1 - set; 0 - unset.")
    
    class Meta:
        model = models.DCDocLabel
        exclude = ["document", "label"]
        extra_kwargs = {
            "id": {'read_only': True},
        }
