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
            text = seq[0].text[:50]
        return text
