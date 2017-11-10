# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from coder_app.models import Project, Tag, Variable, Coder, Row

def index(request):
    coder_data = Coder.objects.all()

    return render(request, 'coder_view/index.html', {'coder_data': coder_data})

def select_project(request, coder_id):
    coder = Coder.objects.get(id=coder_id)
    projects = coder.project_set.all()
    project_data = []

    for project in projects:
        rows = Row.objects.filter(project=project)
        row_count = rows.count()

        single_project = {
            'name': project.name,
            'rate': project.rate,
            'row_count': row_count
        }

        project_data.append(single_project)

    return render(request, 'coder_view/select_project.html', context={'coder_data': coder, 'project_data': project_data})



