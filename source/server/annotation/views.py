from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from annotation.models import Projects
from annotation.serializers import ProjectsSerializer


def project_page(request, project):
    print("Project Number:", project, type(project))
    return render(request, 'project_page.html')


def project_action(request, project, action):
    print("Project Number:", project, type(project))
    print("Project Action:", action, type(action))
    actions_list = ["import"]
    if action not in actions_list:
        # return 404
        pass
    render_template = "project_{}.html".format(action)

    return render(request, render_template)


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
