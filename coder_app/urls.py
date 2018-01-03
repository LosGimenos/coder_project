from django.conf.urls import url

from . import views

# from AUTH URLS
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
# from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from . import auth_pangea_common_views
import os

app_name = 'coder_app'
urlpatterns = [
    # url(r'^$', views.index, name='index'),
    url(r'^$', views.index, name='homepage'),
    url(r'^variables', views.submit_new_variable, name='submit_new_variable'),
    url(r'^add_project', views.submit_new_project, name='submit_new_project'),
    url(r'^(?P<project_id>[0-9]+)/edit_project/$', views.edit_project, name='edit_project'),
    url(r'edit_variable/(?P<variable_id>[0-9]+)/$', views.edit_variable, name='edit_variable'),
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
    url(r'^get_project_names', views.get_project_names, name='get_project_names'),
    url(r'^edit_tags', views.edit_tags, name='edit_tags'),
    url(r'^review_tag/(?P<tag_id>[0-9]+)', views.review_tag, name='review_tag'),
    url(r'^create_tag', views.create_tag, name='create_tag'),
    url(r'^edit_variables', views.edit_variables, name='edit_variables'),
    url(r'^review_variable/(?P<variable_id>[0-9]+)', views.review_variable, name='review_variable'),
    url(r'^tag_to_variable/(?P<variable_id>[0-9]+)', views.tag_to_variable, name='tag_to_variable'),
    url(r'^filter_tags', views.filter_tags, name='filter_tags'),
    url(r'^filter_variables', views.filter_variables, name='filter_variables'),

    # AUTH URLS
    # url(r'^$', RedirectView.as_view(url=reverse_lazy('collect_homepage',urlconf='coder_app.urls')), name='homepage'),
    # url(r'^login/$', auth_pangea_common_views.pangea_login, name='login'),
    # url(r'^logout/$', auth_views.logout, {'next_page': reverse_lazy('login', urlconf='coder_app.urls')}, name='logout'),
    # url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'common/auth/password_reset.html',
    #                                                      'post_reset_redirect': reverse_lazy('password_reset_done',urlconf='coder_app.urls'),
    #                                                      'email_template_name': 'common/auth/password_reset_email.html',
    #                                                      'subject_template_name': 'common/auth/password_reset_subject.txt',
    #                                                      'from_email': 'no-reply@cambriananalytics.com'},
    #                                                      name='password_reset'),
    # url(r'^password_reset/done/$', auth_views.password_reset_done, {'template_name': 'common/auth/password_reset_done.html'}, name='password_reset_done'),
    # url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #     auth_views.password_reset_confirm, {'template_name': 'common/auth/password_reset_confirm.html'}, name='password_reset_confirm'),
    # url(r'^reset/done/$', auth_views.password_reset_complete, {'template_name': 'common/auth/password_reset_complete.html'}, name='password_reset_complete'),
    # url(r'^pangea_admin_pangea', admin.site.urls),
    # url('^', include('django.contrib.auth.urls'))
]
