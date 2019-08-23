import io
import os
from zipfile import ZipFile

from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import Http404
from django.db import transaction
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from annotation import models
from annotation.exceptions import FileParseException
from annotation.models import Projects, PROJECT_TYPE
import annotation.serializers as anno_serializer
from annotation.serializers import ProjectsSerializer, DocumentsSerializer

import conllu


def project_action(request, project, action=None):
    actions_list = ["page", "import", "export", "settings", "annotation"]

    if action is None:
        action = "page"

    if action not in actions_list:
        raise Http404("Project action not found")

    project_obj = Projects.objects.get(pk=project)

    if action == "annotation":
        if project_obj.type == "text_label":
            render_template = "project_annotation_tl.html"
        else:
            raise Http404("Annotation type not found")
    else:
        render_template = "project_{}.html".format(action)

    context = {
        "project": project_obj,
    }

    return render(request, render_template, context)


# API
# ====
class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for project

    Action:
        ds_import - Импортирует файл датасета
        PUT multipart:
        * files - файля для импорта
        * format - строка с нужным форматом (conllup)

        documents_list - список документов в проекте
        GET json
        Возвращает стриницами по 10ть (?page)
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer
    # pagination_class = None

    # Поддерживаемые форматы
    file_format_list = ["conllup"]

    def list(self, request, *args, **kwargs):
        queryset = models.Projects.objects.all()

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
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
    def documents_list(self, request, pk=None):
        docs = models.Documents.objects.filter(
            project=self.get_object()
        ).order_by("id")
        docs_page = self.paginate_queryset(docs)

        if docs_page is not None:
            serializer = DocumentsSerializer(docs_page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentsSerializer(docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tl_labels_list(self, request, pk=None):
        labels = models.TlLabels.objects.filter(
            project=self.get_object()
        ).order_by("id")

        serializer = anno_serializer.TLLabelsSerializer(labels, many=True)
        return Response(serializer.data)

    def _import_conllup(self, file, file_name):
        """Импортирует файл формата CoNLLU Plus"""
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
            raise FileParseException("Файл не в кодировке UTF-8")

        doc = models.Documents.objects.create(
            project=self.get_object(),
            file_name=file_name,
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
            for label in list(labels_uniq):
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
                    label=models.TlLabels.objects.get(name=tag),
                    offset_start=char_left,
                    offset_stop=char_right
                )

    def _is_zip(self, file) -> bool:
        """Проверяет является ли файла zip"""
        name, ext = os.path.splitext(file._name)
        if ext == ".zip":
            return True
        return False

    def _import_zip_file(self, file, im_file):
        """Импортирует zip файл"""
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


class DocumentSeqViewSet(viewsets.ModelViewSet):
    queryset = models.Documents.objects.all()
    serializer_class = anno_serializer.DocumentSeqSerializer

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class TLLabelsViewSet(viewsets.ModelViewSet):
    queryset = models.TlLabels.objects.all()
    serializer_class = anno_serializer.TLLabelsSerializer

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
