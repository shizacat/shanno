import io
import os
import json
import logging
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
from collections import OrderedDict

from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.db import transaction
from django.db.models import Subquery, OuterRef
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action, permission_classes
from rest_framework import permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.utils.translation import gettext_lazy as _

from annotation import models
from annotation.exceptions import AnnotationBaseExcept, FileParseException
from annotation.models import Projects, PROJECT_TYPE
import annotation.serializers as anno_serializer
from annotation.serializers import ProjectsSerializer, DocumentsSerializer
from libs.files import FilesBase

import conllu


def health(request):
    response = HttpResponse(
        "OK",
        content_type="text/plain",
        status=200
    )
    return response


@login_required
def project_action(request, project, action=None):
    # dict: name_action -> name_suffix_template
    # Action and menu setting different for type projects
    # suffix - used for make template name
    # name - showed name on html page
    # level - number of menu; 0 not show
    # pos - position

    actions_list_map = {
        None: {
            "suffix": "page",
            "name": _("Info"),
            "level": 1,
            "url": "/projects/{}/".format(project),
            "pos": 1,
        },
        "import": {
            "suffix": "import",
            "name": _("Import"),
            "level": 1,
            "url": "import",
            "pos": 2,
        },
        "export": {
            "suffix": "export",
            "name": _("Export"),
            "level": 1,
            "url": "export",
            "pos": 3,
        },
        "settings": {
            "suffix": "settings",
            "name": _("Settings"),
            "level": 3,
            "url": "settings",
            "pos": 1,
        },
    }

    actions_list_map_tl = {
        "annotation": {
            "suffix": "tl_annotation",
            "name": _("Annotation"),
            "level": 0,
            "url": "",
            "pos": 1,
        },
        "tl-labels": {
            "suffix": "tl_labels",
            "name": _("Labels"),
            "level": 2,
            "url": "tl-labels",
            "pos": 1,
        },
    }

    actions_list_map_dc = {
        "annotation": {
            "suffix": "dc_annotation",
            "name": _("Annotation"),
            "level": 0,
            "url": "",
            "pos": 1,
        },
        "dc-labels": {
            "suffix": "tl_labels",
            "name": _("Labels"),
            "level": 2,
            "url": "dc-labels",
            "pos": 1,
        },
    }

    # main
    actions_map = deepcopy(actions_list_map)
    project_obj = Projects.objects.get(pk=project)

    if project_obj.type == "text_label":
        actions_map.update(actions_list_map_tl)
    
    if project_obj.type == "document_classificaton":
        actions_map.update(actions_list_map_dc)
    
    if action not in actions_map.keys():
        raise Http404("Project action not found")

    render_template = "project_{}.html".format(actions_map.get(action)["suffix"])

    context = {
        "project": project_obj,
        "actions_map": OrderedDict(
            sorted(actions_map.items(), key=lambda t: t[1]["pos"])
        ),
    }
    if action in ["import", "export"]:
        context["format_docs"] = FilesBase.get_docs(project_obj.type, action)

    return render(request, render_template, context)


# API
# ====
class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for project

    Action:
        ds_import - Imports a dataset file
            PUT multipart:
            * files - file for import
            * format - string with the necessary format (conllup)

        documents_list - list of documents in project
            GET json
            Returns pages by 10th (?page)

        documents_list_simple - list of documents in project
            identifiers only

        tl_labels_list - TL, list of labels for project
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer
    # pagination_class = None

    def create(self, request, *args, **kwargs):
        project = models.Projects.objects.create(
            name=request.data["name"],
            description=request.data.get("description", ""),
            type=request.data["type"],
            owner=request.user
        )

        serializer = self.serializer_class(project, many=False)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser):
            return Response(status=status.HTTP_403_FORBIDDEN)

        o_pr_id = models.ProjectsPermission.objects.filter(
            user=request.user
        ).values_list('project', flat=True)

        q1 = models.Projects.objects.filter(owner=request.user)
        q2 = models.Projects.objects.filter(pk__in=o_pr_id)
        queryset = q1 | q2

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'])
    def ds_import(self, request, pk=None):
        file_obj = request.FILES.get("files", None)
        file_format = request.data.get("format", None)
        project_type = self.get_object().type

        if file_obj is None:
            return Response(
                _("File not found"), status=status.HTTP_400_BAD_REQUEST)
            
        file_handler = FilesBase.factory(
            file_format, project_type, "import", file_obj
        )
        if file_handler is None:
            return Response(
                _("Format not exists"), status=status.HTTP_400_BAD_REQUEST)

        try:
            # Select process labels
            label_handler = self._label_get_handler(project_type)
            label_doc_handler = self._label_doc_get_handler(project_type)

            with transaction.atomic():
                for data, meta, file_name, lb_doc in file_handler.import_ds():
                    # Create doc
                    doc = models.Documents.objects.create(
                        project=self.get_object(),
                        file_name=os.path.splitext(file_name)[0],
                        meta=json.dumps(meta)
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
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except AnnotationBaseExcept as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def ds_export(self, request, pk=None):
        """
        Query:
            exformat - The format exported files
        """
        exformat = request.query_params.get("exformat")        
        project_type = self.get_object().type

        file_handler = FilesBase.factory(exformat, project_type, "export", None)
        if file_handler is None:
            return Response(
                _("Format not exists"), status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(
            file_handler.export_ds(self._export_handler),
            content_type='application/zip'
        )
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            "export.zip"
        )
        return response

    @action(detail=True, methods=['get'])
    def documents_list(self, request, pk=None):
        """
        Query:
            approved - If specified then will filter by field 'approved'
                0 - Not verifed only
                1 - Verifed only
        """
        afilter = {
            "project": self.get_object()
        }
        f_approved = request.query_params.get("approved")
        if f_approved is not None and self.is_int(f_approved):
            afilter["approved"] = bool(int(f_approved))

        docs = models.Documents.objects.filter(**afilter).order_by("file_name")
        docs_page = self.paginate_queryset(docs)

        if docs_page is not None:
            serializer = DocumentsSerializer(docs_page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentsSerializer(docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents_list_simple(self, request, pk=None):
        """
        Query:
            approved - If specified then will filter by field 'approved'
                0 - Not verifed only
                1 - Verifed only
        """
        afilter = {
            "project": self.get_object()
        }
        f_approved = request.query_params.get("approved")
        if f_approved is not None and self.is_int(f_approved):
            afilter["approved"] = bool(int(f_approved))

        docs = models.Documents.objects.filter(**afilter).order_by("file_name")

        serializer = anno_serializer.DocumentsSerializerSimple(docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents_all_is_approved(self, request, pk=None):
        """Total verified"""
        docs_approved = models.Documents.objects.filter(
            project=self.get_object(), approved=True
        ).count()
        docs_total = models.Documents.objects.filter(
            project=self.get_object()
        ).count()
        r = {
            "count": docs_approved,
            "total": docs_total
        }
        return Response(r, status=200)

    @action(detail=True, methods=['get'])
    def tl_labels_list(self, request, pk=None):
        labels = models.TlLabels.objects.filter(
            project=self.get_object()
        ).order_by("id")

        serializer = anno_serializer.TLLabelsSerializer(labels, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post', 'put', 'delete'])
    def permission(self, request, pk=None):
        """Router for work with rights"""
        # --- Auth
        if self.get_object().owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            resp = self._permission_list(request, pk)
        elif request.method == 'POST':
            resp = self._permission_add(request, pk)
        elif request.method == 'PUT':
            resp = self._permission_add(request, pk)
        elif request.method == 'DELETE':
            resp = self._permission_delete(request, pk)
        else:
            resp = Response(status.HTTP_405_METHOD_NOT_ALLOWED)

        return resp

    def _permission_add(self, request, pk=None):
        """Add/change rights for user

        Args:
            username - user login
            permission - string from ["view", "change"]
        """
        # --- Auth
        # if self.get_object().owner != request.user:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # --- Checks

        username = request.data.get("username")
        role = request.data.get("role")

        if username is None:
            return Response(
                _("The field '{}' is incorrectly filled").format("username"),
                status=status.HTTP_400_BAD_REQUEST)
        if role is None:
            return Response(
                _("The field '{}' is incorrectly filled").format("role"),
                status=status.HTTP_400_BAD_REQUEST)

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                _("'{}'. User not found").format(username),
                status=status.HTTP_400_BAD_REQUEST)

        if user_obj == self.get_object().owner:
            return Response(
                _("The project owner selected"),
                status=status.HTTP_400_BAD_REQUEST)

        if role not in [x[0] for x in models.PROJECT_ROLES]:
            return Response(
                _("Unknown role"), status=status.HTTP_400_BAD_REQUEST)

        try:
            perm = models.ProjectsPermission.objects.get(
                project=self.get_object(),
                user=user_obj
            )
        except models.ProjectsPermission.DoesNotExist:
            perm = None

        # --- Action
        if perm is None:
            # create
            perm = models.ProjectsPermission.objects.create(
                project=self.get_object(),
                user=user_obj,
                role=role
            )
        else:
            # update
            perm.role = role
            perm.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _permission_delete(self, request, pk=None):
        """It takes the rights from user

        Args:
            username - login
        """
        # --- Auth
        # if self.get_object().owner != request.user:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # --- Check
        username = request.data.get("username")

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                _("'{}'. User not found").format(username),
                status=status.HTTP_400_BAD_REQUEST)

        try:
            perm = models.ProjectsPermission.objects.get(
                project=self.get_object(),
                user=user_obj
            )
            perm.delete()
        except models.ProjectsPermission.DoesNotExist:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _permission_list(self, request, pk=None):
        """Get the list of rights"""
        # --- Auth
        # if self.get_object().owner != request.user:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # --- Action
        result = []

        try:
            user_qs = User.objects.filter(
                pk=OuterRef("user")
            )
            perm = models.ProjectsPermission.objects.filter(
                project=self.get_object()
            ).annotate(
                username=Subquery(
                    user_qs.values('username')[:1]
                )
            ).values()
        except models.ProjectsPermission.DoesNotExist:
            pass

        return Response(perm)
    
    # ==/ Block: Labels

    def _label_get_handler(self, project_type):
        map = {
            "text_label": self._process_labels_tl,
            "document_classificaton": self._process_labels_dc
        }
        label_handler = map.get(project_type)
        if label_handler is None:
            raise AnnotationBaseExcept(_("Did not find handler for labels"))
        return label_handler
    
    def _label_doc_get_handler(self, project_type):
        map = {
            "text_label": self._process_labels_doc_tl,
            "document_classificaton": self._process_labels_doc_dc
        }
        label_handler = map.get(project_type)
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
            project=self.get_object()
        ).values_list('name', flat=True)

        for label in list(labels_uniq):
            if label in all_label_name:
                continue
            try:
                models.TlLabels.objects.create(
                    project=self.get_object(),
                    name=label
                )
            except ValidationError:
                pass
        
        # Add label for sequence
        for tag, char_left, char_right in labels:
            models.TlSeqLabel.objects.create(
                sequence=seq,
                label=models.TlLabels.objects.get(
                    project=self.get_object(),
                    name=tag
                ),
                offset_start=char_left,
                offset_stop=char_right
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
            project=self.get_object()
        ).values_list('name', flat=True)

        for label in list(labels_uniq):
            if label in all_label_name:
                continue
            try:
                models.TlLabels.objects.create(
                    project=self.get_object(),
                    name=label
                )
            except ValidationError:
                pass
        
        # Add label for doc
        for tag, value in labels:
            models.DCDocLabel.objects.create(
                document=doc,
                label=models.TlLabels.objects.get(
                    project=self.get_object(),
                    name=tag
                ),
            )

    # ==/ End Block

    def _export_handler(self):
        """Iteration documents for export process"""
        docs = models.Documents.objects.filter(
            project=self.get_object()).order_by("file_name")
        project_type = self.get_object().type

        for doc in docs:
            data = []
            labels_on_doc = []

            if project_type == "document_classificaton":
                for x in doc.get_labels():
                    labels_on_doc.append((x["name"], x["value"]))

            seqs = models.Sequence.objects.filter(
                document=doc).order_by("order")
            for idx, seq in enumerate(seqs):
                labels = []
                if project_type == "text_label":
                    labels_obj = models.TlSeqLabel.objects.filter(
                        sequence=seq).order_by("offset_start")
                    for lb_seq in labels_obj:
                        labels.append((
                            lb_seq.label.name,
                            lb_seq.offset_start,
                            lb_seq.offset_stop
                        ))
                data.append((idx, seq.text, labels))

            yield data, json.loads(doc.meta), doc.file_name, labels_on_doc
    
    def is_int(self, s) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    def _check_permision(self, request) -> bool:
        """Checks if there are rights to the operation"""


class DocumentSeqViewSet(viewsets.ModelViewSet):
    queryset = models.Documents.objects.all()
    serializer_class = anno_serializer.DocumentSeqSerializer

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def approved(self, request, pk=None):
        doc = self.get_object()
        doc.approved = True
        doc.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def unapproved(self, request, pk=None):
        doc = self.get_object()
        doc.approved = False
        doc.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def reset(self, request, pk=None):
        """Delete the all labels in document"""
        doc = self.get_object()
        for sequence in models.Sequence.objects.filter(document=doc):
            models.TlSeqLabel.objects.filter(sequence=sequence).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def label_set(self, request, pk=None):
        """
        {
            "label_id": int,
            "value": 0/1,
        }
        """
        doc = self.get_object()
        
        label_id = request.data.get("label_id", None)
        if label_id is None:
            return Response(
                _("Label not found"), status=status.HTTP_400_BAD_REQUEST)
        label = models.TlLabels.objects.get(pk=label_id)

        try:
            value = int(request.data.get("value", None))
            if value not in [0, 1]:
                raise ValueError(_("Value label not 0/1"))
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except TypeError:
            msg = _("Value not convert to int")
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

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
    
    @action(detail=True, methods=['get', 'delete'])
    def labels(self, request, pk=None):
        """Control labels
            Get - return all list for documents. Format see in models.
            Delete - delete all label for documents.

        Return:
            Depended from method
        """
        if request.method == 'GET':
            resp = Response(self.get_object().get_labels(), status=200)
        elif request.method == 'DELETE':
            self.get_object().labels_del()
            resp = Response(status=status.HTTP_204_NO_CONTENT)
        else:
            resp = Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
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
class TLLabelsViewSet(viewsets.ModelViewSet):
    """
    suffix_key - если не указано будет попытка найти свободную букву
    """
    queryset = models.TlLabels.objects.all()
    serializer_class = anno_serializer.TLLabelsSerializer

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class TLSeqLabelViewSet(viewsets.ModelViewSet):
    queryset = models.TlSeqLabel.objects.all()
    serializer_class = anno_serializer.TLSeqLabelSerializer

    def create(self, request):
        """Creates the object of labels and return their the array"""
        result = []

        offset_start = request.data["offset_start"]
        offset_stop = request.data["offset_stop"]
        seq_id = request.data["sequence"]
        label_id = request.data["label"]

        text = models.Sequence.objects.filter(pk=seq_id).values("text")
        if len(text) != 1:
            Response(status=404)
        text = text[0].get("text", "")

        offset_chunk = offset_start
        for item in text[offset_start:offset_stop].split(" "):
            r = models.TlSeqLabel.objects.create(
                offset_start=offset_chunk,
                offset_stop=offset_chunk + len(item),
                sequence=models.Sequence.objects.get(pk=seq_id),
                label=models.TlLabels.objects.get(pk=label_id)
            )
            offset_chunk = offset_chunk + len(item) + 1

            serializer = anno_serializer.TLSeqLabelSerializer(r)
            result.append(serializer.data)
        return Response(result)

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
