# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from coder_app_project.settings import MEDIA_URL
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Max
from django.core import serializers
from .models import Project, Tag, Variable, Coder, Column, Row, Data, ColumnMeta, RowMeta, DataMeta, Dataset
from common.models import Account
from django.contrib.auth.models import User
from .pytoxl import process_ae_data
from .email_operations import send_coder_intro_email, send_add_coder_from_user_email
import json
import requests
import datetime
import pytz

@login_required()
def index(request):
    if request.method == "POST" and 'bulk-tag-delete' in request.POST:
        tags_to_delete = request.POST.getlist('tag-names[]')
        for tag_to_delete in tags_to_delete:
            tag = Tag.objects.get(id=tag_to_delete)
            tag.delete()


    user_data = User.objects.get(username=request.user)
    return render(
        request,
        'coder_app/index.html',
        {
            'user_data': user_data
        })

@login_required()
def view_projects(request):
    user = User.objects.get(username=request.user)
    user_account = user.accounts.all().first()
    users = user_account.users.all()

    # pulling projects based on datasets. possibly set for production
    # datasets = Dataset.objects.filter(owner__in=users)
    # project_data = Project.objects.filter(dataset__in=datasets)

    # get projects based on account. will possibly remove in production
    project_data = Project.objects.filter(account=user_account)

    if request.method == 'POST' and 'delete_project_button' in request.POST:
        project_id = request.POST.get('project_id')
        project_to_delete = project_data.get(id=project_id)
        project_to_delete.delete()

    if request.method == 'POST' and 'toggle_freeze_project' in request.POST:
        project_id = request.POST.get('project_id')
        project_to_toggle = project_data.get(id=project_id)

        project_to_toggle.is_frozen = not project_to_toggle.is_frozen
        project_to_toggle.save()

    if request.method == 'POST' and 'replicate_project' in request.POST:
        project_id = request.POST.get('project_id')
        project_to_copy = project_data.get(id=project_id)

        variable_data = Variable.objects.filter(project=project_to_copy)
        # tag_data = project_to_copy.tag_set.all()

        project_to_copy.pk = None
        project_to_copy.name = project_to_copy.name + ' COPY'
        project_to_copy.save()
        new_project_data = project_to_copy

        new_project_tag_name = new_project_data.name.split(' ')
        new_project_tag_name = ''.join(new_project_tag_name)
        new_project_tag = Tag()
        new_project_tag.name = new_project_tag_name
        new_project_tag.save()
        copy_tag, created = Tag.objects.get_or_create(name='copy')

        new_project_data.tag_set.add(new_project_tag)
        new_project_data.tag_set.add(copy_tag)

        # for tag in tag_data:
        #     new_project_data.tag_set.add(tag)

        for variable in variable_data:
            variable.pk = None
            variable.project = new_project_data
            variable.save()

            column = Column(
                dataset=dataset
            )
            column.save()

            greatest_col_index = \
                ColumnMeta.objects.filter(
                    project=project_data
                ).aggregate(Max('column_number'))

            if not greatest_col_index['column_number__max']:
                greatest_col_index = 1
            else:
                greatest_col_index = greatest_col_index['column_number__max'] + 1

            columnMeta = ColumnMeta(
                column=column,
                variable=variable,
                project=project_data,
                column_number=greatest_col_index
            )
            columnMeta.save()

        project_data = Project.objects.filter(account=user_account)


    # project_data = Project.objects.filter(dataset__in=datasets)
    # project_data = Project.objects.all()

    for project in project_data:
        ae_data = []

        if project.contains_adverse_events:
            mentions_containing_ae = RowMeta.objects.filter(contains_adverse_events=True,project=project)

            if mentions_containing_ae:
                for mention in mentions_containing_ae:

                    ae = {
                        'project_name': project.name,
                        'url': mention.media_url,
                        'contents': mention.media_text,
                        'date_posted': 'date posted',
                        'author': 'author',
                        'source': 'source',
                        'date': datetime.datetime.strftime(mention.adverse_event_datetime_submitted, '%m/%d/%Y'),
                        'time': datetime.datetime.strftime(mention.adverse_event_datetime_submitted, '%I:%M')
                    }
                    ae_data.append(ae)
            else:
                ae_data = None

            if ae_data:
                contains_ae_data = True
                file_path = process_ae_data(ae_data)
                project.file_path = file_path
                project.MEDIA_URL = MEDIA_URL
            else:
                contains_ae_data = False

            project.contains_ae_data = contains_ae_data

    return render(
        request,
        'coder_app/project_table.html',
        {
            'project_data': project_data
        }
    )

@login_required()
def replicate_project(request, project_id):
    user = User.objects.get(username=request.user)
    user_account = user.accounts.all().first()

    project_data = Project.objects.get(id=project_id)
    dataset_data = Dataset.objects.all()

    if request.method == 'POST' and 'replicate-project' in request.POST:
        dataset_id = request.POST.get('dataset-name')
        dataset = dataset_data.get(id=dataset_id)
        tags_to_add = request.POST.getlist('tags-to-add[]')
        tag_data = Tag.objects.filter(id__in=tags_to_add)

        # set dataset to current user remove in production
        dataset.owner = user
        dataset.save()

        coder_data = project_data.coder.all()
        variable_data = Variable.objects.filter(project=project_data)

        project_data.pk = None
        project_data.dataset = dataset
        project_data.name = project_data.name + ' COPY'
        project_data.save()
        new_project_data = project_data

        for tag in tag_data:
            new_project_data.tag_set.add(tag)

        for coder in coder_data:
            coder.project_set.add(new_project_data)

        for variable in variable_data:
            variable.pk = None
            variable.project = new_project_data
            variable.save()

            column = Column(
                dataset=dataset
            )
            column.save()

            greatest_col_index = \
                ColumnMeta.objects.filter(
                    project=project_data
                ).aggregate(Max('column_number'))

            if not greatest_col_index['column_number__max']:
                greatest_col_index = 1
            else:
                greatest_col_index = greatest_col_index['column_number__max'] + 1

            columnMeta = ColumnMeta(
                column=column,
                variable=variable,
                project=project_data,
                column_number=greatest_col_index
            )
            columnMeta.save()

        redirect_url = reverse('coder_app:view_projects')
        return redirect(redirect_url)

    return render(
        request,
        'coder_app/replicate_project.html',
        {
            'project_data': project_data,
            'dataset_data': dataset_data
        }
    )

@login_required()
def submit_new_variable(request):
    if request.method == 'POST' and 'submit_variable' in request.POST:
        variable_name = request.POST.get('variable-name')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        project_id = request.POST.get('project_id')

        if project_id == 'None':
            variable = Variable()
            variable.save()
            redirect_url = reverse('coder_app:edit_variables')
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
                column_name=column.column_name,
                project=project
            )
            column_meta.save()
            # redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'
            redirect_url = reverse('coder_app:edit_project', args=[project_id])

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

@login_required()
def submit_new_project(request):
    if request.method == 'POST':
        user = User.objects.get(username=request.user)
        user_account = user.accounts.all().first()

        project_name = request.POST.get('project-name')
        project_rate = request.POST.get('project-rate')
        project_tags = request.POST.getlist('tags_to_add[]')
        project_introduction = request.POST.get('project-introduction')

        # Dataset and info derived from dataset
        # dataset_id = request.POST.get('dataset-name')
        # project_dataset = Dataset.objects.get(id=dataset_id)
        # project_dataset.owner = user
        # project_dataset.save()
        # project_rows = Row.objects.filter(dataset=project_dataset)

        project = Project(
            name=project_name,
            rate=project_rate,
            contains_adverse_events=False,
            is_completed=False,
            # dataset=project_dataset,
            metadata=project_introduction,
            account=user_account
        )

        project.save()

        for tag in project_tags:
            project_tag = Tag.objects.get(id=tag)
            project.tag_set.add(project_tag)

        # for row in project_rows:
        #     row_meta = RowMeta(
        #         row=row,
        #         row_name=row.row_name,
        #         project=project
        #     )
        #
        #     row_meta.save()

        redirect_url = reverse('coder_app:view_projects')

        return redirect(redirect_url)

    # dataset_data = Dataset.objects.all()

    return render(
        request,
        'coder_app/project.html',
        # {'dataset_data': dataset_data},
        {}
    )

@login_required()
def edit_project(request, project_id):
    p = Project.objects.get(id=project_id)
    project_data = p
    tag_data = p.tag_set.all()
    mention_data = RowMeta.objects.filter(project=p)
    mentions_count = mention_data.count()
    rate_per_mention = p.rate
    projected_project_cost = mentions_count * rate_per_mention
    projected_project_cost = '${:,.2f}'.format(projected_project_cost)

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

        # redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'
        redirect_url = reverse('coder_app:edit_project', args=[project_id])

        return redirect(redirect_url)

    if request.method == 'POST' and 'available_coder_view' in request.POST:
        project_edit_view = 'coder'
        user = User.objects.get(username=request.user)
        user_account = user.accounts.all().first()
        user_account_coders = user_account.users.all()
        coder_data = Coder.objects.filter(user__in=user_account_coders).exclude(project=project_data)

        for coder in coder_data:
            coder_as_user = coder.user
            coder.first_name = coder_as_user.first_name
            coder.last_name = coder_as_user.last_name
            coder.username = coder_as_user.username
            coder.email = coder_as_user.email

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'coder_data': coder_data,
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost
            }
        )

    if request.method == 'POST' and 'cambrian_coder_view' in request.POST:
        project_edit_view = 'coder'
        user_account = Account.objects.get(name="Cambrian")
        user_account_coders = user_account.users.all()
        coder_data = Coder.objects.filter(user__in=user_account_coders).exclude(project=project_data)

        for coder in coder_data:
            coder_as_user = coder.user
            coder.first_name = coder_as_user.first_name
            coder.last_name = coder_as_user.last_name
            coder.username = coder_as_user.username
            coder.email = coder_as_user.email

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'coder_data': coder_data,
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost,
                'cambrian_coder_data': True
            }
        )

    if request.method == 'POST' and 'assigned_coder_view' in request.POST:
        project_edit_view = 'coder'
        coder_data = Coder.objects.filter(project=project_id)

        for coder in coder_data:
            coder_as_user = coder.user
            coder.first_name = coder_as_user.first_name
            coder.last_name = coder_as_user.last_name
            coder.username = coder_as_user.username
            coder.email = coder_as_user.email

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
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost
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
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost
            }
        )

    if request.method == 'POST' and 'mentions_view' in request.POST:
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
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost
            }
        )

    if request.method == 'POST' and 'add_to_project' in request.POST:
        project_id = request.POST.get('project_id')
        coders_to_add = request.POST.getlist('add_to_project')

        project = Project.objects.get(id=project_id)

        for coder_id in coders_to_add:
            coder = Coder.objects.get(id=coder_id)
            project.coder.add(coder)

        redirect_url = reverse('coder_app:view_projects')

        return redirect(redirect_url)

    if request.method == 'POST' and 'remove_from_project' in request.POST:
        project_id = request.POST.get('project_id')
        coders_to_remove = request.POST.getlist('remove_from_project')

        project = Project.objects.get(id=project_id)

        for coder_id in coders_to_remove:
            coder = Coder.objects.get(id=coder_id)
            project.coder.remove(coder)

            rows = RowMeta.objects.filter(project=project, coder=coder, is_locked=True, is_completed=False)

            for row in rows:
                row.is_locked = False
                row.coder = None
                row.save()

        redirect_url = reverse('coder_app:view_projects')

        return redirect(redirect_url)

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

            for variable in variables:
                variable.tag_set.remove(tag_to_remove)

        tag_data = p.tag_set.all()

        return render(
            request,
            'coder_app/edit_project.html',
            {
                'variable_data': variable_data_list,
                'id': project_id,
                'project_data': project_data,
                'project_edit_view': project_edit_view,
                'tag_data': tag_data,
                'projected_project_cost': projected_project_cost
            })

    if request.method == 'POST':
        project_name = request.POST.get('project-name')
        project_rate = request.POST.get('project-rate')
        project_introduction = request.POST.get('project-introduction')


        if project_name == '':
            project_name = p.name
        if project_rate == '':
            project_rate = p.rate
        if project_introduction == '':
            project_introduction = p.metadata

        p.name = project_name
        p.rate = project_rate
        p.metadata = project_introduction
        p.save()

        # project_data['name'] = project_name
        # project_data['rate'] = project_rate

        redirect_url = reverse('coder_app:view_projects')

        return redirect(redirect_url)


    return render(
        request,
        'coder_app/edit_project.html',
        {
            'variable_data': variable_data_list,
            'id': project_id,
            'project_data': project_data,
            'project_edit_view': project_edit_view,
            'tag_data': tag_data,
            'projected_project_cost': projected_project_cost
        }
    )

@login_required()
def edit_variable(request, variable_id):
    v = Variable.objects.get(id=variable_id)
    project_data = v.project

    if request.method == 'POST':
        variable_name = request.POST.get('variable-name')
        variable_description = request.POST.get('variable-description')
        variable_instructions = request.POST.get('variable-instructions')
        multiple_or_freeform = request.POST.get('variable_answer_option')

        if multiple_or_freeform == 'multiple_choice':
            v.is_freeform = False
            v.is_multiple_choice = True

            variable_choices = {}

            for index in range(1, 8):
                node_name_string = 'variable-choice-' + str(index)
                choice_content = request.POST.get(node_name_string)

                variable_choices[node_name_string] = choice_content

            v.multiple_choice_option_one = variable_choices['variable-choice-1']
            v.multiple_choice_option_two = variable_choices['variable-choice-2']
            v.multiple_choice_option_three = variable_choices['variable-choice-3']
            v.multiple_choice_option_four = variable_choices['variable-choice-4']
            v.multiple_choice_option_five = variable_choices['variable-choice-5']
            v.multiple_choice_option_six = variable_choices['variable-choice-6']
            v.multiple_choice_option_seven = variable_choices['variable-choice-7']
        elif multiple_or_freeform == 'freeform':
            v.is_freeform = True
            v.is_multiple_choice = False

        v.name = variable_name
        v.description = variable_description
        v.instructions = variable_instructions
        v.save()
        # redirect_url = '/coder_project/' + str(project_id) + '/edit_project/'

        # return redirect('/coder_project/')

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

    if project_data:
        project_tags = project_data.tag_set.all()
        tag_data = tag_data.exclude(id__in=[project_tag.id for project_tag in project_tags])

    return render(
        request,
        'coder_app/edit_variable.html',
        {
            'variable_data': variable_data,
            'tag_data': tag_data,
            # 'project_id': project_id,
            'choice_data': choice_data
        })

@login_required()
def submit_new_coder(request):
    current_username = request.user
    current_user = User.objects.get(username=current_username)
    current_user_account = current_user.accounts.all().first()
    user_data = current_user_account.users.all()
    user_ids_with_coder_id = []
    coder_ids_from_users = []

    for user in user_data:
        coder = Coder.objects.filter(user=user).first()

        if coder:
            user_ids_with_coder_id.append(user.id)
            coder_ids_from_users.append(coder.id)

    user_data = user_data.exclude(id__in=user_ids_with_coder_id)
    coder_data = Coder.objects.filter(id__in=coder_ids_from_users)

    for coder in coder_data:
        coder_as_user = coder.user
        coder.first_name = coder_as_user.first_name
        coder.last_name = coder_as_user.last_name
        coder.username = coder_as_user.username
        coder.email = coder_as_user.email

    if request.method == 'POST' and 'import-user-to-coder' in request.POST:
        user_id = request.POST.get('user-to-coder')
        user = user_data.get(id=user_id)

        new_coder = Coder(
            user=user
        )
        new_coder.save()

        send_add_coder_from_user_email(user)

        user_data = current_user_account.users.all()

        user_ids_with_coder_id = []
        coder_ids_from_users = []

        for user in user_data:
            coder = Coder.objects.filter(user=user).first()

            if coder:
                user_ids_with_coder_id.append(user.id)
                coder_ids_from_users.append(coder.id)

        user_data = user_data.exclude(id__in=user_ids_with_coder_id)
        coder_data = Coder.objects.filter(id__in=coder_ids_from_users)

        for coder in coder_data:
            coder_as_user = coder.user
            coder.first_name = coder_as_user.first_name
            coder.last_name = coder_as_user.last_name
            coder.username = coder_as_user.username
            coder.email = coder_as_user.email

        return render(request, 'coder_app/add_coder.html', {'coder_data': coder_data, 'user_data': user_data})

    if request.method == 'POST' and 'add_new_coder' in request.POST:
        first_name = request.POST.get('coder-first-name')
        last_name = request.POST.get('coder-last-name')
        email_value = request.POST.get('coder-email')
        username = request.POST.get('coder-username')
        password = first_name + '.' + last_name

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email_value,
            username=username
        )
        user.set_password(password)
        user.save()

        current_user_account.users.add(user)

        coder = Coder(
            user=user
        )
        coder.save()

        send_coder_intro_email(user)

        user_data = current_user_account.users.all()

        user_ids_with_coder_id = []
        coder_ids_from_users = []

        for user in user_data:
            coder = Coder.objects.filter(user=user).first()

            if coder:
                user_ids_with_coder_id.append(user.id)
                coder_ids_from_users.append(coder.id)

        user_data = user_data.exclude(id__in=user_ids_with_coder_id)
        coder_data = Coder.objects.filter(id__in=coder_ids_from_users)

        for coder in coder_data:
            coder_as_user = coder.user
            coder.first_name = coder_as_user.first_name
            coder.last_name = coder_as_user.last_name
            coder.username = coder_as_user.username
            coder.email = coder_as_user.email



        return render(request, 'coder_app/add_coder.html', {'coder_data': coder_data, 'user_data': user_data})

    return render(request, 'coder_app/add_coder.html', {'coder_data': coder_data, 'user_data': user_data})

@login_required()
def edit_coder(request, coder_id):
    coder = Coder.objects.get(id=coder_id)
    projects = coder.project_set.all()

    user = coder.user

    if request.method == 'POST':
        user.first_name = request.POST.get('coder-first-name')
        user.middle_name = request.POST.get('coder-middle-name')
        user.last_name = request.POST.get('coder-last-name')
        user.username = request.POST.get('coder-username')
        user.email = request.POST.get('coder-email')

        user.save()

        redirect_url = reverse('coder_app:edit_coder', args=[coder_id])

        return redirect(redirect_url)

    coder.first_name = user.first_name
    coder.last_name = user.last_name
    coder.username = user.username
    coder.email = user.email

    return render(
        request,
        'coder_app/edit_coder.html',
        {
            'coder': coder,
            'projects': projects }
    )

@login_required()
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

        for variable in variables:
            attached_variable = \
                next((item for item in variable_ids_attached_to_project if item['id'] == variable['id']), None)

            if attached_variable:
                continue
            else:
                variable = Variable.objects.get(id=variable['id'])
                variable_project_origin = variable.project

                if variable_project_origin:
                    project_origin_tag_ids = [tag.id for tag in variable_project_origin.tag_set.all()]
                    tags_attached_to_original_variable = variable.tag_set.exclude(id__in=project_origin_tag_ids)
                else:
                    tags_attached_to_original_variable = variable.tag_set.all()

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

@login_required()
def select_mention(request, coder_id, project_id):
    coder_data = Coder.objects.get(id=coder_id)
    user_data = coder_data.user
    coder_data.username = user_data.username

    project_data = Project.objects.get(id=project_id)
    mention_data = RowMeta.objects.filter(project=project_data)
    total_variable_count = Variable.objects.filter(project=project_data).count()

    for mention in mention_data:
        row = mention.row
        answer_data = Data.objects.filter(row=row)
        answer_data = DataMeta.objects.filter(data_id__in=[data.id for data in answer_data])
        answer_ids = ''

        for index, answer in enumerate(answer_data):
            answer_ids += str(answer.id)
            if index + 1 != answer_data.count():
                answer_ids += ','

        # row = RowMeta.objects.get(row=row)

        mention.completed_variables = answer_ids
        mention.completed_variables_count = answer_data.count()

    return render(
        request,
        'coder_app/select_mention.html',
        {
            'coder_data': coder_data,
            'project_data': project_data,
            'mention_data': mention_data,
            'total_variable_count': total_variable_count
        })

@login_required()
def review_variables(request, coder_id, project_id):
    completed_variable_ids = request.POST.get('completed_variables')
    completed_variable_id = request.POST.get('completed_variable_id')
    is_review_all = False

    if request.POST and 'submit_review_all' in request.POST:
        completed_variable_ids = completed_variable_ids.split(',')
        completed_variable_id = completed_variable_ids[0]
        completed_variable_ids = ','.join(completed_variable_ids)
        is_review_all = True

    if not completed_variable_ids:
        completed_variable_ids = request.GET.get('completed_variables').split(',')
        completed_variable_id = request.GET.get('completed_variable_id')
        is_review_all = True

        if completed_variable_id not in completed_variable_ids:
            redirect_url = reverse('coder_app:select_mention', args=[coder_id, project_id])
            return redirect(redirect_url)
        else:
            completed_variable_ids = ','.join(completed_variable_ids)

    coder_data = Coder.objects.get(id=coder_id)
    user_data = coder_data.user
    coder_data.username = user_data.username

    answer_data_meta = DataMeta.objects.get(id=int(completed_variable_id))
    answer_data = answer_data_meta.data
    row_data = Row.objects.get(id=answer_data.row_id)
    mention_data = RowMeta.objects.get(row=row_data)
    column_data = Column.objects.get(id=answer_data.column_id)
    column_meta_data = ColumnMeta.objects.get(column=column_data)
    variable_data = column_meta_data.variable

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
        try:
            social_api_json = requests.get(social_api_url).json()
            social_data = social_api_json['html']
        except:
            social_data = 'Media Error'
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
            'completed_variable_ids': completed_variable_ids,
            'is_review_all': is_review_all
         }
    )

@login_required()
def select_variable(request, coder_id, project_id):
    completed_variable_ids = request.POST.get('completed_variables')
    completed_variables = completed_variable_ids.split(',')

    coder_data = Coder.objects.get(id=coder_id)
    user_data = coder_data.user
    coder_data.username = user_data.username

    if request.method == "POST" and 'confirm-variable' in request.POST or 'submit_review_all' in request.POST:
        completed_variable_id = request.POST.get('completed_variable_id')
        answer = Data.objects.get(id=completed_variable_id)
        answer_meta = DataMeta.objects.get(data=answer)

        if 'variable-freeform' in request.POST:
            variable_value = request.POST.get('variable-freeform')
        elif 'variable-multiple' in request.POST:
            variable_value = request.POST.get('variable-multiple')
        else:
            variable_value = None

        has_adverse_events = request.POST.get('variable-adverse-events')

        if has_adverse_events:
            row_data = Row.objects.get(id=answer.row_id)
            mention = RowMeta.objects.get(row=row_data)

            if not mention.contains_adverse_events:
                mention.contains_adverse_events = True
                mention.adverse_event_datetime_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)

                mention.save()

        if answer.value != variable_value:
            answer.value = variable_value
            answer_meta.corrected = True
            answer.save()

        answer_meta.reviewed = True
        answer_meta.save()

        total_coder_answer_count = DataMeta.objects.filter(coder=coder_data).count()
        corrected_coder_answer_count = DataMeta.objects.filter(coder=coder_data, corrected=True).count()

        if corrected_coder_answer_count == 0:
            coder_rating = 10.0
        else:
            coder_rating_decimal = float(corrected_coder_answer_count) / float(total_coder_answer_count)
            coder_rating_percentage = float(coder_rating_decimal * 100)
            coder_rating_from_hundred = float(100 - coder_rating_percentage)
            coder_rating = float(coder_rating_from_hundred / 10)
            coder_rating = round(coder_rating, 1)

        coder_data.rating = float(coder_rating)
        coder_data.save()

    answer_meta_data = DataMeta.objects.filter(id__in=completed_variables)
    answer_data = Data.objects.filter(id__in=[answer.data_id for answer in answer_meta_data])

    if answer_data:
        row_data = Row.objects.get(id=answer_data[0].row_id)
        mention_data = RowMeta.objects.get(row=row_data)

        for answer_meta in answer_meta_data:
            answer = answer_meta.data
            column_data = Column.objects.get(id=answer.column_id)
            column_meta_data = ColumnMeta.objects.get(column=column_data)
            variable_data = column_meta_data.variable

            if variable_data.is_multiple_choice:
                variable_data.multiple_or_freeform = 'Multiple Choice'
            else:
                variable_data.multiple_or_freeform = 'Freeform'

            answer_meta.variable_data = variable_data

    if request.method == 'POST' and 'submit_review_all' in request.POST:
        completed_variables = ','.join(completed_variables)
        completed_variables_query = '?completed_variables=%s' % completed_variables
        completed_variable_query = '&completed_variable_id=%s' % completed_variable_id
        redirect_suffix = completed_variables_query + completed_variable_query
        redirect_url = reverse('coder_app:review_variables', args=[coder_id, project_id]) + redirect_suffix

        return redirect(redirect_url)

    return render(
        request,
        'coder_app/select_variable.html',
        {
            'coder_data': coder_data,
            'mention_data': mention_data,
            'answer_data': answer_meta_data,
            'project_id': project_id,
            'completed_variable_ids': completed_variable_ids
        }
    )

@login_required()
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

@login_required()
def get_tag_names(request):
    if request.method == "POST" and request.POST.get('tag_id_to_add_to_variable'):
        tag_id = json.loads(request.POST.get('tag_id_to_add_to_variable'))
        tag = Tag.objects.get(id=tag_id)

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

        variable_data = variables

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

@login_required()
def get_project_names(request):
    if request.is_ajax():
        query = request.GET.get('term', '')
        projects = Project.objects.filter(name__icontains=query)
        results = []
        for project in projects:
            project_names_json = {
                'value': project.name,
                'label': project.name,
                'id': project.id
            }
            results.append(project_names_json)
        project_data = json.dumps(results)
    else:
        project_data = 'fail'

    mimetype = 'application/json'
    return HttpResponse(project_data, mimetype)

@login_required()
def edit_tags(request):
    if request.is_ajax() and json.loads(request.POST.get('rename_tag')):
        tag_id = request.POST.get('tag_id')
        tag = Tag.objects.get(id=tag_id)
        new_name = request.POST.get('new_tag_name')

        if new_name != tag.name:
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

        redirect_url = '/coder_project/'

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'redirect_url': redirect_url,
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

@login_required()
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

@login_required()
def create_tag(request):
    if request.method == 'POST' and 'create-tag' in request.POST:
        tag_name = request.POST.get('create-tag')
        new_tag = Tag()
        new_tag.name = tag_name
        new_tag.save()

        url_redirect = reverse('coder_app:edit_tags')

        return redirect(url_redirect)

    return render(
        request,
        'coder_app/create_tag.html',
        {}
    )

@login_required()
def edit_variables(request):
    redirect_url = reverse('coder_app:edit_variables')

    if request.is_ajax() and request.POST.get('variable_action') == 'redirect':
        variable_id = request.POST.get('variable_id')
        base_url = '/coder_project/review_variable/'
        redirect_url = base_url + str(variable_id)

        return HttpResponse(
            json.dumps({
                'result': 'successful!',
                'redirect_url': redirect_url
            }),
            content_type="application/json"
        )

    if request.is_ajax() and request.POST.get('variable_action') == 'bulk_add':
        tag_name = request.POST.get('tag_name')
        variable_ids = json.loads(request.POST.get('variable_ids'))

        tag_to_add = Tag.objects.get(name=tag_name)

        if tag_to_add:
            for variable_id in variable_ids:
                variable = Variable.objects.get(id=variable_id)
                variable.tag_set.add(tag_to_add)

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )
    elif request.is_ajax() and request.POST.get('variable_action') == 'bulk_remove':
        tag_name = request.POST.get('tag_name')
        variable_ids = json.loads(request.POST.get('variable_ids'))

        tag_to_remove = Tag.objects.get(name=tag_name)

        if tag_to_remove:
            for variable_id in variable_ids:
                variable = Variable.objects.get(id=variable_id)
                variable.tag_set.remove(tag_to_remove)

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.method == "POST" and 'bulk-variable-delete' in request.POST:
        variables_to_delete = request.POST.getlist('variable-names[]')
        for variable_to_delete in variables_to_delete:
            variable = Variable.objects.get(id=variable_to_delete)
            variable.delete()

    if request.is_ajax() and request.POST.get('variable_action') == 'delete_single_variable':
        variable_id = request.POST.get('variable_id')
        variable = Variable.objects.get(id=variable_id)
        variable.delete()
        variable_data = serializers.serialize('json', Variable.objects.all())

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and request.POST.get('variable_action') == 'edit_variable':
        variable_id = request.POST.get('variable_id')
        redirect_url = '/coder_project/edit_variable/' + str(variable_id)

        return HttpResponse(
            json.dumps({
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    if request.is_ajax() and request.POST.get('variable_action') == 'copy_variable':
        variable_id = request.POST.get('variable_id')
        variable = Variable.objects.get(id=variable_id)
        project_data = variable.project

        if project_data:
            project_tags = project_data.tag_set.all()
            project_tag_ids = [tag.id for tag in project_tags]
        else:
            project_tag_ids = []

        tag_data = variable.tag_set.exclude(id__in=project_tag_ids)

        variable.pk = None
        variable.save()

        variable.project = None
        variable.name = variable.name + ' COPY'
        variable.save()

        for tag in tag_data:
            variable.tag_set.add(tag)

        copy_tag, created = Tag.objects.get_or_create(name='copy')

        variable.tag_set.add(copy_tag)

        variable_data = serializers.serialize('json', Variable.objects.all())

        return HttpResponse(
            json.dumps({
                'variable_data': variable_data,
                'redirect_url': redirect_url,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

    variable_data = Variable.objects.all()

    return render(
        request,
        'coder_app/edit_variables.html',
        {
            'variable_data': variable_data
        }
    )

@login_required()
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

@login_required()
def tag_to_variable(request, variable_id):
    variable_data = Variable.objects.get(id=variable_id)
    project_data = variable_data.project

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

    if project_data:
        project_tags = project_data.tag_set.all()
        tags = tags.exclude(id__in=[project_tag.id for project_tag in project_tags])

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

@login_required()
def filter_tags(request):
    if request.is_ajax() and request.POST.get('tag_action') == 'filter_tag':
        tag_list = json.loads(request.POST.get('tag_list'))
        filtered_tag_data = []
        tag_data = []
        filtered_tags = Tag.objects.all()

        for tag_id in tag_list:
            tag = Tag.objects.get(id=tag_id)
            tag_name = tag.name

            tag_info = {
                'id': tag_id,
                'name': tag_name
            }
            tag_data.append(tag_info)

            filtered_tags = filtered_tags.filter(name__icontains=tag_name)

        for filtered_tag in filtered_tags:
                filtered_tag_info = {
                    'id': filtered_tag.id,
                    'name': filtered_tag.name
                }
                filtered_tag_data.append(filtered_tag_info)

        return HttpResponse(
            json.dumps({
                'tag_data': tag_data,
                'filtered_tag_data': filtered_tag_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )

@login_required()
def filter_variables(request):
    if request.is_ajax() and request.POST.get('variable_action') == 'filter_variables':
        variable_keywords = json.loads(request.POST.get('variable_keywords'))
        tag_ids = json.loads(request.POST.get('tag_ids'))
        project_ids = json.loads(request.POST.get('project_ids'))

        projects = Project.objects.filter(id__in=project_ids)
        project_data = []
        tags = Tag.objects.filter(id__in=tag_ids)
        tag_data = []
        keyword_data = []

        for project in projects:
            project_info = {
                'id': project.id,
                'name': project.name,
                'type': 'project'
            }
            project_data.append(project_info)

        for tag in tags:
            tag_info = {
                'id': tag.id,
                'name': tag.name,
                'type': 'tag'
            }
            tag_data.append(tag_info)

        for index, keyword in enumerate(variable_keywords):
            keyword_info = {
                'id': index + 1,
                'name': keyword,
                'type': 'variable'
            }
            keyword_data.append(keyword_info)

        filtered_variables = Variable.objects.all()
        filtered_variable_data = []

        if project_ids != []:
            filtered_variables = filtered_variables.filter(project_id__in=project_ids)

        if variable_keywords != []:
            for keyword in variable_keywords:
                filtered_variables = filtered_variables.filter(name__icontains=keyword)

        if tag_ids !=[]:
            filtered_variables = filtered_variables.filter(tag__in=tags)

        for filtered_variable in filtered_variables:
            variable_info = {
                'id': filtered_variable.id,
                'name': filtered_variable.name
            }
            filtered_variable_data.append(variable_info)

        return HttpResponse(
            json.dumps({
                'project_data': project_data,
                'tag_data': tag_data,
                'keyword_data': keyword_data,
                'filtered_variable_data': filtered_variable_data,
                'result': 'successful!'
            }),
            content_type="application/json"
        )
