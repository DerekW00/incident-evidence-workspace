from django.urls import path
from django.contrib.auth import views as auth
from investigations import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "login/",
        auth.LoginView.as_view(template_name="investigations/login.html"),
        name="login",
    ),
    path("logout/", auth.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("incidents/<int:pk>/", views.incident, name="incident"),
    path("runs/<int:pk>/", views.detail, name="run"),
    path("runs/<int:pk>/events/", views.events, name="events"),
    path("runs/<int:pk>/cancel/", views.cancel_view, name="cancel"),
    path("runs/<int:pk>/review/", views.review, name="review"),
    path("runs/<int:pk>/brief/", views.brief, name="brief"),
]
