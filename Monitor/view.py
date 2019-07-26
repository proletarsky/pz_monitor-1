from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls.base import reverse_lazy
from .form import UserRegistrationForm, UserEditForm, ProfileEditForm, CodeForm
from machines.models import Profile, Code
from django.views.generic import FormView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from random import randint


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
            profile.phone = user_form.cleaned_data['phone']
            profile.save()
            # Сохранение пользователя c  дополнительными данными из модели Code(code)
            code = Code.objects.create(user=new_user)
            code.code = send_email(new_user.email)
            code.save()
            url = reverse_lazy('validate') + '?user={0}'.format(new_user.id)
            return redirect(url)
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)
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

    # Генерация кода безопасности


def generate_code():
    array = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    register_code = ""
    for i in range(4):
        index = randint(0, 9)
        register_code += str(array[index])
    return register_code


# Отправка письма
def send_email(email):
    register_code = ""
    register_code = generate_code()
    msg = 'Здравствуйте!\n Для подверждения регистрации на сайте введите код: ' + register_code + ".\nЕсли вы не регистрировались на сайте Портал ПАО Пролетарский завод, не обращайте внимание на это письмо."
    send_mail('Подтверждение регистрации', msg, 'monitor@proletarsky.ru', [email])
    return register_code


# Отправка письма если код указан неверно
def send_email2(email):
    register_code = ""
    register_code = generate_code()
    msg = 'Здравствуйте!\n Вы указали неправильный код для подверждения регистрации на сайте.\n Держите новый код: ' + register_code + ".\nЕсли вы не регистрировались на сайте Портал ПАО Пролетарский завод, не обращайте внимание на это письмо."
    send_mail('Подтверждение регистрации', msg, 'monitor@proletarsky.ru', [email])
    return register_code


# Подтверждение кода безопасности
def validate(request):
    if request.method == 'POST':
        code_form = CodeForm(request.POST)
        if code_form.is_valid():
            user = code_form.cleaned_data['user_id']
            code = code_form.cleaned_data['code']
            code_from_base = Code.objects.filter(user_id=user).first()
            if code == code_from_base.code:
                active_user = User.objects.filter(id=user).first()
                active_user.is_active = True
                active_user.save()
                return render(request, 'account/register_done.html')
            else:
                code = Code.objects.filter(user_id=user).first()
                email = User.objects.filter(id=user).first()
                code.code = send_email2(email.email)
                code.save()
                url = reverse_lazy('not_validate') + '?user={0}'.format(user)
                return redirect(url)
    else:
        code_form = CodeForm(request.GET)
        return render(request, 'account/register_code.html', {'code_form': code_form})


def not_validate(request):
    if request.method == 'POST':
        code_form = CodeForm(request.POST)
        if code_form.is_valid():
            user = code_form.cleaned_data['user_id']
            code = code_form.cleaned_data['code']
            code_from_base = Code.objects.filter(user_id=user).first()
            if code == code_from_base.code:
                active_user = User.objects.filter(id=user).first()
                active_user.is_active = True
                active_user.save()
                return render(request, 'account/register_done.html')
            else:
                code = Code.objects.filter(user_id=user).first()
                email = User.objects.filter(id=user).first()
                code.code = send_email2(email.email)
                code.save()
                url = reverse_lazy('not_validate') + '?user={0}'.format(user)
                return redirect(url)
    else:
        code_form = CodeForm(request.GET)
        return render(request, 'account/register_not_done.html', {'code_form': code_form})
