from django.conf.urls import url

from . import views

app_name = 'coder_view'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<coder_id>[0-9]+)/project_select/$', views.select_project, name='coder_splash'),
    url(r'^(?P<coder_id>[0-9]+)/project_overview/(?P<project_id>[0-9]+)/project_query/(?P<row_id>[0-9]+)/$', views.project_overview, name='coder_project_overview'),
    url(r'^(?P<coder_id>[0-9]+)/project_answering/(?P<project_id>[0-9]+)/project_query/(?P<row_id>[0-9]+)/variable/(?P<variable_id>[0-9]+)/$',
        views.project_answering, name='coder_project_answering')
]