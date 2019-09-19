import io
import os
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED

from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
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


def health(request):
    response = HttpResponse(
        "OK",
        content_type="text/plain",
        status=200
    )
    return response


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
        ds_import - Импортирует файл датасета
        PUT multipart:
        * files - файля для импорта
        * format - строка с нужным форматом (conllup)

        documents_list - список документов в проекте
        GET json
        Возвращает стриницами по 10ть (?page)

        documents_list_simple - список документов в проекте
            только идентификаторы

        tl_labels_list - TL, список меток для проекта
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
    def ds_export(self, request, pk=None):
        """
        Query:
            exformat - Формат экспортируемых файлов
        """
        exformat = request.query_params.get("exformat")
        if exformat not in self.file_format_list:
            return Response("The format of file not support", status=400)

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
        docs = models.Documents.objects.filter(
            project=self.get_object()
        ).order_by("file_name")
        docs_page = self.paginate_queryset(docs)

        if docs_page is not None:
            serializer = DocumentsSerializer(docs_page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentsSerializer(docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents_list_simple(self, request, pk=None):
        docs = models.Documents.objects.filter(
            project=self.get_object()
        ).order_by("file_name")

        serializer = anno_serializer.DocumentsSerializerSimple(docs, many=True)
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
            all_label_name = models.TlLabels.objects.all().values_list('name', flat=True)
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
        """Получаем файл нужного формата"""
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
        """Получает готовый документ в виде
        массива массива кортежей (слово, тэг)
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
        """Пересекает ли слово базовый диапазон"""
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
        Последний индекс не включается
        """
        result = []
        lb_last_index = None  # Последний индекс обработанных меток
        offsetStart = 0       # Смещение текущиего слова
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
        """Создает объекты меток и возвращает их массив"""
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
