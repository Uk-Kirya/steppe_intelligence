from django.urls import path

from .views import HomePage, PageView, ApplicationView, ArticlePage

app_name = 'content'

urlpatterns = [
    path('', HomePage.as_view(), name='home'),
    path('send-email/', ApplicationView.as_view(), name='application'),
    path('<slug:slug>/', PageView.as_view(), name='page'),
    path('issledovaniya/<slug:slug>/', ArticlePage.as_view(), name='article_detail'),
]
