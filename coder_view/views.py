# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from coder_app.models import Project, Tag, Variable

def index(request):

    return render(request, 'coder_view/index.html', context={})


