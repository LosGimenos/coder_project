# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Max
from django.shortcuts import render, redirect, HttpResponse
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
            dataset = project.dataset
            row_data = Row.objects.filter(dataset=dataset)
            row_ids = [row.id for row in row_data]
            all_rows = RowMeta.objects.filter(row_id__in=row_ids)
            all_rows_count = all_rows.count()

            uncompleted_rows = all_rows.filter(is_completed=False)
            completed_rows = all_rows.filter(is_completed=True)
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
                    'row_id': row_id
                }

                project_ids_to_render['project_id'] = project.id

                if all_rows_count <= completed_rows_count:
                    single_project['is_completed'] = True

                project_data.append(single_project)

                for completed_row in completed_rows:
                    if completed_row.id not in project_ids_to_render:
                        single_project = {
                            'id': project.id,
                            'name': project.name,
                            'rate': project.rate,
                            'all_rows_count': all_rows_count,
                            'completed_rows_count': completed_rows_count,
                            'row_id': row_id,
                            'is_completed': True
                        }

                        project_data.append(single_project)

    elif request.method == 'POST' and 'completed_projects_view' in request.POST:
        for project in projects:
            dataset = project.dataset
            row_data = Row.objects.filter(dataset=dataset)
            row_ids = [row.id for row in row_data]
            all_rows = RowMeta.objects.filter(row_id__in=row_ids)
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
                    'is_completed': True
                }

                project_data.append(single_project)

    else:
        # pending projects default
        for project in projects:
            dataset = project.dataset
            row_data = Row.objects.filter(dataset=dataset)
            row_ids = [row.id for row in row_data]
            all_rows = RowMeta.objects.filter(row_id__in=row_ids)
            all_rows_count = all_rows.count()

            uncompleted_rows = all_rows.filter(is_completed=False)

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
                    'row_id': row_id
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
    dataset = project_data.dataset
    coder = Coder.objects.get(id=coder_id)

    print('this is project id', project_data.id)
    #check if coder is currently working on a row query

    previous_coder_row = Row.objects.filter(
        project=project_data,
        coder=coder,
        is_completed=False
    )

    if not previous_coder_row:
        rows = Row.objects.filter(
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

    greatest_col_index = Column.objects.filter(project=project_data).aggregate(Max('column_number'))
    print('greatest col from filter', greatest_col_index)
    greatest_col_index = greatest_col_index['column_number__max']

    column_acquired = False

    num_attempts = 0
    while not column_acquired:
        print(current_column_index, 'current index', row_id, 'this is row id')
        attempted_column = Column.objects.filter(project=project_data, is_variable=True, column_number=current_column_index)
        print(attempted_column, 'attempted col')

        try:
            column = Column.objects.filter(
                project=project_data,
                is_variable=True,
                column_number=current_column_index
            )[0]
            column_acquired = True
            print('made it out')
        except:
            current_column_index = current_column_index + 1
            num_attempts += 1
            print('current', current_column_index)
            if num_attempts > 20:
                return

    #load up next column information URL with error handling

    next_column_acquired = False

    while not next_column_acquired:
        try:
            next_column = Column.objects.filter(
                project=project_data,
                is_variable=True,
                column_number=next_column_index
            )[0]
            next_column_acquired = True
            print('made it out of next')
        except:
            if next_column_index > greatest_col_index:
                no_next_column_found = True
                break

            if current_column_index > next_column_index:
                next_column_index = current_column_index + 1
            else:
                next_column_index = next_column_index + 1
            print('next', next_column_index)

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

    column = Column.objects.get(id=column_id)
    variable_id = column.variable_id
    project_data = Project.objects.get(id=project_id)
    row_data = Row.objects.get(id=row_id)
    variable_data = Variable.objects.get(id=variable_id)
    coder = Coder.objects.get(id=coder_id)

    all_columns_in_project = Column.objects.filter(project=project_data, is_variable=True)
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
        social_api_json = requests.get(social_api_url).json()
        social_data = social_api_json['html']
    else:
        social_data = None

    if request.method == 'POST' and 'start-answer' not in request.POST:
        # save values to Data model

        date_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)

        data = Data.objects.filter(
            project=project_data,
            column=column,
            row=row_data
        ).first()

        if not data:
            data = Data(
                project=project_data,
                column=column,
                row=row_data
            )

        if 'variable-freeform' in request.POST:
            data.value = request.POST.get('variable-freeform')
        elif 'variable-multiple' in request.POST:
            selected_choice = request.POST.get('variable-multiple')
            data.value = selected_choice

        data.coder = coder
        data.date = date_submitted
        data.save()

        # check for adverse events
        if 'variable-adverse-events' in request.POST:
            row_data.contains_adverse_events = True
            row_data.adverse_event_datetime_submitted = datetime.datetime.now().replace(tzinfo=pytz.UTC)


        # advance row curr_col_index count
        row_data.curr_col_index = row_data.curr_col_index + 1
        row_data.save()

        current_column_index = row_data.curr_col_index

        # check if row is complete
        greatest_col_index = Column.objects.filter(project=project_data).aggregate(Max('column_number'))
        greatest_col_index = greatest_col_index['column_number__max']

        if row_data.curr_col_index > greatest_col_index:
            row_data.is_completed = True
            row_data.save()

        if row_data.is_completed == True:
            rows = Row.objects.filter(
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
            column = Column.objects.get(column_number=current_column_index)
            variable_data = Variable.objects.get(column=column.variable_id)

        # add next column information

        next_column_acquired = False
        no_next_column_found = False

        while not next_column_acquired:
            try:
                next_column = Column.objects.filter(
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



