import io
import os
import json
import logging
from copy import deepcopy
from collections import OrderedDict

from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.db import transaction
from django.db.models import Subquery, OuterRef
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status, parsers, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler
from rest_framework.decorators import action, permission_classes
from rest_framework import permissions, pagination, mixins
from rest_framework import exceptions as rest_except
from rest_framework.exceptions import APIException
from rest_framework.schemas.openapi import AutoSchema
from drf_yasg.inspectors.view import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi

from annotation import models
from annotation.exceptions import AnnotationBaseExcept, FileParseException
from annotation.models import Projects, PROJECT_TYPE
import annotation.serializers as anno_serializer
from annotation.serializers import ProjectsSerializer, DocumentsSerializer
from libs.files import FilesBase
from libs.utils import is_int


# Utils
# -------------------

def get_generic_error_schema(name="API Error"):
    return openapi.Schema(
        name,
        type=openapi.TYPE_OBJECT,
        properties={
            "detail": openapi.Schema(
                type=openapi.TYPE_STRING, description="Error details"
            ),
            # 'code': openapi.Schema(
            #     type=openapi.TYPE_STRING, description='Error code'),
        },
        required=["detail"],
    )


def custom_exception_handler(exc, context):
    """Convert dict and list to string"""
    if not hasattr(exc, "detail"):
        exc.detail = str(exc)
    if isinstance(exc.detail, list):
        exc.detail = " ".join(exc.detail)
    if isinstance(exc.detail, dict):
        s = ". ".join(["{}: {}".format(k, v) for k, v in exc.detail.items()])
        exc.detail = s

    response = exception_handler(exc, context)
    return response


# API
# -------------------

class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for work with project"""

    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(responses={"400": get_generic_error_schema()})
    def create(self, request, *args, **kwargs):
        """Create the project"""
        if request.data["type"] not in [x[0] for x in models.PROJECT_TYPE]:
            raise rest_except.ParseError(_("Type not found"))
        description = request.data.get("description")
        if description is None:
            description = ""

        project = models.Projects.objects.create(
            name=request.data["name"],
            description=description,
            type=request.data["type"],
            owner=request.user,
        )

        serializer = self.serializer_class(project, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={"400": get_generic_error_schema()})
    def list(self, request, *args, **kwargs):
        """List of all projects"""
        if isinstance(request.user, AnonymousUser):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # share projects
        o_pr_id = models.ProjectsPermission.objects.filter(
            user=request.user
        ).values_list("project", flat=True)

        q1 = models.Projects.objects.filter(owner=request.user)
        q2 = models.Projects.objects.filter(pk__in=o_pr_id)
        queryset = q1 | q2

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success"},
    )
    def destroy(self, request, *args, **kwargs):
        """Delete the project"""
        obj = self.get_object()
        if obj.owner != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses={
            "200": anno_serializer.DocumentsSerializerSimple(many=True),
            "400": get_generic_error_schema(),
        },
        manual_parameters=[
            openapi.Parameter(
                "approved",
                openapi.IN_QUERY,
                description="If specified then will filter by field 'approved'",
                type=openapi.TYPE_INTEGER,
                required=False,
                enum=[0, 1],
            ),
        ],
    )
    @action(detail=True, methods=["get"])
    def documents_list_simple(self, request, pk=None):
        """Get documents without content
        Query:
            approved - If specified then will filter by field 'approved'
                0 - Not verifed only
                1 - Verifed only
        """
        afilter = {"project": self.get_object()}
        f_approved = request.query_params.get("approved")
        if f_approved is not None and is_int(f_approved):
            afilter["approved"] = bool(int(f_approved))

        docs = models.Documents.objects.filter(**afilter).order_by("file_name")

        serializer = anno_serializer.DocumentsSerializerSimple(docs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={
            "200": openapi.Schema(
                "Success",
                type=openapi.TYPE_OBJECT,
                properties={
                    "docs_approve_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Count approved documents",
                    ),
                    "docs_total": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Total documents"
                    ),
                },
                required=["docs_approve_count", "docs_total"],
            ),
            "400": get_generic_error_schema(),
        },
    )
    @action(detail=True, methods=["get"])
    def info(self, request, pk=None):
        """Get info about approved documents in project: count and total"""
        docs_approved = models.Documents.objects.filter(
            project=self.get_object(), approved=True
        ).count()
        docs_total = models.Documents.objects.filter(
            project=self.get_object()
        ).count()
        r = {"docs_approve_count": docs_approved, "docs_total": docs_total}
        return Response(r, status=200)


@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve document",
        responses={
            "400": get_generic_error_schema(),
            "404": get_generic_error_schema(),
        },
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Delete document",
        responses={"204": "Success delete", "400": get_generic_error_schema()},
    ),
)
class DocumentSeqViewSet(
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    queryset = models.Documents.objects.all()
    serializer_class = anno_serializer.DocumentSeqSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success change"},
        request_body=no_body,
    )
    @action(detail=True, methods=["post"])
    def approved(self, request, pk=None):
        """Set approved"""
        doc = self.get_object()
        doc.approved = True
        doc.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success change"},
        request_body=no_body,
    )
    @action(detail=True, methods=["post"])
    def unapproved(self, request, pk=None):
        """Unset approved"""
        doc = self.get_object()
        doc.approved = False
        doc.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success reset"},
        request_body=no_body,
    )
    @action(detail=True, methods=["post"])
    def reset(self, request, pk=None):
        """Delete the all TL Labels in document"""
        doc = self.get_object()
        for sequence in models.Sequence.objects.filter(document=doc):
            models.TlSeqLabel.objects.filter(sequence=sequence).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentSeqDcLabel(generics.GenericAPIView):
    """Work with Documnt Classifier Label for document"""

    queryset = models.Documents.objects.all()
    serializer_class = anno_serializer.DocumentSeqSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success set",},
        request_body=openapi.Schema(
            in_=openapi.IN_BODY,
            type=openapi.TYPE_OBJECT,
            properties={
                "label_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Id label"
                ),
                "value": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Value of label (0/1)",
                    enum=[0, 1],
                ),
            },
            required=["label_id", "value"],
        ),
    )
    def post(self, request, pk=None):
        """Set label for document"""
        doc = self.get_object()

        label_id = request.data.get("label_id", None)
        if label_id is None:
            raise rest_except.ParseError(_("Label not found"))
        label = models.TlLabels.objects.get(pk=label_id)

        try:
            value = int(request.data.get("value", None))
            if value not in [0, 1]:
                raise rest_except.ParseError(_("Value label not 0/1"))
        except TypeError:
            raise rest_except.ParseError(_("Value not convert to int"))

        obj = None
        try:
            obj = models.DCDocLabel.objects.get(label=label, document=doc)
        except models.DCDocLabel.DoesNotExist:
            pass

        if value == 1:
            # set
            if obj is None:
                models.DCDocLabel.objects.create(label=label, document=doc)
        if value == 0:
            if obj is not None:
                obj.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        responses={
            "400": get_generic_error_schema(),
            "200": anno_serializer.DCDocLabelSerializer(many=True),
        },
        request_body=no_body,
    )
    def get(self, request, pk=None):
        """Return all list labels for documents."""
        resp = Response(self.get_object().get_labels(), status=200)
        return resp
    
    @swagger_auto_schema(
        responses={"400": get_generic_error_schema(), "204": "Success delete"},
        request_body=no_body,
    )
    def delete(self, request, pk=None):
        """Delete all label for documents."""
        self.get_object().labels_del()
        resp = Response(status=status.HTTP_204_NO_CONTENT)
        return resp


# Permissions
# ==========

# class RBACPermission(permissions.BasePermission):
#     def has_permission(self, request, view):
#         print(type(view))
#         project = None
#         if type(view) == TLLabelsViewSet:
#             project = models.Projects.objects.get(pk=request.data["project"])
#         return self._check(request, project)

#     def has_object_permission(self, request, view, obj):
#         project = None
#         if type(obj) == models.TlLabels:
#             project = obj.project
#         return self._check(request, project)

#     def _check(self, request, project):
#         if project is None:
#             return False

#         if request.user == project.owner:
#             return True
#         return False


# @permission_classes([RBACPermission])
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Create label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partial update label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Delete label",
        responses={"204": "Success delete", "400": get_generic_error_schema(),},
    ),
)
class TLLabelsViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    """Work with label"""

    queryset = models.TlLabels.objects.all()
    serializer_class = anno_serializer.TLLabelsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve TL-Seq-Label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update TL-Seq-Label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partial update TL-Seq-Label",
        responses={"400": get_generic_error_schema(),},
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Delete TL-Seq-Label",
        responses={"204": "Success delete", "400": get_generic_error_schema(),},
    ),
)
class TLSeqLabelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    queryset = models.TlSeqLabel.objects.all()
    serializer_class = anno_serializer.TLSeqLabelSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        responses={
            "200": anno_serializer.TLSeqLabelSerializer(many=True),
            # "201": "Created success",
            "400": get_generic_error_schema(),
        },
    )
    def create(self, request):
        """Creates the object 'Seq labels' and returns their as array"""
        result = []

        offset_start = request.data["offset_start"]
        offset_stop = request.data["offset_stop"]
        seq_id = request.data["sequence"]
        label_id = request.data["label"]

        text = models.Sequence.objects.filter(pk=seq_id).values("text")
        if len(text) != 1:
            return Response(status=404)
        text = text[0].get("text", "")

        offset_chunk = offset_start
        for item in text[offset_start:offset_stop].split(" "):
            try:
                r = models.TlSeqLabel.objects.create(
                    offset_start=offset_chunk,
                    offset_stop=offset_chunk + len(item),
                    sequence=models.Sequence.objects.get(pk=seq_id),
                    label=models.TlLabels.objects.get(pk=label_id),
                )
            except models.TlLabels.DoesNotExist:
                raise rest_except.ParseError(_("Label not found"))
            offset_chunk = offset_chunk + len(item) + 1

            serializer = anno_serializer.TLSeqLabelSerializer(r)
            result.append(serializer.data)
        return Response(result)


# Extra


class ProjectHelps:
    def __init__(self, project_id):
        self.project = models.Projects.objects.get(pk=project_id)

    # ==/ Block: Labels
    def _label_get_handler(self):
        map = {
            "text_label": self._process_labels_tl,
            "document_classificaton": self._process_labels_dc,
        }
        label_handler = map.get(self.project.type)
        if label_handler is None:
            raise AnnotationBaseExcept(_("Did not find handler for labels"))
        return label_handler

    def _label_doc_get_handler(self):
        map = {
            "text_label": self._process_labels_doc_tl,
            "document_classificaton": self._process_labels_doc_dc,
        }
        label_handler = map.get(self.project.type)
        if label_handler is None:
            raise AnnotationBaseExcept(_("Did not find handler for labels doc"))
        return label_handler

    def _process_labels_tl(self, labels, seq):
        """Process labels for text labels"""
        # Create new label
        labels_uniq = set()
        for tag, _, _ in labels:
            labels_uniq.add(tag)

        all_label_name = models.TlLabels.objects.filter(
            project=self.project
        ).values_list("name", flat=True)

        for label in list(labels_uniq):
            if label in all_label_name:
                continue
            try:
                models.TlLabels.objects.create(project=self.project, name=label)
            except ValidationError:
                pass

        # Add label for sequence
        for tag, char_left, char_right in labels:
            models.TlSeqLabel.objects.create(
                sequence=seq,
                label=models.TlLabels.objects.get(
                    project=self.project, name=tag
                ),
                offset_start=char_left,
                offset_stop=char_right,
            )

    def _process_labels_dc(self, labels, seq):
        pass

    def _process_labels_doc_tl(self, labels, doc):
        pass

    def _process_labels_doc_dc(self, labels, doc):
        labels_uniq = set()
        for tag, _ in labels:
            labels_uniq.add(tag)

        all_label_name = models.TlLabels.objects.filter(
            project=self.project
        ).values_list("name", flat=True)

        for label in list(labels_uniq):
            if label in all_label_name:
                continue
            try:
                models.TlLabels.objects.create(project=self.project, name=label)
            except ValidationError:
                pass

        # Add label for doc
        for tag, value in labels:
            models.DCDocLabel.objects.create(
                document=doc,
                label=models.TlLabels.objects.get(
                    project=self.project, name=tag
                ),
            )

    # ==/ End Block

    def _export_handler(self):
        """Iteration documents for export process"""
        docs = models.Documents.objects.filter(project=self.project).order_by(
            "file_name"
        )
        project_type = self.project.type

        for doc in docs:
            data = []
            labels_on_doc = []

            if project_type == "document_classificaton":
                for x in doc.get_labels():
                    labels_on_doc.append((x["name"], x["value"]))

            seqs = models.Sequence.objects.filter(document=doc).order_by(
                "order"
            )
            for idx, seq in enumerate(seqs):
                labels = []
                if project_type == "text_label":
                    labels_obj = models.TlSeqLabel.objects.filter(
                        sequence=seq
                    ).order_by("offset_start")
                    for lb_seq in labels_obj:
                        labels.append(
                            (
                                lb_seq.label.name,
                                lb_seq.offset_start,
                                lb_seq.offset_stop,
                            )
                        )
                data.append((idx, seq.text, labels))

            yield data, json.loads(doc.meta), doc.file_name, labels_on_doc


class ProjectDSImport(generics.GenericAPIView):
    parser_classes = (parsers.MultiPartParser,)
    serializer_class = anno_serializer.ProjectDSImport
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={"204": "Success import", "400": get_generic_error_schema(),},
    )
    def put(self, request, pk=None):
        """Import file/files in dataset"""
        try:
            file_obj = request.FILES.get("files", None)
            file_format = request.data.get("format", None)
            proj_helper = ProjectHelps(pk)
            # project = models.Projects.objects.get(pk=pk)
        except models.Projects.DoesNotExist:
            raise rest_except.ParseError(_("Project not found"))

        if file_obj is None:
            raise rest_except.ParseError(_("File not found"))

        file_handler = FilesBase.factory(
            file_format, proj_helper.project.type, "import", file_obj
        )
        if file_handler is None:
            raise rest_except.ParseError(_("Format not exists"))

        try:
            # Select process labels
            label_handler = proj_helper._label_get_handler()
            label_doc_handler = proj_helper._label_doc_get_handler()

            with transaction.atomic():
                for data, meta, file_name, lb_doc in file_handler.import_ds():
                    # Create doc
                    doc = models.Documents.objects.create(
                        project=proj_helper.project,
                        file_name=os.path.splitext(file_name)[0],
                        meta=json.dumps(meta),
                    )
                    # Create seqences
                    for index, text, labels in data:
                        seq = models.Sequence.objects.create(
                            document=doc, text=text, order=index
                        )
                        # Create labels for seq
                        label_handler(labels, seq)
                    # Create label for doc
                    label_doc_handler(lb_doc, doc)
        except FileParseException as e:
            raise rest_except.ParseError(str(e))
        except AnnotationBaseExcept as e:
            raise rest_except.ParseError(str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return None


class ProjectDSExport(generics.GenericAPIView, ProjectHelps):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    serializer_class = None

    @swagger_auto_schema(
        produces="application/zip",
        responses={
            "200": openapi.Response(
                description="Content-Type: application/zip",
                schema=openapi.Schema(type=openapi.TYPE_FILE),
            ),
            "400": get_generic_error_schema(),
        },
        manual_parameters=[
            openapi.Parameter(
                "exformat",
                openapi.IN_QUERY,
                description="Format file",
                type=openapi.TYPE_STRING,
                required=True,
                enum=[x[0] for x in anno_serializer.get_all_formats()],
            )
        ],
    )
    def get(self, request, pk=None):
        """Export documents from dataset"""
        # Query:
        #     exformat - The format exported files
        try:
            proj_helper = ProjectHelps(pk)
        except models.Projects.DoesNotExist:
            raise rest_except.ParseError(_("Project not found"))

        exformat = request.query_params.get("exformat")

        file_handler = FilesBase.factory(
            exformat, proj_helper.project.type, "export", None
        )
        if file_handler is None:
            raise rest_except.ParseError(_("Format not exists"))

        response = HttpResponse(
            file_handler.export_ds(proj_helper._export_handler),
            content_type="application/zip",
        )
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            "export.zip"
        )
        return response

    def get_queryset(self):
        return None


class ProjectActionDocumentList(generics.GenericAPIView):
    """"""

    queryset = Projects.objects.all()
    serializer_class = DocumentsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = pagination.PageNumberPagination

    @swagger_auto_schema(
        responses={
            "400": get_generic_error_schema(),
            "404": get_generic_error_schema("Page not found"),
        },
        manual_parameters=[
            openapi.Parameter(
                "approved",
                openapi.IN_QUERY,
                description="If specified then will filter by field 'approved'",
                type=openapi.TYPE_INTEGER,
                required=False,
                enum=[0, 1],
            ),
        ],
    )
    def get(self, request, pk=None):
        """Get list documents with content by page
        Query:
            approved - If specified then will filter by field 'approved'
                0 - Not verifed only
                1 - Verifed only
        """
        try:
            project = models.Projects.objects.get(pk=pk)
        except models.Projects.DoesNotExist:
            raise rest_except.ParseError(_("Project not found"))
        afilter = {"project": project}
        f_approved = request.query_params.get("approved")
        if f_approved is not None and is_int(f_approved):
            afilter["approved"] = bool(int(f_approved))

        docs = models.Documents.objects.filter(**afilter).order_by("file_name")
        docs_page = self.paginate_queryset(docs)

        if docs_page is not None:
            serializer = DocumentsSerializer(docs_page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentsSerializer(docs, many=True)
        return Response(serializer.data, status=200)


class ProjectActionTLLabelList(generics.GenericAPIView):
    """"""

    queryset = Projects.objects.all()
    serializer_class = anno_serializer.TLLabelsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        responses={
            "200": anno_serializer.TLLabelsSerializer(many=True),
            "400": get_generic_error_schema(),
        },
    )
    def get(self, request, pk=None):
        """Get list labels for project"""
        try:
            project = models.Projects.objects.get(pk=pk)
        except models.Projects.DoesNotExist:
            raise rest_except.ParseError(_("Project not found"))
        labels = models.TlLabels.objects.filter(project=project).order_by("id")

        serializer = anno_serializer.TLLabelsSerializer(labels, many=True)
        return Response(serializer.data)


class ProjectPermission(generics.GenericAPIView):
    """"""

    queryset = Projects.objects.all()
    serializer_class = anno_serializer.ProjectsPermission
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(responses={"400": get_generic_error_schema(),},)
    def get(self, request, pk=None):
        """Get list permissions"""
        project = self.get_project(pk)
        perm = models.ProjectsPermission.objects.filter(
            project=self.get_object()
        )
        serializer = self.serializer_class(perm, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        responses={
            "201": "Created success",
            # "201": openapi.Schema(
            #     type=openapi.TYPE_OBJECT,
            #     properties={
            #         'role': openapi.Schema(
            #             type=openapi.TYPE_STRING,
            #             description='Name of role',
            #             enum=[x[0] for x in models.PROJECT_ROLES]),
            #         'username': openapi.Schema(
            #             type=openapi.TYPE_STRING, description='User name'),
            #     },
            #     required=['username', "role"]
            # ),
            "400": get_generic_error_schema(),
        },
    )
    def post(self, request, pk=None):
        """Add rights for user"""
        project = self.get_project(pk)
        # --- Auth
        # if self.get_object().owner != request.user:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # --- Checks
        username = request.data.get("username")
        role = request.data.get("role")

        if username is None:
            raise rest_except.ParseError(
                _("The field '{}' is incorrectly filled").format("username")
            )
        if role is None:
            raise rest_except.ParseError(
                _("The field '{}' is incorrectly filled").format("role")
            )

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            raise rest_except.ParseError(
                _("'{}'. User not found").format(username)
            )

        if user_obj == project.owner:
            raise rest_except.ParseError(_("The project owner selected"))

        if role not in [x[0] for x in models.PROJECT_ROLES]:
            raise rest_except.ParseError(_("Unknown role"))

        try:
            perm = models.ProjectsPermission.objects.get(
                project=project, user=user_obj
            )
        except models.ProjectsPermission.DoesNotExist:
            perm = None

        # --- Action
        if perm is None:
            # create
            perm = models.ProjectsPermission.objects.create(
                project=project, user=user_obj, role=role
            )
            return Response(status=status.HTTP_201_CREATED)
        else:
            # update
            perm.role = role
            perm.save()
            serializer = self.serializer_class(perm)
            return Response(serializer.data, status=200)

    @swagger_auto_schema(responses={"400": get_generic_error_schema(),},)
    def put(self, request, pk=None):
        """Update permission"""
        return self.post(request, pk)

    @swagger_auto_schema(
        responses={"204": "Success delete", "400": get_generic_error_schema(),},
        request_body=openapi.Schema(
            in_=openapi.IN_BODY,
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User name"
                ),
            },
            required=["username"],
        ),
    )
    def delete(self, request, pk=None):
        """Delete permission for user"""
        # --- Auth
        # if self.get_object().owner != request.user:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # --- Check
        project = self.get_project(pk)
        username = request.data.get("username")

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            raise rest_except.ParseError(
                _("'{}'. User not found").format(username)
            )

        try:
            perm = models.ProjectsPermission.objects.get(
                project=project, user=user_obj
            )
            perm.delete()
        except models.ProjectsPermission.DoesNotExist:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_project(self, pk):
        try:
            project = models.Projects.objects.get(pk=pk)
        except models.Projects.DoesNotExist:
            raise rest_except.ParseError(_("Project not found"))
        return project
