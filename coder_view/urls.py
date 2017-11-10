from django.conf.urls import url

from . import views

app_name = 'coder_view'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<coder_id>[0-9]+)/choose_project/$', views.select_project, name='coder_splash')
]