import io
import os
import json
import logging
from copy import deepcopy
from collections import OrderedDict

from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from annotation import models
from annotation.models import Projects, PROJECT_TYPE
from libs.files import FilesBase


def health(request):
    response = HttpResponse("OK", content_type="text/plain", status=200)
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
    try:
        project_obj = Projects.objects.get(pk=project)
    except Projects.DoesNotExist:
        raise Http404("Project not found")

    if project_obj.type == "text_label":
        actions_map.update(actions_list_map_tl)

    if project_obj.type == "document_classificaton":
        actions_map.update(actions_list_map_dc)

    if action not in actions_map.keys():
        raise Http404("Project action not found")

    render_template = "project_{}.html".format(
        actions_map.get(action)["suffix"]
    )

    context = {
        "project": project_obj,
        "actions_map": OrderedDict(
            sorted(actions_map.items(), key=lambda t: t[1]["pos"])
        ),
    }
    if action in ["import", "export"]:
        context["format_docs"] = FilesBase.get_docs(project_obj.type, action)

    return render(request, render_template, context)
