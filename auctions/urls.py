from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # categories
    path("<str:category_slug>", views.category_listings, name="category_listings"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
]
