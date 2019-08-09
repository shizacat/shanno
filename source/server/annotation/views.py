from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from annotation import models
from annotation.exceptions import FileParseException
from annotation.models import Projects, PROJECT_TYPE
from annotation.serializers import ProjectsSerializer

import conllu


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
    """API endpoint for project

    Action:
        ds_import - Импортирует файл датасета
        PUT multipart:
        * files - файля для импорта
        * format - строка с нужным форматом (conllup)
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer

    # Поддерживаемые форматы
    file_format_list = ["conllup"]

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'])
    def ds_import(self, request, pk=None):
        print("DS import")

        file_obj = request.FILES.get("files", None)
        file_format = request.data.get("format", None)

        print(file_format)
        print(file_obj)

        if file_obj is None:
            return Response("File not found", status=status.HTTP_400_BAD_REQUEST)
        if file_format not in self.file_format_list:
            return Response("Format not exists", status=status.HTTP_400_BAD_REQUEST)

        try:
            if file_format == "conllup":
                self._import_conllup(file_obj)
        except FileParseException as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _import_conllup(self, file):
        """Импортирует файл формата CoNLLU Plus"""
        file_name = file._name

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
