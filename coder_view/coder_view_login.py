from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from coder_app.models import Coder
import logging
import cgitb; cgitb.enable()
from django.contrib.auth import authenticate, login, update_session_auth_hash

logger = logging.getLogger(__name__)

def coder_view_login(request):
    print('made it here')
    if 'next' in request.GET:
        next_url = request.GET['next']
        url_suffix = '?next=' + next_url
        redirect_url = next_url
    else:
        url_suffix = ''
        coder_id = None
        redirect_url = reverse_lazy('coder_view:coder_splash', urlconf="coder_app_project.urls", args=[coder_id])

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print('user found')
            login(request, user)

            coder = Coder.objects.get(user=user)
            coder_id = coder.id
            redirect_url = reverse_lazy('coder_view:coder_splash', urlconf="coder_app_project.urls", args=[coder_id])
            return HttpResponseRedirect(redirect_url)
        else:
            print('there was error')
            error_message = 'Incorrect username or password'
            action_url = reverse_lazy('coder_view_login') + url_suffix

            return render(request, 'auth/login.html',
                          {'action_url': action_url, 'error_message': error_message})

    error_message = ''
    action_url = reverse_lazy('coder_view:coder_view_login', urlconf='coder_app_project.urls') + url_suffix

    return render(request, 'auth/login.html',
                  {'action_url': action_url, 'error_message': error_message})