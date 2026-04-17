from django.urls import path

from content.views import Country, Expertise

from .views import ProfilePage, VerifyEmailView, MyPublicationsView, MyPlainView, LogoutView

app_name = 'accounts'

urlpatterns = [
    path('', ProfilePage.as_view(), name='home'),
    path('my-publications/', MyPublicationsView.as_view(), name='my_publications'),
    path('my-plain/', MyPlainView.as_view(), name='my_plain'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
]
