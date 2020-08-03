from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from . import views
from . import views_api

urlpatterns = [
    path('health', views.health),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path(
        'project_create/',
        TemplateView.as_view(template_name='project_create.html'),
        name='project_create'),
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
]

# API
router = routers.DefaultRouter()
router.register(r'project', views_api.ProjectViewSet)
router.register(r'document', views_api.DocumentSeqViewSet)
router.register(r'tl_label', views_api.TLLabelsViewSet)
router.register(r'tl_seq_label', views_api.TLSeqLabelViewSet)

urlpatterns += [
    path('api/', include(router.urls)),
    # extra
    path('api/project/<int:pk>/ds_import/', views_api.ProjectDSImport.as_view()),
    path('api/project/<int:pk>/ds_export/', views_api.ProjectDSExport.as_view()),
    path(
        "api/project/<int:pk>/documents_list/",
        views_api.ProjectActionDocumentList.as_view()
    ),
    path(
        "api/project/<int:pk>/tl_labels_list/",
        views_api.ProjectActionTLLabelList.as_view()
    ),
    path(
        "api/project/<int:pk>/permission/",
        views_api.ProjectPermission.as_view()
    ),
    path(
        "api/document/<int:pk>/labels/",
        views_api.DocumentSeqDcLabel.as_view()
    ),
]
