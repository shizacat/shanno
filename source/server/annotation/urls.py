from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'project', views.ProjectViewSet)
router.register(r'document', views.DocumentSeqViewSet)
router.register(r'tl_label', views.TLLabelsViewSet)

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path(
        'projects/',
        TemplateView.as_view(template_name='projects.html'),
        name='projects'),
    path(
        'projects/<int:project>/',
        views.project_action,
        name='projects_page'
    ),
    path(
        'projects/<int:project>/<action>',
        views.project_action,
        name='projects_action'
    ),
    path('api/', include(router.urls)),
    # path(
    #     'api-auth/',
    #     include('rest_framework.urls', namespace='rest_framework'))
]
