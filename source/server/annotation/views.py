import io
import os
import json
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED

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
from annotation.exceptions import FileParseException
from annotation.models import Projects, PROJECT_TYPE
import annotation.serializers as anno_serializer
from annotation.serializers import ProjectsSerializer, DocumentsSerializer

import conllu


def health(request):
    response = HttpResponse(
        "OK",
        content_type="text/plain",
        status=200
    )
    return response


@login_required
def project_action(request, project, action="page"):
    # dict: name_action -> name_suffix_template
    actions_list_map = {
        "page": "page",
        "import": "import",
        "export": "export",
        "settings": "settings",
    }

    actions_list_map_tl = {
        "annotation": "tl_annotation",
        "tl-labels": "tl_labels",
    }

    # main
    actions_map = deepcopy(actions_list_map)
    project_obj = Projects.objects.get(pk=project)

    if project_obj.type == "text_label":
        actions_map.update(actions_list_map_tl)

    if action not in actions_map.keys():
        raise Http404("Project action not found")

    render_template = "project_{}.html".format(actions_map.get(action))

    context = {
        "project": project_obj,
    }

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

    # Supported formats
    file_format_list = ["conllup"]

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

        if file_obj is None:
            return Response("File not found", status=status.HTTP_400_BAD_REQUEST)
        if file_format not in self.file_format_list:
            return Response("Format not exists", status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if file_format == "conllup":
                    if self._is_zip(file_obj):
                        print("Zip")
                        self._import_zip_file(file_obj, self._import_conllup)
                    else:
                        self._import_conllup(file_obj, file_obj._name)
        except FileParseException as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def ds_export(self, request, pk=None):
        """
        Query:
            exformat - The format exported files
        """
        exformat = request.query_params.get("exformat")
        if exformat not in self.file_format_list:
            return Response(_("This file format is not supported"), status=400)

        response = HttpResponse(
            self._export(exformat),
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

    def _import_conllup(self, file, file_name):
        """Imports the file of format CoNLLU Plus"""
        field_parsers = {
            "ne": lambda line, i: conllu.parser.parse_nullable_value(line[i]),
        }

        try:
            sentences = conllu.parse(
                file.read().decode(),
                fields=("form", "ne"),
                field_parsers=field_parsers
            )
        except conllu.parser.ParseException as e:
            raise FileParseException(str(e))
        except UnicodeDecodeError:
            raise FileParseException(_("The file is not encoded in UTF-8"))

        doc = models.Documents.objects.create(
            project=self.get_object(),
            file_name=os.path.splitext(file_name)[0],
        )

        for index, sentence in enumerate(sentences):
            if not sentence:
                continue
            words, labels = [], []
            labels_uniq = set()
            for item in sentence:
                word = item.get("form")
                tag = item.get("ne", None)

                if tag is not None:
                    char_left = sum(map(len, words)) + len(words)
                    char_right = char_left + len(word)
                    span = [char_left, char_right, tag]
                    labels_uniq.add(tag)
                    labels.append(span)

                words.append(word)

            seq = models.Sequence.objects.create(
                document=doc,
                text=" ".join(words),
                order=index
            )

            # Labels
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
                except ValidationError as e:
                    pass

            for char_left, char_right, tag in labels:
                models.TlSeqLabel.objects.create(
                    sequence=seq,
                    label=models.TlLabels.objects.get(
                        project=self.get_object(),
                        name=tag
                    ),
                    offset_start=char_left,
                    offset_stop=char_right
                )

    def _is_zip(self, file) -> bool:
        """Checks that the file is format zip"""
        name, ext = os.path.splitext(file._name)
        if ext == ".zip":
            return True
        return False

    def _import_zip_file(self, file, im_file):
        """Imports the file of zip"""
        with ZipFile(file) as zip:
            for item in zip.infolist():
                if item.is_dir():
                    continue
                # Fix, service folder MAC OS X
                if item.filename.startswith("__MACOSX/"):
                    continue
                filename = os.path.split(item.filename)[1]
                content = io.BytesIO(zip.read(item.filename))
                im_file(content, filename)

    def _export(self, export_format="conllup") -> bytes:
        map_ext_format = {
            "conllup": "conllup"
        }
        docs = models.Documents.objects.filter(
            project=self.get_object()).order_by("file_name")
        zip_file = io.BytesIO()
        zip_obj = ZipFile(zip_file, mode="w", compression=ZIP_DEFLATED)
        for doc in docs:
            if export_format == "conllup":
                data = self._export_to_conllup(doc)
            else:
                raise ValueError("")
            zip_obj.writestr(
                "{}.{}".format(
                    doc.file_name,
                    map_ext_format.get(export_format)
                ),
                data
            )
        zip_obj.close()

        return zip_file.getvalue()

    def _export_to_conllup(self, doc_obj) -> bytes:
        """Getting the file in need format"""
        buf = io.StringIO()

        # Header
        buf.write("# global.columns = FORM NE\n")

        for seq in self._export_one_doc(doc_obj):
            buf.write("\n")
            for word, label in seq:
                if label is None:
                    label = "_"
                buf.write("{}\t{}\n".format(word, label))

        buf.seek(0)
        return buf.read().encode()

    def _export_one_doc(self, doc_obj) -> list:
        """Get the end document as array of arrays tuples
        (word, labels)
        """
        result = []
        seqs = models.Sequence.objects.filter(
            document=doc_obj).order_by("order")
        for seq in seqs:
            seq_res = self._eod_process_seq(
                seq.text,
                models.TlSeqLabel.objects.filter(
                    sequence=seq).order_by("offset_start")
            )
            result.append(seq_res)

        return result

    def _eod_set_lb_index(self, labels, range_word):
        for index, item in enumerate(labels):
            if range_word[0] < item.offset_stop:
                return index
        return None

    def _eod_ch_cross(self, rword: tuple, rbase: tuple) -> bool:
        """Does the word cross the base range"""
        start = 0
        end = 1
        if rword[end] > rbase[start] and rword[end] < rbase[end]:
            return True
        if rword[start] >= rbase[start] and rword[end] < rbase[end]:
            return True
        if rword[start] >= rbase[start] and rword[start] < rbase[end]:
            return True
        return False

    def _eod_process_seq(self, text, seq_labels) -> list:
        """
        Last index not included
        """
        result = []
        lb_last_index = None  # Last index processed labels
        offsetStart = 0       # Offset current word
        for word in text.split(" "):
            range_word = (offsetStart, offsetStart + len(word))
            lb_last_index = self._eod_set_lb_index(seq_labels, range_word)
            if lb_last_index is not None:
                rbase = (
                    seq_labels[lb_last_index].offset_start,
                    seq_labels[lb_last_index].offset_stop
                )
                if self._eod_ch_cross(range_word, rbase):
                    result.append((word, seq_labels[lb_last_index].label.name))
                else:
                    result.append((word, None))
            else:
                result.append((word, None))

            offsetStart = range_word[1] + 1

        return result

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
