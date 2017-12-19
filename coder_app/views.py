# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Max
from django.core import serializers
from .models import Project, Tag, Variable, Coder, Column, Row, Data, ColumnMeta, RowMeta, DataMeta, Dataset
import json
import requests
import datetime
import pytz

def index(request):
    if request.method == 'POST' and 'delete_project' in request.POST:
        value = request.POST.get('delete_project')
        project_to_delete = Project.objects.get(id=value)
        project_to_delete.delete()

    if request.method == "POST" and 'bulk-tag-delete' in request.POST:
        tags_to_delete = request.POST.getlist('tag-names[]')
        for tag_to_delete in tags_to_delete:
            tag = Tag.objects.get(id=tag_to_delete)
            tag.delete()

    if request.method == "POST" and 'bulk-variable-delete' in request.POST:
        variables_to_delete = request.POST.getlist('variable-names[]')
        for variable_to_delete in variables_to_delete:
            variable = Variable.objects.get(id=variable_to_delete)
            variable.delete()

    project_data_list = []
    projects = Project.objects.all()
    coder_data = Coder.objects.all()
    tag_data = Tag.objects.all()
    variable_data = Variable.objects.all()

    for project in projects:
        dataset_data = Dataset.objects.get(id=project.dataset_id)
        project_data = {
            'id': project.id,
            'name': project.name,
            'rate': project.rate,
            'contains_adverse_events': project.contains_adverse_events,
            'dataset_name': dataset_data.dataset_ID
        }
        project_data_list.append(project_data)

    return render(
        request,
        'coder_app/index.html',
        {
            'project_data': project_data_list,
            'coder_data': coder_data,
            'tag_data': tag_data,
            'variable_data': variable_data
        })

def submit_new_variable(request):
    if request.method == 'POST' and 'add_tag' in request.POST:

        pass

    if request.method == 'POST' and 'submit_variable' in request.POST:
        variable_name = request.POST.get('variable-name')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        project_id = request.POST.get('project_id')

        if project_id == 'None':
            variable = Variable()
            variable.save()
            redirect_url = '/coder_project/'
        else:
            project = Project.objects.get(id=project_id)
            project_tags = project.tag_set.all()
            project_dataset = project.dataset

            variables_in_project = Variable.objects.filter(project=project).values()

            if variables_in_project:
                variable_ids = [variable['id'] for variable in variables_in_project]

                greatest_col_index = \
                    ColumnMeta.objects.filter(variable_id__in=variable_ids).aggregate(Max('column_number'))
            else:
                greatest_col_index = {}
                greatest_col_index['column_number__max'] = None

            if not greatest_col_index['column_number__max']:
                greatest_col_index = 1
            else:
                greatest_col_index = greatest_col_index['column_number__max'] + 1

            variable = Variable(
                project=project
            )
            variable.save()

            for project_tag in project_tags:
                variable.tag_set.add(project_tag)

            column = Column(
                dataset=project_dataset
            )
            column.save()

            column_meta = ColumnMeta(
                column=column,
                is_variable=True,
                variable=variable,
                column_number=greatest_col_index,
                column_name=column.column_name
            )
            column_meta.save()
            redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'

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

        return redirect(redirect_url)

    elif request.method == 'POST' and 'add_variable' in request.POST:
        project_id = request.POST.get('project_for_variable')

        return render(request, 'coder_app/variables.html', {'project_id': project_id})

    elif request.is_ajax() and json.loads(request.POST.get('add_tag')):
        tag_name = request.POST.get('tag_name')
        tag = Tag.objects.filter(name=tag_name).first()

        if not tag:
            tag = Tag(
                name=tag_name
            )
            tag.save()

        tag = {
            'id': tag.id,
            'name': tag.name
        }

        return HttpResponse(
            json.dumps({
                'tag_data': tag,
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
        dataset_id = request.POST.get('dataset-name')
        project_tags = request.POST.getlist('tags_to_add[]')
        project_dataset = Dataset.objects.get(id=dataset_id)
        project_rows = Row.objects.filter(dataset=project_dataset)

        project = Project(
            name=project_name,
            rate=project_rate,
            contains_adverse_events=False,
            is_completed=False,
            dataset=project_dataset
        )

        project.save()

        for tag in project_tags:
            project_tag = Tag.objects.get(id=tag)
            project.tag_set.add(project_tag)

        for row in project_rows:
            row_meta = RowMeta(
                row=row,
                row_name=row.row_name
            )

            row_meta.save()

        return redirect('/coder_project')

    dataset_data = Dataset.objects.all()

    return render(request, 'coder_app/project.html', {'dataset_data': dataset_data})

def edit_project(request, project_id):
    p = Project.objects.get(id=project_id)
    project_data = p
    tag_data = p.tag_set.all()

    project_edit_view = 'variable'
    variables = Variable.objects.filter(project=p)

    variable_data_list = [];

    for variable in variables:
        if variable.is_freeform:
            multiple_or_freeform = 'freeform'
        elif variable.is_multiple_choice:
            multiple_or_freeform = 'multiple'
        else:
            multiple_or_freeform = 'not assigned'

        variable_data = {
            'id': variable.id,
            'name': variable.name,
            'multiple_or_freeform': multiple_or_freeform,
            'description': variable.description
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
                'coder_data': coder_data,
                'tag_data': tag_data
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
                'assigned_or_available': 'assigned',
                'tag_data': tag_data
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
                'project_edit_view': project_edit_view,
                'tag_data': tag_data
            }
        )

    if request.method == 'POST' and 'mentions_view' in request.POST:
        dataset = Dataset.objects.get(project=project_data)
        rows_in_dataset = Row.objects.filter(dataset=dataset)
        row_ids = [row.id for row in rows_in_dataset]
        mention_data = RowMeta.objects.filter(id__in=row_ids)
        project_edit_view = 'mention'

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'mention_data': mention_data,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'tag_data': tag_data
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

    if request.is_ajax() and json.loads(request.POST.get('add_tag_to_project')):
        tag_id = request.POST.get('tag_id')
        tag_to_add = Tag.objects.get(id=tag_id)
        p.tag_set.add(tag_to_add)
        p.save()

        variable_data = Variable.objects.filter(project=p)
        for variable in variable_data:
            variable.tag_set.add(tag_to_add)

        redirect_url = '/coder_project/' + str(p.id) + '/edit_project/'

        return HttpResponse(
            json.dumps({
                'result': 'successful!',
                'redirect_url': redirect_url
            }),
            content_type="application/json"
        )
    
    if request.method == 'POST' and 'remove-project-tags' in request.POST:
        tag_ids = request.POST.getlist('tags-to-remove[]')

        for tag_id in tag_ids:
            tag_to_remove = Tag.objects.get(id=tag_id)
            p.tag_set.remove(tag_to_remove)

        tag_data = p.tag_set.all()

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'tag_data': tag_data
            })

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

        # project_data['name'] = project_name
        # project_data['rate'] = project_rate

        return redirect('/coder_project')


    return render(
        request,
        'coder_app/edit_project.html',
        {
            'variable_data': variable_data_list,
            'id': project_id,
            'project_data': project_data,
            'project_edit_view': project_edit_view,
            'tag_data': tag_data
        }
    )

def edit_variable(request, variable_id):
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
        # redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'

        # return redirect('/coder_project/')

    return render(
        request,
        'coder_app/edit_variable.html',
        {
            'variable_data': variable_data,
            'tag_data': tag_data,
            # 'project_id': project_id,
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
        variable_data = Variable.objects.all()

        return render(
            request,
            'coder_app/variable_library.html',
            {
                'project_data': project_data,
                'variable_data': variable_data
            }
        )

    if request.is_ajax() and json.loads(request.POST.get('add_variables')):
        variables = json.loads(request.POST.get('variables_to_add'))
        project_id = request.POST.get('project_id')

        project_data = Project.objects.get(id=project_id)
        dataset = Dataset.objects.get(project=project_data)
        project_tags = project_data.tag_set.all()
        variable_data = Variable.objects.filter(project=project_data)
        variable_ids_attached_to_project = variable_data.values('id')
        print(variable_ids_attached_to_project, 'ids list')

        for variable in variables:
            attached_variable = \
                next((item for item in variable_ids_attached_to_project if item['id'] == variable['id']), None)

            if attached_variable:
                continue
            else:
                variable = Variable.objects.get(id=variable['id'])
                variable_project_origin = variable.project
                project_origin_tag_ids = [tag.id for tag in variable_project_origin.tag_set.all()]
                tags_attached_to_original_variable = variable.tag_set.exclude(id__in=project_origin_tag_ids)
                greatest_col_index = \
                    ColumnMeta.objects\
                        .filter(variable_id__in=variable_ids_attached_to_project)\
                        .aggregate(Max('column_number'))

                if not greatest_col_index['column_number__max']:
                    greatest_col_index = 1
                else:
                    greatest_col_index = greatest_col_index['column_number__max'] + 1

                variable.pk = None
                variable.save()

                variable.project = project_data
                variable.save()

                for tag in project_tags:
                    variable.tag_set.add(tag)

                for tag in tags_attached_to_original_variable:
                    variable.tag_set.add(tag)

                column = Column(
                    dataset=dataset
                )
                column.save()
                
                column_meta = ColumnMeta(
                    variable=variable,
                    is_variable=True,
                    column_name=column.column_name,
                    column=column,
                    column_number=greatest_col_index
                )
                column_meta.save()

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
    dataset = Dataset.objects.get(project=project_data)
    mention_data = Row.objects.filter(dataset=dataset)
    total_variable_count = Variable.objects.filter(project=project_data).count()

    for row in mention_data:
        answer_data = Data.objects.filter(row=row)
        answer_data = DataMeta.objects.filter(data_id__in=[data.id for data in answer_data])
        answer_ids = ''

        for index, answer in enumerate(answer_data):
            answer_ids += str(answer.id)
            if index + 1 != answer_data.count():
                answer_ids += ','

        row = RowMeta.objects.get(row=row)

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
    if request.method == 'POST' and json.loads(request.POST.get('get_variables')):
        keywords = json.loads(request.POST.get('keywords'))
        global_tag_ids = json.loads(request.POST.get('global_tag_ids'))

        if global_tag_ids:
            variables = Variable.objects.filter(tag=global_tag_ids[0])
        else:
            variables = Variable.objects.all()

        if len(global_tag_ids) > 1:
            sliced_global_tag_ids = global_tag_ids[1:]
            for global_tag_id in sliced_global_tag_ids:
                variables = variables.filter(tag=global_tag_id)

        if keywords:
            for keyword in keywords:
                variables = variables.filter(name__icontains=keyword)

        variable_data = variables

        variable_data = serializers.serialize('json', variable_data)

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

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
    if request.method == "POST" and request.POST.get('tag_id_to_add_to_variable'):
        tag_id = json.loads(request.POST.get('tag_id_to_add_to_variable'))
        tag = Tag.objects.get(id=tag_id)
        print(tag_id)

        tag_data = {
            'id': tag.id,
            'name': tag.name
        }

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.method == 'POST' and request.POST.get('add_to_filter') == 'add_keyword':
        keywords = json.loads(request.POST.get('keywords'))
        global_tag_ids = json.loads(request.POST.get('global_tag_ids'))

        if global_tag_ids:
            variables = Variable.objects.filter(tag=global_tag_ids[0])
        else:
            variables = Variable.objects.all()

        if len(global_tag_ids) > 1:
            sliced_global_tag_ids = global_tag_ids[1:]
            for global_tag_id in sliced_global_tag_ids:
                variables = variables.filter(tag=global_tag_id)

        if keywords:
            for keyword in keywords:
                variables = variables.filter(name__icontains=keyword)

        print(variables, 'these are the variables')

        variable_data = variables

        print(global_tag_ids, variable_data, keywords)

        variable_data = serializers.serialize('json', variable_data)

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.method == 'POST' and request.POST.get('add_to_filter') == 'add_tag':
        tag_id = json.loads(request.POST.get('tag_id_to_add'))
        tag = Tag.objects.get(id=tag_id)

        keywords = json.loads(request.POST.get('keywords'))
        global_tag_ids = json.loads(request.POST.get('global_tag_ids'))
        variables = Variable.objects.filter(tag=global_tag_ids[0])

        if len(global_tag_ids) > 1:
            sliced_global_tag_ids = global_tag_ids[1:]
            for global_tag_id in sliced_global_tag_ids:
                variables = variables.filter(tag=global_tag_id)

        if keywords:
            for keyword in keywords:
                variables = variables.filter(name__icontains=keyword)

        variable_data = []

        for variable in variables:
            variable_name_and_id = {
                'id': variable.id,
                'name': variable.name
            }
            variable_data.append(variable_name_and_id)

        tag_data = {
            'id': tag.id,
            'name': tag.name
        }

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

def edit_tags(request):
    if request.is_ajax() and json.loads(request.POST.get('rename_tag')):
        tag_id = request.POST.get('tag_id')
        tag = Tag.objects.get(id=tag_id)
        new_name = request.POST.get('new_tag_name')
        tag.name = new_name
        tag.save()

        tag_data = serializers.serialize('json', Tag.objects.all())

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and json.loads(request.POST.get('delete_single_tag')):
        tag_id = request.POST.get('tag_id')
        tag = Tag.objects.get(id=tag_id)
        tag.delete()

        tag_data = serializers.serialize('json', Tag.objects.all())

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and json.loads(request.POST.get('tag_list_redirect')):
        tag_id = request.POST.get('tag_id')
        base_url = '/coder_project/review_tag/'
        url_redirect = base_url + str(tag_id)

        return HttpResponse(
            json.dumps({
                'result': 'successful!',
                'url_redirect': url_redirect
            }),
            content_type="application/json"
        )

    tag_data = Tag.objects.all()

    return render(request, 'coder_app/edit_tags.html', {'tag_data': tag_data})

def review_tag(request, tag_id):
    tag_data = Tag.objects.get(id=tag_id)
    variable_data = tag_data.variable.all()
    for variable in variable_data:
        variable.tag_names = [tag.name for tag in variable.tag_set.all()]

    return render(
        request,
        'coder_app/review_tag.html',
        {
            'tag_data': tag_data,
            'variable_data': variable_data
        }
    )

def create_tag(request):
    if request.method == 'POST' and 'create-tag' in request.POST:
        tag_name = request.POST.get('create-tag')
        new_tag = Tag()
        new_tag.name = tag_name
        new_tag.save()

        url_redirect = '/coder_project'

        return redirect(url_redirect)

    return render(
        request,
        'coder_app/create_tag.html',
        {}
    )

def edit_variables(request):
    if request.is_ajax() and request.POST.get('variable_action') == 'bulk_add':
        tag_id = request.POST.get('tag_id')
        variable_ids = json.loads(request.POST.get('variable_ids'))

        tag_to_add = Tag.objects.get(id=tag_id)

        for variable_id in variable_ids:
            variable = Variable.objects.get(id=variable_id)
            variable.tag_set.add(tag_to_add)

        redirect_url = '/coder_project/'

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )
    elif request.is_ajax() and request.POST.get('variable_action') == 'bulk_remove':
        tag_id = request.POST.get('tag_id')
        variable_ids = json.loads(request.POST.get('variable_ids'))

        tag_to_remove = Tag.objects.get(id=tag_id)

        for variable_id in variable_ids:
            variable = Variable.objects.get(id=variable_id)
            variable.tag_set.remove(tag_to_remove)

        redirect_url = '/coder_project/'

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )
    else:
        variable_id = request.POST.get('variable_id')
        variable = Variable.objects.get(id=variable_id)

    if request.is_ajax() and request.POST.get('variable_action') == 'delete_single_variable':
        variable.delete()
        variable_data = serializers.serialize('json', Variable.objects.all())
        redirect_url = '/coder_project/'

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and request.POST.get('variable_action') == 'edit_variable':

        redirect_url = '/coder_project/edit_variable/' + str(variable_id)

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and request.POST.get('variable_action') == 'copy_variable':
        project_data = variable.project
        project_tags = project_data.tag_set.all()
        project_tag_ids = [tag.id for tag in project_tags]

        tag_data = variable.tag_set.exclude(id__in=project_tag_ids)

        variable.pk = None
        variable.save()

        variable.project = None

        for tag in tag_data:
            variable.tag_set.add(tag)

        variable_data = serializers.serialize('json', Variable.objects.all())

        redirect_url = '/coder_project/'

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

def review_variable(request, variable_id):
    variable_data = Variable.objects.get(id=variable_id)
    tag_data = variable_data.tag_set.all()

    return render(
        request,
        'coder_app/review_variable.html',
        {
            'tag_data': tag_data,
            'variable_data': variable_data
        }
    )

def tag_to_variable(request, variable_id):
    variable_data = Variable.objects.get(id=variable_id)

    if request.is_ajax() and request.POST.get('tag_action') == 'add_to_variable':
        tag_id = request.POST.get('tag_id')
        variable_data.tag_set.add(tag_id)

    if request.is_ajax() and request.POST.get('tag_action') == 'remove_tag':
        tag_id = request.POST.get('tag_id')
        tag_to_remove = Tag.objects.get(id=tag_id)
        variable_data.tag_set.remove(tag_to_remove)

    if request.is_ajax() and request.POST.get('tag_action') == 'create_tag':
        tag_name = request.POST.get('tag_name')
        new_tag = Tag()
        new_tag.name = tag_name
        new_tag.save()

        variable_data.tag_set.add(new_tag)

    tags = variable_data.tag_set.all()
    tag_data = []

    for tag in tags:
        tag_info = {
            'id': tag.id,
            'name': tag.name
        }
        tag_data.append(tag_info)

    return HttpResponse(
        json.dumps({
            'tag_data': tag_data,
            'result': 'successful!'
        }),
        content_type="application/json"
    )