from uuid import uuid4

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail
from django.contrib import messages

from accounts.models import Profile, EmailVerificationToken
from content.models import Page, Application, Plain, Country, Expertise, PublicationType, Article


class HomePage(View):
    def get(self, request):
        return render(request, 'home.html')


class PageView(View):
    def get(self, request, *args, **kwargs):
        page = get_object_or_404(Page, slug=kwargs.get('slug'), is_active=True)

        context = {
            'page': page,
            'form_data': request.session.pop('form_data', {}),
        }

        if page.type == 'sb':
            context['plains'] = Plain.objects.filter(is_active=True)

        if page.type == 'register':
            if request.user.is_authenticated:
                return redirect('accounts:home')
            context['countries'] = Country.objects.filter(is_active=True)
            context['expertises'] = Expertise.objects.filter(is_active=True)

        if page.type == 'researches':
            context['countries'] = Country.objects.filter(is_active=True)
            context['expertises'] = Expertise.objects.filter(is_active=True)
            context['pub_types'] = PublicationType.objects.filter(is_active=True)

            articles = Article.objects.filter(is_active=True)

            query = request.GET.get('query')
            if query:
                articles = articles.filter(
                    Q(title__icontains=query) |
                    Q(short_text__icontains=query) |
                    Q(text__icontains=query)
                )

            pub_type = request.GET.get('publications_type')
            if pub_type:
                articles = articles.filter(types__id=pub_type)

            selected_countries = request.GET.getlist('countries')
            if selected_countries:
                articles = articles.filter(countries__id__in=selected_countries)

            selected_expertises = request.GET.getlist('expertises')
            if selected_expertises:
                articles = articles.filter(expertises__id__in=selected_expertises)

            articles = articles.distinct()

            paginator = Paginator(articles, 12)
            page_number = request.GET.get('page', 1)

            try:
                articles_page = paginator.page(page_number)
            except PageNotAnInteger:
                articles_page = paginator.page(1)
            except EmptyPage:
                articles_page = paginator.page(paginator.num_pages)

            context['articles'] = articles_page
            context['paginator'] = paginator

            context['selected_countries'] = list(map(str, selected_countries))
            context['selected_expertises'] = list(map(str, selected_expertises))

        if page.type == 'auth':
            if request.user.is_authenticated:
                return redirect('accounts:home')

        return render(request, 'page.html', context=context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'register':
            request.session['form_data'] = request.POST.dict()

            name = (request.POST.get('name') or '').strip()
            last_name = (request.POST.get('last_name') or '').strip()
            email = (request.POST.get('email') or '').strip()
            country = request.POST.get('country')
            expertise_ids = request.POST.getlist('expertise')
            description = request.POST.get('description')
            linkedin = request.POST.get('linkedin')

            error__messages = []

            if User.objects.filter(email=email).exists():
                error__messages.append('Пользователь с таким Email уже существует!')

            if not name:
                error__messages.append('Имя обязательно к заполнению!')

            if not last_name:
                error__messages.append('Фамилия обязательна к заполнению!')

            if email:
                if '@' not in email:
                    error__messages.append('E-mail некорректный!')
            else:
                error__messages.append('E-mail обязателен к заполнению!')

            if not country:
                error__messages.append('Необходимо выбрать страну!')

            if not expertise_ids:
                error__messages.append('Необходимо выбрать хотя бы одну сферу экспертизы!')

            if error__messages:
                for error in error__messages:
                    messages.error(request, f'{error}')
                return redirect('content:page', slug='stat-ekspertom')

            try:
                country_obj = Country.objects.get(id=country)
            except Country.DoesNotExist:
                messages.error(request, 'Выбранная страна не существует!')
                return redirect('content:page', slug='stat-ekspertom')

            try:
                password = f"{uuid4()}"

                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}-{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                profile = Profile.objects.create(
                    user=user,
                    name=name,
                    lastname=last_name,
                    country=country_obj,
                    bio=description,
                    linkedin=linkedin,
                )
                profile.expertises.set(expertise_ids)

                verification_token = EmailVerificationToken.objects.create(user=user)
                if settings.DEBUG:
                    domain = 'http://127.0.0.1:8000'
                else:
                    domain = f'{settings.PROTOCOL}/{settings.DOMAIN}'
                verification_link = f"{domain}{reverse('accounts:verify_email', kwargs={'token': verification_token.token})}"

                subject = 'Регистрация аккаунта'

                message_template = render_to_string('messages/success-register.html', {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'link': verification_link
                })

                send_mail(
                    subject,
                    message_template,
                    settings.EMAIL_HOST_USER,
                    [email],
                    html_message=message_template,
                    fail_silently=False
                )

                return redirect('content:page', slug='success-registration')
            except Exception as e:
                messages.error(request, f'Возникла ошибка при регистрации! {e}')
                return redirect('content:page', slug='stat-ekspertom')

        if action == 'auth':
            request.session['form_data'] = request.POST.dict()

            email = (request.POST.get('email') or '').strip()
            password = (request.POST.get('password') or '').strip()

            error__messages = []

            if email:
                if '@' not in email:
                    error__messages.append('E-mail некорректный!')
            else:
                error__messages.append('Необходимо ввести E-mail!')

            if not password:
                error__messages.append('Необходимо ввести пароль!')

            if not User.objects.filter(email=email).exists():
                error__messages.append('Пользователя с таким E-mail нет!')

            if error__messages:
                for error in error__messages:
                    messages.error(request, f'{error}')
                return redirect('content:page', slug='login')

            user = User.objects.get(email=email)

            if user.profile.status == 'deactivated':
                messages.error(request, 'Ваш аккаунт был деактивирован! Пожалуйста, обратитесь к администратору!')
                return redirect('content:page', slug='login')

            if user.profile.status == 'pending_email':
                messages.error(request, 'Пожалуйста, подтвердите аккаунт, пройдя по ссылке, отправленной на почту!')
                return redirect('content:page', slug='login')

            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if authenticated_user is not None:
                login(request, user)
                return redirect('accounts:home')
            else:
                messages.success(request, 'Пароль неверный!')
                return redirect('content:page', slug='login')

        if action == 'reset_password':
            email = (request.POST.get('email') or '').strip()

            error__messages = []

            if email:
                if '@' not in email:
                    error__messages.append('E-mail некорректный!')
            else:
                error__messages.append('Необходимо ввести E-mail!')

            if not User.objects.filter(email=email).exists():
                error__messages.append('Пользователя с таким E-mail нет!')

            if error__messages:
                for error in error__messages:
                    messages.error(request, f'{error}')
                return redirect('content:page', slug='login')

            try:
                user = User.objects.get(email=email)
                new_password = f'{uuid4()}'
                user.set_password(new_password)
                user.save()

                subject = 'Восстановление пароля на сайте'

                if settings.DEBUG:
                    domain = 'http://127.0.0.1:8000'
                else:
                    domain = f'{settings.PROTOCOL}/{settings.DOMAIN}'
                link = f"{domain}{reverse('content:page', kwargs={'slug': 'login'})}"

                message_template = render_to_string('messages/new-password.html', {
                    'name': user.profile.name,
                    'email': user.email,
                    'subject': subject,
                    'link': link,
                    'password': new_password
                })

                send_mail(
                    subject,
                    message_template,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    html_message=message_template,
                    fail_silently=False
                )
                messages.error(request, 'Новый пароль отправлен вам на почту!')
            except:
                messages.error(request, 'Возникла ошибка при сбросе пароля!')

            return redirect('content:page', slug='login')


class ApplicationView(View):
    def post(self, request):

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        message = request.POST.get('message', '—')
        post = request.POST.get('post', '—')
        subject = request.POST.get('subject')

        message_template = render_to_string('messages/message.html', {
            'name': name,
            'phone': phone,
            'email': email,
            'message': message,
            'post': post,
            'subject': subject
        })

        try:
            send_mail(
                subject,
                message_template,
                settings.EMAIL_HOST_USER,
                ['info@steppeintel.kz'],
                html_message=message,
                fail_silently=False
            )
            new_application = Application.objects.create(
                subject=subject,
                name=name,
                phone=phone,
                email=email,
                message=message,
                post=post,
            )
        except Exception:
            pass

        messages.success(request, 'Ваша заявка успешно отправлена!')
        return redirect(request.META.get('HTTP_REFERER', '/'))


class ArticlePage(View):
    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        articles = Article.objects.filter(is_active=True).exclude(pk=article.id)[:3]

        if article.by_subscription:
            if request.user != article.author:
                messages.warning(request, 'Данный материал доступен только по подписке!')
                base_url = reverse('content:page', kwargs={'slug': 'steppe-brief'})
                return redirect(f'{base_url}#trials')

        context = {
            'article': article,
            'articles': articles
        }

        return render(request, 'article.html', context=context)
