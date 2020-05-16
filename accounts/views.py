from django.views import View
from accounts.models import CustomUser
from django.shortcuts import render, redirect

class ProfileView(View):
  def get(self, request, *args, **kwargs):
    user_data = CustomUser.objects.get(id=request.user.id)

    return render(request, 'accounts/profile.html', {
      'user_data': user_data,
    })