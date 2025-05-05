from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name="landing_page"),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),
    path('home/', views.home, name="home"),
    path('download_csv/', views.save_csv, name="save_csv")
]
