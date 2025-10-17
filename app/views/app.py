import json

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.views import View

from nodeodm.models import ProcessingNode
from app.models import Project, Task
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from app.views.utils import get_permissions
from webodm import settings


def index(request):
    print(2)
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('welcome')


@login_required
def dashboard(request):
    no_processingnodes = ProcessingNode.objects.count() == 0
    if no_processingnodes and settings.PROCESSING_NODES_ONBOARDING is not None:
        return redirect(settings.PROCESSING_NODES_ONBOARDING)

    no_tasks = Task.objects.filter(project__owner=request.user).count() == 0
    no_projects = Project.objects.filter(owner=request.user).count() == 0

    permissions = []
    if request.user.has_perm('app.add_project'):
        permissions.append('add_project')

    # Create first project automatically
    if settings.DASHBOARD_ONBOARDING and no_projects and 'add_project' in permissions:
        Project.objects.create(owner=request.user, name=_("First Project"))

    return render(request, 'app/dashboard.html', {'title': _('Dashboard'),
                                                  'no_processingnodes': no_processingnodes,
                                                  'no_tasks': no_tasks,
                                                  'onboarding': settings.DASHBOARD_ONBOARDING,
                                                  'params': {
        'permissions': json.dumps(permissions)
    }.items()
    })


@login_required
def map(request, project_pk=None, task_pk=None):
    title = _("Map")

    if project_pk is not None:
        project = get_object_or_404(Project, pk=project_pk)
        if not request.user.has_perm('app.view_project', project):
            raise Http404()

        if task_pk is not None:
            task = get_object_or_404(Task.objects.defer(
                'orthophoto_extent', 'dsm_extent', 'dtm_extent'), pk=task_pk, project=project)
            title = task.name or task.id
            mapItems = [task.get_map_items()]
            projectInfo = None
        else:
            title = project.name or project.id
            mapItems = project.get_map_items()
            projectInfo = project.get_public_info()

    return render(request, 'app/map.html', {
        'title': title,
        'params': {
            'map-items': json.dumps(mapItems),
            'title': title,
            'public': 'false',
            'share-buttons': 'false' if settings.DESKTOP_MODE else 'true',
            'permissions': json.dumps(get_permissions(request.user, project)),
            'project': json.dumps(projectInfo),
        }.items()
    })


@login_required
def model_display(request, project_pk=None, task_pk=None):
    title = _("3D Model Display")

    if project_pk is not None:
        project = get_object_or_404(Project, pk=project_pk)
        if not request.user.has_perm('app.view_project', project):
            raise Http404()

        if task_pk is not None:
            task = get_object_or_404(Task.objects.defer(
                'orthophoto_extent', 'dsm_extent', 'dtm_extent'), pk=task_pk, project=project)
            title = task.name or task.id
        else:
            raise Http404()

    return render(request, 'app/3d_model_display.html', {
        'title': title,
        'params': {
            'task': json.dumps(task.get_model_display_params()),
            'public': 'false',
            'share-buttons': 'false' if settings.DESKTOP_MODE else 'true'
        }.items()
    })


def about(request):
    return render(request, 'app/about.html', {'title': _('About'), 'version': settings.VERSION})


@login_required
def processing_node(request, processing_node_id):
    pn = get_object_or_404(ProcessingNode, pk=processing_node_id)
    if not pn.update_node_info():
        messages.add_message(request, messages.constants.WARNING, _(
            '%(node)s seems to be offline.') % {'node': pn})

    return render(request, 'app/processing_node.html',
                  {
                      'title': _('Processing Node'),
                      'processing_node': pn,
                      'available_options_json': pn.get_available_options_json(pretty=True)
                  })


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password', )
        widgets = {
            'password': forms.PasswordInput(),
        }


class RegistrationView(View):
    template_path = 'app/registration/registration.html'

    def get(self, request):
        form = UserRegistrationForm()

        return render(request, self.template_path,
                      {
                          'title': _('Регистрация'),
                          'form': form
                      })

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.save()

            # Log-in automatically
            login(request, user, 'django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
        return render(request, self.template_path,
                      {
                          'title': _('Регистрация'),
                          'form': form
                      })


def welcome_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'welcome.html', context={'title': _('Добро пожаловать')})


class ModifiedLoginView(LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect user to index
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Вход')
        return context


@login_required
def logout_view(request):
    logout(request)
    return redirect('welcome')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
