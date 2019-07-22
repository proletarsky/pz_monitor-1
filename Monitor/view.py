from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls.base import reverse_lazy
from .form import UserRegistrationForm, UserEditForm, ProfileEditForm, CodeForm
from machines.models import Profile

def main_index(request):
    return render(request, 'main_index.html')


# Регистрация пользователей
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Создание пользователятеля, но пока не сохраняем его
            new_user = user_form.save(commit=False)
            # Устанвока пароля
            new_user.set_password(user_form.cleaned_data['password'])
            # Сохранение пользователя c  данными из модели User(username,password,firstname,lastname)
            new_user.save()
            # Сохранение пользователя c  дополнительными данными из модели Profile(phone)
            profile = Profile.objects.filter(user=new_user).first()
            profile.phone=user_form.cleaned_data['phone']
            profile.save()

            return redirect('validate', user=new_user.id)
            # return render(request, 'accounts/validate/', {'new_user': new_user.id})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(request.POST,instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return render(request,
                      'account/edit.html',
                      {'user_form': user_form,
                       'profile_form': profile_form})


# Подтверждение кода безопасности
def validate(request, user=None):
    if request.method == 'POST':
        code = request.POST.get("code")
        if code == "777":
            return render(request, 'account/register_done.html')
        else:
            return render(request, 'account/register_not_done.html')
    else:
        code_form = CodeForm(request.GET)
        user = request.GET.get('new_user')
        return render(request, 'account/register_code.html', {'code_form': code_form, 'new_user': user})

