from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import CustomUser
from accounts.forms import ProfileForm, SignupUserForm
from django.shortcuts import render, redirect
from allauth.account import views
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib import messages
import requests
import json
import jwt


LINE_CHANNEL_ID = settings.LINE_CHANNEL_ID
LINE_CHANNEL_SECRET = settings.LINE_CHANNEL_SECRET
REDIRECT_URL = settings.LINE_REDIRECT_URL

# LINEloginのリダイレクト先
class LineLoginView(View):
  def get(self, request, *args, **kwargs):
    context = {}
    # 認可コードを取得する
    request_code = request.GET.get('code')
    uri_access_token = 'https://api.line.me/oauth2/v2.1/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data_params = {
        'grant_type': 'authorization_code',
        'code': request_code,
        'redirect_uri': REDIRECT_URL,
        'client_id': LINE_CHANNEL_ID,
        'client_secret': LINE_CHANNEL_SECRET
    }

    # トークンを取得するためにリクエストを送る
    response_post = requests.post(uri_access_token, headers=headers, data=data_params)

    # 今回は"id_token"のみを使用する
    line_id_token = json.loads(response_post.text)['id_token']

    # ペイロード部分をデコードすることで、ユーザ情報を取得する
    user_profile = jwt.decode(line_id_token,
                              LINE_CHANNEL_SECRET,
                              audience=LINE_CHANNEL_ID,
                              issuer='https://access.line.me',
                              algorithms=['HS256'])

    # LINEで取得した情報と、ユーザーデータベースを付け合わせ
    line_user, created = CustomUser.objects.get_or_create(email=user_profile['email'])

    if (created):
        line_user.first_name = user_profile['name']
        line_user.save()

    # そのままログインさせる
    login(request, line_user, backend='django.contrib.auth.backends.ModelBackend')

    return render(request, 'app/index.html', context)

class SignupView(views.SignupView):
  template_name = 'accounts/signup.html'
  form_class = SignupUserForm

class LogoutView(views.LogoutView):
  template_name = 'accounts/logout.html'

  def post(self, *args, **kwargs):
    if self.request.user.is_authenticated:
      self.logout()
    return redirect('/')

class LoginView(views.LoginView):
  template_name = 'accounts/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['channel_id'] = LINE_CHANNEL_ID
    context['redirect_url'] = REDIRECT_URL
    context['random_state'] = "line1216" # 参照元ママ
    return context

class ProfileEditView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.get(id=request.user.id)
    form = ProfileForm(
      request.POST or None,
      initial={
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'department': user_data.department
      }
    )

    return render(request, 'accounts/profile_edit.html', {
      'form': form
    })
  
  def post(self, request, *args, **kwargs):
    form = ProfileForm(request.POST or None)
    if form.is_valid():
      user_data = CustomUser.objects.get(id=request.user.id)
      user_data.first_name = form.cleaned_data['first_name']
      user_data.last_name = form.cleaned_data['last_name']
      user_data.department = form.cleaned_data['department']
      user_data.save()
      return redirect('profile')

    return render(request, 'accounts/profile.html', {
      'form': form
    })

class ProfileView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.get(id=request.user.id)

    return render(request, 'accounts/profile.html', {
      'user_data': user_data,
    })