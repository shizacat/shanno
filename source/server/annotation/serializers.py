from rest_framework import serializers

from annotation.models import Projects


class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "type": {'read_only': True},
        }
