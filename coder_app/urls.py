from django.conf.urls import url

from . import views

app_name = 'coder_app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^variables', views.submit_new_variable, name='submit_new_variable'),
    url(r'^add_project', views.submit_new_project, name='submit_new_project'),
    url(r'^(?P<project_id>[0-9]+)/edit_project/$', views.edit_project, name='edit_project'),
    url(r'^(?P<project_id>[0-9]+)/edit_variable/(?P<variable_id>[0-9]+)/$', views.edit_variable, name='edit_variable'),
    url(r'^add_coder', views.submit_new_coder, name='add_coder'),
    url(r'^(?P<coder_id>[0-9]+)/edit_coder/$', views.edit_coder, name='edit_coder'),
    url(r'^variable_library', views.edit_variable_library, name='variable_library'),
    url(r'^(?P<coder_id>[0-9]+)/coder/(?P<project_id>[0-9]+)/select_mention/$',
        views.select_mention, name='select_mention'),
    url(r'^(?P<coder_id>[0-9]+)/coder/(?P<project_id>[0-9]+)/select_variable/$',
        views.select_variable, name='select_variable'),
    url(r'^(?P<coder_id>[0-9]+)/coder/(?P<project_id>[0-9]+)/review_variables/$',
        views.review_variables, name='review_variables'),
    url(r'^get_variable_names', views.get_variable_names, name='get_variable_names'),
    url(r'^get_tag_names', views.get_tag_names, name='get_tag_names'),
    url(r'^edit_tags', views.edit_tags, name='edit_tags')
]
