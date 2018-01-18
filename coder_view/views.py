# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Max
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from coder_app.models import Project, Variable, Coder, Row, Column, Data, RowMeta, ColumnMeta, DataMeta
import random
import datetime
import pytz
import requests

def index(request):
    coder_data = Coder.objects.all()

    return render(request, 'coder_view/index.html', {'coder_data': coder_data})

def select_project(request, coder_id):
    coder = Coder.objects.get(id=coder_id)
    projects = coder.project_set.all()
    project_data = []

    if request.method == 'POST' and 'all_projects_view' in request.POST:
        project_ids_to_render = {}

        for project in projects:
            all_rows = RowMeta.objects.filter(project=project)
            num_variables_in_project = project.variable_set.all().count()
            all_rows_count = all_rows.count()

            uncompleted_rows = all_rows.filter(is_completed=False)
            completed_rows = all_rows.filter(is_completed=True)
            completed_rows_by_coder = completed_rows.filter(coder=coder).count()
            completed_rows_count = completed_rows.count()

            project_is_available = False

            for row in uncompleted_rows:
                if not row.coder_id or int(coder_id) == int(row.coder_id):
                    project_is_available = True

            if project_is_available:
                try:
                    row = all_rows[0]
                    row_id = row.id
                except:
                    row_id = None

                single_project = {
                    'id': project.id,
                    'name': project.name,
                    'rate': project.rate,
                    'all_rows_count': all_rows_count,
                    'completed_rows_count': completed_rows_count,
                    'row_id': row_id,
                    'num_variables_in_project': num_variables_in_project,
                    'completed_rows_by_coder': completed_rows_by_coder,
                    'is_frozen': project.is_frozen
                }

                project_ids_to_render['project_id'] = project.id

                if all_rows_count <= completed_rows_count:
                    single_project['is_completed'] = True

                project_data.append(single_project)

                for completed_row in completed_rows:
                    if completed_row.project_id not in [row.project_id for row in uncompleted_rows] :
                        total_answered_vars = DataMeta.objects.filter(coder=coder, project=project)
                        corrected_var_count = total_answered_vars.filter(coder=coder, project=project, corrected=True).count()

                        single_project = {
                            'id': project.id,
                            'name': project.name,
                            'rate': project.rate,
                            'all_rows_count': all_rows_count,
                            'completed_rows_count': completed_rows_count,
                            'row_id': row_id,
                            'is_completed': True,
                            'num_variables_in_project': num_variables_in_project,
                            'corrected_var_count': corrected_var_count,
                            'total_answered_vars': total_answered_vars.count(),
                            'completed_rows_by_coder': completed_rows_by_coder,
                            'is_frozen': project.is_frozen
                        }

                        project_data.append(single_project)

    elif request.method == 'POST' and 'completed_projects_view' in request.POST:
        for project in projects:
            all_rows = RowMeta.objects.filter(project=project)
            num_variables_in_project = project.variable_set.all().count()
            all_rows_count = all_rows.count()
            completed_rows = all_rows.filter(
                is_completed=True
            )
            completed_rows_count = completed_rows.count()

            try:
                row = all_rows[0]
                row_id = row.id
            except:
                row_id = None

            if all_rows_count <= completed_rows_count:
                single_project = {
                    'id': project.id,
                    'name': project.name,
                    'rate': project.rate,
                    'all_rows_count': all_rows_count,
                    'completed_rows_count': completed_rows_count,
                    'row_id': row_id,
                    'is_completed': True,
                    'num_variables_in_project': num_variables_in_project,
                    'is_frozen': project.is_frozen
                }

                project_data.append(single_project)

    else:
        # pending projects default
        for project in projects:
            all_rows = RowMeta.objects.filter(project=project)
            all_rows_count = all_rows.count()
            num_variables_in_project = project.variable_set.all().count()

            uncompleted_rows = all_rows.filter(is_completed=False)
            completed_rows_by_coder = all_rows.filter(coder=coder, is_completed=True).count()


            project_is_available = False

            for row in uncompleted_rows:
                if not row.coder_id or int(coder_id) == int(row.coder_id):
                    project_is_available = True

            if project_is_available:
                completed_rows = all_rows.filter(
                    is_completed=True
                )
                completed_rows_count = completed_rows.count()

                try:
                    row = all_rows[0]
                    row_id = row.id
                except:
                    row_id = None

                single_project = {
                    'id': project.id,
                    'name': project.name,
                    'rate': project.rate,
                    'all_rows_count': all_rows_count,
                    'completed_rows_count': completed_rows_count,
                    'row_id': row_id,
                    'num_variables_in_project': num_variables_in_project,
                    'completed_rows_by_coder': completed_rows_by_coder,
                    'is_frozen': project.is_frozen
                }

                if all_rows_count <= completed_rows_count:
                    single_project['is_completed'] = True

                project_data.append(single_project)

    return render(
        request,
        'coder_view/select_project.html',
        {
            'coder_data': coder,
            'project_data': project_data
        })

def project_overview(request, coder_id, project_id, row_id):
    project_data = Project.objects.get(id=project_id)

    if project_data.is_frozen:
        redirect_url = reverse('coder_view:coder_splash', args=[coder_id])
        return redirect(redirect_url)

    dataset = project_data.dataset
    coder = Coder.objects.get(id=coder_id)

    #check if coder is currently working on a row query

    previous_coder_row = RowMeta.objects.filter(
        project=project_data,
        coder=coder,
        is_completed=False
    )

    if not previous_coder_row:
        rows = RowMeta.objects.filter(
            project=project_data,
            is_locked=False,
            is_completed=False
        )

        if rows:
            row = random.choice(rows)
        else:
            return redirect('/coder_view/' + str(coder_id) + '/project_select')

        row.is_locked = True
        row.coder = coder
        row.save()

        row_data = row
    else:
        row_data = previous_coder_row[0]

    row_id = row_data.id

    # get current column with error handling if column_number does not match row curr_col_index

    current_column_index = row_data.curr_col_index
    next_column_index = current_column_index + 1
    no_column_found = False
    no_next_column_found = False

    greatest_col_index = ColumnMeta.objects.filter(project=project_data).aggregate(Max('column_number'))
    greatest_col_index = greatest_col_index['column_number__max']

    column_acquired = False

    num_attempts = 0
    while not column_acquired:
        attempted_column = ColumnMeta.objects.filter(project=project_data, is_variable=True, column_number=current_column_index)

        try:
            column = ColumnMeta.objects.filter(
                project=project_data,
                is_variable=True,
                column_number=current_column_index
            )[0]
            column_acquired = True
        except:
            current_column_index = current_column_index + 1
            num_attempts += 1
            if num_attempts > 20:
                return

    #load up next column information URL with error handling

    next_column_acquired = False

    while not next_column_acquired:
        try:
            next_column = ColumnMeta.objects.filter(
                project=project_data,
                is_variable=True,
                column_number=next_column_index
            )[0]
            next_column_acquired = True
        except:
            if next_column_index > greatest_col_index:
                no_next_column_found = True
                break

            if current_column_index > next_column_index:
                next_column_index = current_column_index + 1
            else:
                next_column_index = next_column_index + 1

    # get variable for render

    variable_data = Variable.objects.get(id=column.variable_id)

    if no_next_column_found:
        next_variable_id = None
    else:
        next_variable_id = next_column.id

    return render(
        request,
        'coder_view/project_overview.html',
        {
            'coder_id': coder_id,
            'project_data': project_data,
            'variable_data': variable_data,
            'next_variable_id': next_variable_id,
            'row_id': row_id,
            'column_data': column
        })

def project_answering(request, coder_id, project_id, row_id, column_id):
    next_variable_id = request.POST.get('next_variable_id')
    project_data = Project.objects.get(id=project_id)

    if project_data.is_frozen:
        redirect_url = reverse('coder_view:coder_splash', args=[coder_id])
        return redirect(redirect_url)

    column = ColumnMeta.objects.get(id=column_id)
    column_base = column.column
    variable_id = column.variable_id
    row_data = RowMeta.objects.get(id=row_id)
    row = row_data.row
    variable_data = Variable.objects.get(id=variable_id)
    coder = Coder.objects.get(id=coder_id)
    dataset = project_data.dataset

    all_columns_in_project = ColumnMeta.objects.filter(project=project_data, is_variable=True)
    total_variable_count = all_columns_in_project.count()
    completed_variable_count = row_data.curr_col_index

    # check media source as Twitter or Instagram
    if row_data.is_twitter:
        source = 'twitter'
    elif row_data.is_instagram:
        source = 'instagram'

    # make API call to Social Media API
    media_url = row_data.media_url
    media_text = row_data.media_text
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


    if request.method == 'POST' and 'start-answer' not in request.POST:
        # save values to Data model

        date_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)


        # data = Data.objects.filter(
        #     project=project_data,
        #     column=column,
        #     row=row_data
        # ).first()

        # if not data:
        data = Data(
            dataset=dataset,
            column=column_base,
            row=row,
            date=date_submitted
        )

        if 'variable-freeform' in request.POST:
            data.value = request.POST.get('variable-freeform')
        elif 'variable-multiple' in request.POST:
            selected_choice = request.POST.get('variable-multiple')
            data.value = selected_choice

        data.save()

        data_meta = DataMeta(
            data=data,
            coder=coder,
            project=project_data
        )
        data_meta.save()

        # check for adverse events
        if 'variable-adverse-events' in request.POST:
            row_data.contains_adverse_events = True
            row_data.adverse_event_datetime_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)
            project_data.contains_adverse_events = True


        # advance row curr_col_index count
        row_data.curr_col_index = row_data.curr_col_index + 1
        row_data.save()

        current_column_index = row_data.curr_col_index

        # check if row is complete
        greatest_col_index = ColumnMeta.objects.filter(project=project_data).aggregate(Max('column_number'))
        greatest_col_index = greatest_col_index['column_number__max']

        if row_data.curr_col_index > greatest_col_index:
            row_data.is_completed = True
            row_data.save()

        if row_data.is_completed == True:
            rows = RowMeta.objects.filter(
                is_completed=False,
                is_locked=False,
                project=project_data
            )

            try:
                row_data = random.choice(rows)
            except:
                redirect_url = 'coder_view/' + str(coder.id) + '/project_select/'
                return redirect(redirect_url)

            current_column_index = row_data.curr_col_index
            column = ColumnMeta.objects.get(column_number=current_column_index)
            variable_data = Variable.objects.get(column=column.variable_id)

        # add next column information

        next_column_acquired = False
        no_next_column_found = False

        while not next_column_acquired:
            try:
                next_column = ColumnMeta.objects.filter(
                    project=project_data,
                    is_variable=True,
                    column_number=current_column_index
                )[0]
                next_column_acquired = True
            except:
                if next_column_index > greatest_col_index:
                    no_next_column_found = True
                    break

                if current_column_index > next_column_index:
                    next_column_index = current_column_index + 1
                else:
                    next_column_index = next_column_index + 1

        if no_next_column_found:
            next_variable_id = None
        else:
            next_variable_id = next_column.id

        if not next_variable_id:
            redirect_url = '/coder_view/' + str(coder.id) + '/project_select/'
        else:
            redirect_url = '/coder_view/' + str(coder.id) + '/project_answering/' + str(project_data.id) + '/project_mention/'+ str(row_data.id) + '/variable/' + str(next_variable_id)
        return redirect(redirect_url)

    return render(
        request,
        'coder_view/project_answering.html',
        {
            'coder_id': coder_id,
            'project_id': project_id,
            'variable_data': variable_data,
            'row_id': row_id,
            'next_variable_id': next_variable_id,
            'total_variable_count': total_variable_count,
            'completed_variable_count': completed_variable_count,
            'social_data': social_data,
            'media_url': media_url,
            'media_text': media_text
        })



