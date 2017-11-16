# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Max
from .models import Project, Tag, Variable, Coder, Column, Row, Data
import json

def index(request):
    if request.method == 'POST' and 'delete_project' in request.POST:
        value = request.POST.get('delete_project')
        project_to_delete = Project.objects.get(id=value)
        project_to_delete.delete()

    project_data_list = []
    projects = Project.objects.all()

    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'rate': project.rate,
            'contains_adverse_effects': project.contains_adverse_effects
        }
        project_data_list.append(project_data)

    return render(request, 'coder_app/index.html', {'project_data': project_data_list})

def submit_new_variable(request):
    if request.method == 'POST' and 'submit_variable' in request.POST:
        variable_name = request.POST.get('variable-name')
        project_id = request.POST.get('project_id')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        variable_id = request.POST.get('variable_id')
        variable = Variable.objects.get(id=variable_id)

        if multiple_or_freeform == 'multiple_choice':
            variable.is_freeform = False
            variable.is_multiple_choice = True

            variable_choices = {}

            for index in range(1,8):
                node_name_string = 'variable-choice-' + str(index)
                choice_content = request.POST.get(node_name_string)

                variable_choices[node_name_string] = choice_content

            variable.multiple_choice_option_one = variable_choices['variable-choice-1']
            variable.multiple_choice_option_two = variable_choices['variable-choice-2']
            variable.multiple_choice_option_three = variable_choices['variable-choice-3']
            variable.multiple_choice_option_four = variable_choices['variable-choice-4']
            variable.multiple_choice_option_five = variable_choices['variable-choice-5']
            variable.multiple_choice_option_six = variable_choices['variable-choice-6']
            variable.multiple_choice_option_seven = variable_choices['variable-choice-7']
        elif multiple_or_freeform == 'freeform':
            variable.is_freeform = True
            variable.is_multiple_choice = False

        variable.name = variable_name
        variable.description = variable_description
        variable.instructions = variable_instructions

        variable.save()

        redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'
        return redirect(redirect_url)

    elif request.method == 'POST' and 'add_variable' in request.POST:
        project_id = request.POST.get('project_for_variable')
        project = Project.objects.get(id=project_id)

        greatest_col_index = Column.objects.filter(project=project).aggregate(Max('column_number'))
        greatest_col_index = greatest_col_index['column_number__max'] + 1

        column = Column(
            project=project,
            is_variable=True,
            column_number=greatest_col_index
        )
        column.save()

        variable = Variable(
            column=column
        )
        variable.save()

        rows = Row.objects.filter(project=project)

        for row in rows:
            data = Data(
                column=column,
                row=row,
                project=project
            )
            data.save()

    elif request.method == 'POST' and request.POST.get('add-tag') == 'add-tag':
        tag_name = request.POST.get('variable-tag')
        variable_id = request.POST.get('variable_id')
        variable = Variable.objects.get(id=variable_id)
        project_id = request.POST.get('project_id')

        tag = Tag(
            name=tag_name
        )
        tag.save()

        tag.variable.add(variable)
        tag_data = variable.tag_set.all()
        tag_data_list = []

        for tag in tag_data:
            tag_data_list.append({'name': tag.name, 'id': tag.id})

        return HttpResponse(
            json.dumps({
                'variable_id': variable_id,
                'project_id': project_id,
                'tag_data': tag_data_list,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    elif request.method == 'POST' and request.POST.get('delete_tag') == 'delete_tag':
        tag_id = request.POST.get('tag_id')
        project_id = request.POST.get('project_id')
        variable_id = request.POST.get('variable_id')

        print(tag_id, variable_id, 'these are the ids')

        variable = Variable.objects.get(id=variable_id)
        tag = Tag.objects.get(id=tag_id)
        variable.tag_set.remove(tag)

        return HttpResponse(
            json.dumps({
                'variable_id': variable_id,
                'project_id': project_id,
                'tag_id': tag_id,
                'result': 'successful!'
            }),
            content_type="application/json"
            )

    try:
        variable_id = variable.id
    except:
        variable_id = request.POST.get('variable_id')

    if request.POST.get('project_id') == None:
        project_id = request.POST.get('project_for_variable')
    else:
        project_id = request.POST.get('project_id')

    return render(request, 'coder_app/variables.html', {'variable_id': variable_id, 'project_id': project_id })

def submit_new_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('project-name')
        project_rate = request.POST.get('project-rate')

        project = Project(
            name=project_name,
            rate=project_rate,
            contains_adverse_effects=False
        )

        project.save()

        return redirect('/coder_project')

    return render(request, 'coder_app/project.html', context={})

def edit_project(request, project_id):
    variable_data_list = []
    project_edit_view = 'variable'

    p = Project.objects.get(id=project_id)
    project_data = {
        'id': p.id,
        'name': p.name,
        'rate': p.rate,
        'contains_adverse_effects': p.contains_adverse_effects
    }

    columns = Column.objects.filter(project=p)
    variables = []
    for column in columns:
        v = Variable.objects.get(column=column)
        variable = {
         'id': v.id,
         'name': v.name,
         'description': v.description,
         'instructions': v.instructions,
         'is_freeform': v.is_freeform,
         'is_multiple_choice': v.is_multiple_choice
        }
        variables.append(variable)

    for variable in variables:
        if variable['is_freeform'] == True:
            multiple_or_freeform = 'freeform'
        elif variable['is_multiple_choice'] == True:
            multiple_or_freeform = 'multiple'
        else:
            multiple_or_freeform = 'not assigned'

        variable_data = {
            'id': variable['id'],
            'name': variable['name'],
            'multiple_or_freeform': multiple_or_freeform,
            'description': variable['description']
        }
        variable_data_list.append(variable_data)

    if request.method == 'POST' and 'delete_variable' in request.POST:
        value = request.POST.get('delete_variable')
        column_to_delete = Column.objects.get(id=value)
        variable_to_delete = Variable.objects.get(id=value)

        column_to_delete.delete()
        variable_to_delete.delete()

        redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'

        return redirect(redirect_url)

    if request.method == 'POST' and 'available_coder_view' in request.POST:
        project_edit_view = 'coder'
        coder_data = Coder.objects.exclude(project=project_id)

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'coder_data': coder_data
            }
        )

    if request.method == 'POST' and 'assigned_coder_view' in request.POST:
        project_edit_view = 'coder'
        coder_data = Coder.objects.filter(project=project_id)

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'coder_data': coder_data,
                'assigned_or_available': 'assigned'
            }
        )

    if request.method == 'POST' and 'variable_view' in request.POST:
        project_edit_view = 'variable'

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view
            }
        )

    if request.method == 'POST' and 'add_to_project' in request.POST:
        project_id = request.POST.get('project_id')
        coders_to_add = request.POST.getlist('add_to_project')

        project = Project.objects.get(id=project_id)

        for coder_id in coders_to_add:
            coder = Coder.objects.get(id=coder_id)
            project.coder.add(coder)

        return redirect('/coder_project')


    if request.method == 'POST':
        project_name = request.POST.get('project-name')
        project_rate = request.POST.get('project-rate')


        if project_name == '':
            project_name = p.name
        if project_rate == '':
            project_rate = p.rate

        p.name = project_name
        p.rate = project_rate
        p.save()

        project_data['name'] = project_name
        project_data['rate'] = project_rate

        return redirect('/coder_project')


    return render(
        request,
        'coder_app/edit_project.html',
        {
            'variable_data': variable_data_list,
            'id': project_id,
            'project_data': project_data,
            'project_edit_view': project_edit_view
        }
    )

def edit_variable(request, variable_id, project_id):
    if project_id == None:
        project_id = request.POST.get('project_id')

    v = Variable.objects.get(id=variable_id)
    variable_data = {
        'id': v.id,
        'name': v.name,
        'description': v.description,
        'instructions': v.instructions,
        'is_freeform': v.is_freeform,
        'is_multiple_choice': v.is_multiple_choice
    }

    choice_data = {}

    if v.is_multiple_choice:
        choice_data_list = [
            {'1': {'value': v.multiple_choice_option_one}},
            {'2': {'value': v.multiple_choice_option_two}},
            {'3': {'value': v.multiple_choice_option_three}},
            {'4': {'value': v.multiple_choice_option_four}},
            {'5': {'value': v.multiple_choice_option_five}},
            {'6': {'value': v.multiple_choice_option_six}},
            {'7': {'value': v.multiple_choice_option_seven}}
        ]

        choice_data = []

        for index, choice in enumerate(choice_data_list):
            if choice[str(index + 1)]['value'] != None:
                choice_name_string = 'variable-choice-' + str(index + 1)

                choice[str(index + 1)]['index'] = index + 1
                choice[str(index + 1)]['choice_name'] = choice_name_string
                choice_data.append(choice[str(index + 1)])

    tag_data = v.tag_set.all()

    if request.method == 'POST':
        variable_name = request.POST.get('variable-name')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        if multiple_or_freeform == 'multiple_choice':
            v.is_freeform = False
            v.is_multiple_choice = True
        elif multiple_or_freeform == 'freeform':
            v.is_freeform = True
            v.is_multiple_choice = False

        v.name = variable_name
        v.description = variable_description
        v.instructions = variable_instructions
        v.save()
        redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'

        return redirect(redirect_url)

    return render(
        request,
        'coder_app/edit_variable.html',
        {
            'variable_data': variable_data,
            'tag_data': tag_data,
            'project_id': project_id,
            'choice_data': choice_data
        })

def submit_new_coder(request):
    if request.method == 'POST':
        first_name = request.POST.get('coder-first-name')
        middle_name = request.POST.get('coder-middle-name')
        last_name = request.POST.get('coder-last-name')
        email_value = request.POST.get('coder-email')
        username = request.POST.get('coder-username')

        c = Coder(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email_value,
            username=username
        )
        c.save()

    coder_data = Coder.objects.all()


    return render(request, 'coder_app/add_coder.html', {'coder_data': coder_data})

def edit_coder(request, coder_id):
    try:
        project_id = request.GET['project_id']
    except:
        project_id = None

    coder = Coder.objects.get(id=coder_id)

    if request.method == 'POST':
        coder.first_name = request.POST.get('coder-first-name')
        coder.middle_name = request.POST.get('coder-middle-name')
        coder.last_name = request.POST.get('coder-last-name')
        coder.username = request.POST.get('coder-username')
        coder.email = request.POST.get('coder-email')

        coder.save()

        project_id = request.POST.get('project_id')

        if project_id != '':
            redirect_url = '/coder_project/' + str(project_id) + '/edit_project'
            return redirect(redirect_url)

        return redirect('/coder_project/add_coder')

    return render(request, 'coder_app/edit_coder.html', {'coder': coder, 'project_id': project_id })