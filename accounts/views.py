import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail

from content.models import Plain
from .models import EmailVerificationToken, Profile


class ProfilePage(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'auth/profile.html')


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            # Пытаемся найти неиспользованный токен
            verification_token = EmailVerificationToken.objects.get(token=token, is_used=False)
        except EmailVerificationToken.DoesNotExist:
            # Проверяем, может токен существует но уже использован
            try:
                used_token = EmailVerificationToken.objects.get(token=token, is_used=True)
                messages.error(request, 'Эта ссылка уже была использована! Войдите в свой аккаунт!')
            except EmailVerificationToken.DoesNotExist:
                messages.error(request, 'Неверная или недействительная ссылка активации!')
            return redirect('content:page', slug='login')

        # Получаем профиль пользователя
        try:
            profile = Profile.objects.get(user=verification_token.user)
        except Profile.DoesNotExist:
            messages.error(request, 'Профиль пользователя не найден!')
            return redirect('content:page', slug='login')

        # Проверяем статус профиля
        if profile.status != 'pending_email':
            messages.warning(request, 'Аккаунт уже активирован')
            return redirect('accounts:home')

        # Генерируем новый пароль
        new_password = f'{uuid.uuid4()}'

        # Получаем объект пользователя
        user = profile.user  # Сохраняем ссылку на пользователя

        # Устанавливаем новый пароль
        user.set_password(new_password)  # ВАЖНО: используйте set_password, а не прямое присвоение
        user.save()

        # Меняем статус
        profile.status = 'pending_review'
        profile.save()

        # Помечаем токен как использованный
        verification_token.is_used = True
        verification_token.save()

        subject = 'Успешное подтверждение аккаунта на сайте Steppe Intelligence'

        if settings.DEBUG:
            domain = 'http://127.0.0.1:8000'
        else:
            domain = settings.DOMAIN
        link = f"{domain}{reverse('content:page', kwargs={'slug': 'login'})}"

        message_template = render_to_string('messages/success-confirm.html', {
            'name': profile.name,
            'email': profile.user.email,
            'subject': subject,
            'link': link,
            'password': new_password
        })

        send_mail(
            subject,
            message_template,
            settings.EMAIL_HOST_USER,
            [profile.user.email],
            html_message=message_template,
            fail_silently=False
        )

        authenticated_user = authenticate(
            request,
            username=user.username,
            password=new_password
        )

        if authenticated_user is not None:
            login(request, user)
            return redirect('accounts:home')
        else:
            messages.success(request, 'Ошибка авторизации')
            return redirect('content:page', slug='login')


class MyPublicationsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'auth/my-publications.html')


class MyPlainView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'plains': Plain.objects.filter(is_active=True)
        }
        return render(request, 'auth/my-plain.html', context=context)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('content:home')
