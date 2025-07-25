from django.urls import path, include
from . import views


urlpatterns = [
    path('login/', views.LoginView.as_view(),name="login"),
    path('logout/', views.LogoutView.as_view(),name="logout"),
    path('profile/', views.ProfileView.as_view(),name="profile"),
    path('experiment/', include('experiment.urls')),
    path('dashboard/', views.DashboardView.as_view(), name="dashboard"),
]
