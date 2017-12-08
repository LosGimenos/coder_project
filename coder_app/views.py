# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Max
from django.core import serializers
from .models import Project, Tag, Variable, Coder, Column, Row, Data, VariableLibrary
import json
import requests
import datetime
import pytz

def index(request):
    if request.method == 'POST' and 'delete_project' in request.POST:
        value = request.POST.get('delete_project')
        project_to_delete = Project.objects.get(id=value)
        project_to_delete.delete()

    project_data_list = []
    projects = Project.objects.all()
    coder_data = Coder.objects.all()

    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'rate': project.rate,
            'contains_adverse_events': project.contains_adverse_events
        }
        project_data_list.append(project_data)

    return render(request, 'coder_app/index.html', {'project_data': project_data_list, 'coder_data': coder_data})

def submit_new_variable(request):
    if request.method == 'POST' and 'submit_variable' in request.POST:
        project_id = request.POST.get('project_id')
        variable_name = request.POST.get('variable-name')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        # variable_id = request.POST.get('variable_id')
        # variable = Variable.objects.get(id=variable_id)

        project = Project.objects.get(id=project_id)

        greatest_col_index = Column.objects.filter(project=project).aggregate(Max('column_number'))

        if not greatest_col_index['column_number__max']:
            greatest_col_index = 1
        else:
            greatest_col_index = greatest_col_index['column_number__max'] + 1

        variable = Variable()
        variable.save()

        column = Column(
            project=project,
            is_variable=True,
            column_number=greatest_col_index,
            variable=variable
        )
        column.save()

        rows = Row.objects.filter(project=project)

        for row in rows:
            data = Data(
                column=column,
                row=row,
                project=project
            )
            data.save()

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

        return render(request, 'coder_app/variables.html', {'project_id': project_id})

        project = Project.objects.get(id=project_id)

        greatest_col_index = Column.objects.filter(project=project).aggregate(Max('column_number'))

        if not greatest_col_index['column_number__max']:
            greatest_col_index = 1
        else:
            greatest_col_index = greatest_col_index['column_number__max'] + 1

        variable = Variable()
        variable.save()

        column = Column(
            project=project,
            is_variable=True,
            column_number=greatest_col_index,
            variable=variable
        )
        column.save()

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

        tag = Tag.objects.filter(name=tag_name).first()

        if not tag:
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
            contains_adverse_events=False
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
        'contains_adverse_effects': p.contains_adverse_events
    }

    columns = Column.objects.filter(project=p, is_variable=True)
    variable_ids = columns.values_list('variable_id', flat=True)

    variables = []
    for variable_id in variable_ids:
        if variable_id:
            v = Variable.objects.get(id=variable_id)
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

    if request.method == 'POST' and 'mentions_view' in request.POST:
        mention_data = Row.objects.filter(project=p)
        project_edit_view = 'mention'

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'mention_data': mention_data,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view
            }
        )
        pass

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

        return redirect('/coder_project/')

    coder_data = Coder.objects.all()


    return render(request, 'coder_app/add_coder.html', {'coder_data': coder_data})

def edit_coder(request, coder_id):
    try:
        project_id = request.GET['project_id']
    except:
        project_id = None

    coder = Coder.objects.get(id=coder_id)
    projects = coder.project_set.all()

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

        return redirect('/coder_project/')

    return render(request, 'coder_app/edit_coder.html', {'coder': coder, 'project_id': project_id, 'projects': projects })

def edit_variable_library(request):
    if request.method == "POST" and 'import_variable' in request.POST:
        project_id = request.POST.get('project_for_variable')
        project_data = Project.objects.get(id=project_id)

        return render(
            request,
            'coder_app/variable_library.html',
            {
                'project_data': project_data
            }
        )

    if request.method == "POST" and json.loads(request.POST.get('add_variables')):
        variables = json.loads(request.POST.get('variables_to_add'))
        project_id = request.POST.get('project_id')

        project_data = Project.objects.get(id=project_id)
        column_data = Column.objects.filter(project=project_data, is_variable=True)
        variable_ids_attached_to_project = column_data.values('variable_id')

        for variable in variables:
            attached_variable = \
                next((item for item in variable_ids_attached_to_project if item['variable_id'] == variable['id']), None)

            if attached_variable:
                continue
            else:
                variable = Variable.objects.get(id=variable['id'])
                column = Column(
                    variable=variable,
                    is_variable=True,
                    project=project_data
                )
                column.save()

        redirect_url = '/coder_project/' + project_id + '/edit_project/'
        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

def select_mention(request, coder_id, project_id):
    coder_data = Coder.objects.get(id=coder_id)
    project_data = Project.objects.get(id=project_id)
    mention_data = Row.objects.filter(project=project_data)
    column_data = Column.objects.filter(project=project_data, is_variable=True)
    total_variable_count = column_data.count()

    for row in mention_data:
        answer_data = Data.objects.filter(coder=coder_data, row=row)
        answer_ids = ''

        for index, answer in enumerate(answer_data):
            answer_ids += str(answer.id)
            if index + 1 != answer_data.count():
                answer_ids += ','


        row.completed_variables = answer_ids
        row.completed_variables_count = answer_data.count()

    return render(
        request,
        'coder_app/select_mention.html',
        {
            'coder_data': coder_data,
            'project_data': project_data,
            'mention_data': mention_data,
            'total_variable_count': total_variable_count
        })

def review_variables(request, coder_id, project_id):
    completed_variable_ids = request.POST.get('completed_variables')
    completed_variable_id = request.POST.get('completed_variable_id')

    coder_data = Coder.objects.get(id=coder_id)
    answer_data = Data.objects.get(id=int(completed_variable_id))
    mention_data = Row.objects.get(id=answer_data.row_id)
    column_data = Column.objects.get(id=answer_data.column_id)
    variable_data = Variable.objects.get(column=column_data)

    # check media source as Twitter or Instagram
    if mention_data.is_twitter:
        source = 'twitter'
    elif mention_data.is_instagram:
        source = 'instagram'

    # make API call to Social Media API
    media_url = mention_data.media_url
    media_text = mention_data.media_text
    base_instagram_api_url = 'https://api.instagram.com/oembed?url='
    base_twitter_api_url = 'https://publish.twitter.com/oembed?url='

    if media_url and source == 'twitter':
        social_api_url = base_twitter_api_url + media_url
    elif media_url and source == 'instagram':
        social_api_url = base_instagram_api_url + media_url

    if media_url:
        social_api_json = requests.get(social_api_url).json()
        social_data = social_api_json['html']
    else:
        social_data = None

    return render(
        request,
        'coder_app/review_variables.html',
        {
            'mention_data': mention_data,
            'answer_data': answer_data,
            'variable_data': variable_data,
            'social_data': social_data,
            'media_text': media_text,
            'coder_data': coder_data,
            'project_id': project_id,
            'completed_variable_ids': completed_variable_ids
         }
    )

def select_variable(request, coder_id, project_id):
    completed_variable_ids = request.POST.get('completed_variables')
    completed_variables = completed_variable_ids.split(',')

    coder_data = Coder.objects.get(id=coder_id)

    if request.method == "POST" and 'confirm-variable' in request.POST:
        completed_variable_id = request.POST.get('completed_variable_id')
        answer = Data.objects.get(id=completed_variable_id)

        if 'variable-freeform' in request.POST:
            variable_value = request.POST.get('variable-freeform')
        elif 'variable-multiple' in request.POST:
            variable_value = request.POST.get('variable-multiple')
        else:
            variable_value = None

        has_adverse_events = request.POST.get('variable-adverse-events')

        if has_adverse_events:
            mention = Row.objects.get(id=answer.row_id)

            if not mention.contains_adverse_events:
                mention.contains_adverse_events = True
                mention.adverse_event_datetime_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)

                mention.save()

        if answer.value != variable_value:
            answer.value = variable_value
            answer.corrected = True

        answer.reviewed = True
        answer.save()

        total_coder_answer_count = Data.objects.filter(coder=coder_data).count()
        corrected_coder_answer_count = Data.objects.filter(coder=coder_data, corrected=True).count()

        coder_rating = (100 - ((corrected_coder_answer_count / total_coder_answer_count) * 100)) / 10
        coder_rating = round(coder_rating, 1)

        coder_data.rating = float(coder_rating)
        coder_data.save()

    answer_data = Data.objects.filter(id__in=completed_variables)

    if answer_data:
        mention_data = Row.objects.get(id=answer_data[0].row_id)

        for answer in answer_data:
            column_data = Column.objects.get(id=answer.column_id)
            variable_data = Variable.objects.get(column=column_data)

            if variable_data.is_multiple_choice:
                variable_data.multiple_or_freeform = 'Multiple Choice'
            else:
                variable_data.multiple_or_freeform = 'Freeform'

            answer.variable_data = variable_data

    return render(
        request,
        'coder_app/select_variable.html',
        {
            'coder_data': coder_data,
            'mention_data': mention_data,
            'answer_data': answer_data,
            'project_id': project_id,
            'completed_variable_ids': completed_variable_ids
        }
    )

def get_variable_names(request):
    if request.method == 'POST' and json.loads(request.POST.get('variable_id_to_add')):
        variable_id = json.loads(request.POST.get('variable_id_to_add'))
        variable_data = Variable.objects.filter(id=variable_id)
        variable_data = serializers.serialize('json', variable_data)

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    elif request.is_ajax():
        query = request.GET.get('term', '')
        variables = Variable.objects.filter(name__icontains=query)
        results = []
        for variable in variables:
            variable_names_json = {
                'id': variable.id,
                'label': variable.name,
                'value': variable.description
            }
            results.append(variable_names_json)
        variable_data = json.dumps(results)
    else:
        variable_data = 'fail'

    mimetype = 'application/json'
    return HttpResponse(variable_data, mimetype)

def get_tag_names(request):
    if request.method == 'POST' and json.loads(request.POST.get('tag_id_to_add')):
        tag_id = json.loads(request.POST.get('tag_id_to_add'))
        tag = Tag.objects.get(id=tag_id)
        variable_data = tag.variable.all()
        tag_data = {
            'id': tag.id,
            'name': tag.name
        }
        variable_data = serializers.serialize('json', variable_data)

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'variable_data': variable_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    elif request.is_ajax():
        query = request.GET.get('term', '')
        tags = Tag.objects.filter(name__icontains=query)
        results = []
        for tag in tags:
            tag_names_json = {
                'value': tag.name,
                'label': tag.name,
                'id': tag.id
            }
            results.append(tag_names_json)
        variable_data = json.dumps(results)
    else:
        variable_data = 'fail'

    mimetype = 'application/json'
    return HttpResponse(variable_data, mimetype)