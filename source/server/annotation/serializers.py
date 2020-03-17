from django.forms.models import model_to_dict
from rest_framework import serializers

from annotation import models


class ProjectsSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=models.PROJECT_TYPE)

    class Meta:
        model = models.Projects
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "type": {'read_only': True},
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

    class Meta:
        model = models.Documents
        exclude = ["project"]

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
