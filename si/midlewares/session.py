from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SessionExpiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Проверяем, что пользователь аутентифицирован
        if request.user.is_authenticated:
            # Проверяем, что текущий путь не является страницей аутентификации
            if not request.path.startswith(reverse('content:home')):
                # Проверяем, что сессия истекла
                if not request.session.get_expiry_age():
                    # Перенаправляем на страницу аутентификации
                    return redirect(reverse('content:home') + '?next=' + request.path)
