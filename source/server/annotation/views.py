from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from annotation.models import Projects
from annotation.serializers import ProjectsSerializer

from annotation.models import Projects, PROJECT_TYPE


def project_action(request, project, action=None):
    actions_list = ["page", "import", "export", "settings"]

    if action is None:
        action = "page"

    if action not in actions_list:
        # return 404 !!!
        pass
    render_template = "project_{}.html".format(action)

    context = {
        "project": Projects.objects.get(pk=project),
    }

    return render(request, render_template, context)


# API
# ====
class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint"""
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
