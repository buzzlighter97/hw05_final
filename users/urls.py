from django.urls import path
from .views import SignUp


urlpatterns = [
    # path() для страницы регистрации нового пользователя
    # её полный адрес будет auth/signup/, но префикс auth/ обрабатывется в головном urls.py
    path("signup/", SignUp.as_view(), name="signup")
]