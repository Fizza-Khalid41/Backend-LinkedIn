from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('profile/', views.get_profile),
    path('profile/update/', views.update_profile), 
    path('posts/', views.get_posts),
    path('posts/create/', views.create_post),
    path('posts/<int:post_id>/like/', views.like_post),
    path('posts/<int:post_id>/comment/', views.add_comment),
  
  
]