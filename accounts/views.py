import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from pathlib import Path

from content.models import Plain, Country, Expertise, Article, PublicationType
from .models import EmailVerificationToken, Profile


class ProfilePage(LoginRequiredMixin, View):
    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        countries = Country.objects.filter(is_active=True)
        expertises = Expertise.objects.filter(is_active=True)

        context = {
            'profile': profile,
            'countries': countries,
            'expertises': expertises,
        }

        return render(request, 'auth/profile.html', context=context)

    def post(self, request):
        photo = request.FILES.get('photo')
        name = request.POST.get('name')
        lastname = request.POST.get('lastname')
        phone = request.POST.get('phone')
        linkedin = request.POST.get('linkedin')
        post = request.POST.get('post')
        bio = request.POST.get('bio')
        experience = request.POST.get('experience')
        password = request.POST.get('password')
        country = request.POST.get('country')
        expertise_ids = request.POST.getlist('expertise')

        error__messages = []

        if not name:
            error__messages.append('Имя обязательно к заполнению!')

        if not lastname:
            error__messages.append('Фамилия обязательна к заполнению!')

        if not country:
            error__messages.append('Необходимо выбрать страну!')

        if not expertise_ids:
            error__messages.append('Необходимо выбрать хотя бы одну сферу экспертизы!')

        if error__messages:
            for error in error__messages:
                messages.error(request, f'{error}')
            return redirect('accounts:home')

        if password:
            request.user.set_password(password)

        if photo:
            if request.user.profile.photo:
                try:
                    old_photo_path = Path(request.user.profile.photo.path)

                    # если файл существует и отличается от нового
                    if old_photo_path.exists():
                        old_photo_path.unlink()
                except Exception:
                    pass

            request.user.profile.photo = photo

        country = Country.objects.get(pk=country)

        request.user.profile.name = name
        request.user.profile.lastname = lastname
        request.user.profile.phone = phone
        request.user.profile.linkedin = linkedin
        request.user.profile.post = post
        request.user.profile.bio = bio
        request.user.profile.experience = experience
        request.user.profile.country = country
        request.user.profile.expertises.set(expertise_ids)

        request.user.save()
        request.user.profile.save()

        update_session_auth_hash(request, request.user)

        messages.success(request, 'Данные успешно обновлены!')
        return redirect('accounts:home')


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
        profile = Profile.objects.get(user=request.user)
        publications = Article.objects.filter(author=request.user)

        paginator = Paginator(publications, 12)
        page_number = request.GET.get('page', 1)

        try:
            publications_page = paginator.page(page_number)
        except PageNotAnInteger:
            publications_page = paginator.page(1)
        except EmptyPage:
            publications_page = paginator.page(paginator.num_pages)

        context = {
            'publications': publications_page,
            'paginator': paginator,
            'profile': profile,
        }

        return render(request, 'auth/my-publications.html', context=context)


class MyPlainView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'plains': Plain.objects.filter(is_active=True),
            'profile': Profile.objects.get(user=request.user)
        }
        return render(request, 'auth/my-plain.html', context=context)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('content:home')


class AddPublicationView(View):
    def get(self, request):
        context = {
            'form_data': request.session.pop('form_data', {}),
            'expertises': Expertise.objects.filter(is_active=True),
            'countries': Country.objects.filter(is_active=True),
            'types': PublicationType.objects.filter(is_active=True),
        }
        return render(request, 'auth/add-publication.html', context=context)

    def post(self, request, *args, **kwargs):
        request.session['form_data'] = request.POST.dict()

        title = (request.POST.get('title') or '').strip()
        date = (request.POST.get('date') or '').strip()
        image = request.FILES.get('image')
        short_text = (request.POST.get('short_text') or '').strip()
        text = (request.POST.get('text') or '').strip()
        slug = (request.POST.get('slug') or '').strip()
        order = (request.POST.get('order') or '').strip()
        by_subscription = bool(request.POST.get('by_subscription'))
        expertise_ids = request.POST.getlist('expertise')
        country_ids = request.POST.getlist('country')
        type_ids = request.POST.getlist('type')

        error__messages = []

        if not title:
            error__messages.append('Поле «Заголовок» обязательно к заполнению!')

        if not date:
            error__messages.append('Поле «Дата» обязательно к заполнению!')

        if not image:
            error__messages.append('Необходимо загрузить изображение!')

        if not short_text:
            error__messages.append('Поле «Анонс» обязательно к заполнению!')

        if not text:
            error__messages.append('Поле «Текст» обязательно к заполнению!')

        if slug:
            base_slug = slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
        else:
            error__messages.append('Поле «Slug» обязательно к заполнению!')

        if order:
            try:
                order = int(order)
                if order < 1:
                    error__messages.append('Порядковый номер не может быть меньше нуля!')
            except ValueError:
                error__messages.append('Ошибка с форматом поля «Порядковый номер»!')
        else:
            error__messages.append('Поле «Порядковый номер» обязательно к заполнению!')

        if error__messages:
            for error in error__messages:
                messages.error(request, f'{error}')
            return redirect('accounts:add_publication')

        new_article = Article.objects.create(
            title=title,
            title_h1=title,
            date=date,
            image=image,
            short_text=short_text,
            text=text,
            author=User.objects.get(pk=request.user.pk),
            slug=slug,
            by_subscription=by_subscription or False,
            order=order,
            is_active=False,
        )

        new_article.types.set(type_ids)
        new_article.countries.set(country_ids)
        new_article.expertises.set(expertise_ids)

        messages.error(request, f'Статья «{title}» успешно создана!')
        return redirect('accounts:my_publications')


class EditPublicationView(View):
    def get(self, request, *args, **kwargs):
        publication = get_object_or_404(Article, pk=kwargs['pk'])

        context = {
            'publication': publication,
            'expertises': Expertise.objects.filter(is_active=True),
            'countries': Country.objects.filter(is_active=True),
            'types': PublicationType.objects.filter(is_active=True),
        }
        return render(request, 'auth/edit-publication.html', context=context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        publication = get_object_or_404(Article, pk=kwargs['pk'])

        if action == 'edit':
            title = (request.POST.get('title') or '').strip()
            image = request.FILES.get('image')
            short_text = (request.POST.get('short_text') or '').strip()
            text = (request.POST.get('text') or '').strip()
            slug = (request.POST.get('slug') or '').strip()
            order = (request.POST.get('order') or '').strip()
            by_subscription = bool(request.POST.get('by_subscription'))
            expertise_ids = request.POST.getlist('expertise')
            country_ids = request.POST.getlist('country')
            type_ids = request.POST.getlist('type')

            error__messages = []

            if not title:
                error__messages.append('Поле «Заголовок» обязательно к заполнению!')

            if not short_text:
                error__messages.append('Поле «Анонс» обязательно к заполнению!')

            if not text:
                error__messages.append('Поле «Текст» обязательно к заполнению!')

            if slug:
                base_slug = slug
                counter = 1
                while Article.objects.filter(slug=slug).exclude(pk=publication.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
            else:
                error__messages.append('Поле «Slug» обязательно к заполнению!')

            if order:
                try:
                    order = int(order)
                    if order < 1:
                        error__messages.append('Порядковый номер не может быть меньше нуля!')
                except ValueError:
                    error__messages.append('Ошибка с форматом поля «Порядковый номер»!')
            else:
                error__messages.append('Поле «Порядковый номер» обязательно к заполнению!')

            if error__messages:
                for error in error__messages:
                    messages.error(request, f'{error}')
                return redirect('accounts:edit_publication', pk=kwargs['pk'])

            publication.title = title
            publication.title_h1 = title
            publication.short_text = short_text
            publication.text = text
            publication.slug = slug
            publication.by_subscription = by_subscription or False
            publication.order = order
            publication.is_active = False

            publication.types.set(type_ids)
            publication.countries.set(country_ids)
            publication.expertises.set(expertise_ids)

            if image:
                # если есть старое изображение
                if publication.image:
                    try:
                        old_image_path = Path(publication.image.path)

                        # если файл существует и отличается от нового
                        if old_image_path.exists():
                            old_image_path.unlink()
                    except Exception:
                        pass

                publication.image = image

            publication.save()

            messages.error(request, f'Статья «{publication.title_h1}» успешно обновлена!')

        if action == 'delete':
            publication.delete()
            messages.error(request, f'Статья «{publication.title_h1}» успешно удалена!')

        return redirect('accounts:my_publications')
