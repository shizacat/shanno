from rest_framework import serializers

from annotation.models import Projects, PROJECT_TYPE


class ProjectsSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=PROJECT_TYPE)

    class Meta:
        model = Projects
        exclude = []
        extra_kwargs = {
            "id": {'read_only': True},
            "type": {'read_only': True},
        }
