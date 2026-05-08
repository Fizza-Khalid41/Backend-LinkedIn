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
    path('posts/<int:post_id>/comments/', views.get_comments),
    path('users/', views.get_users),
    path('connections/', views.get_connections),
    path('connections/pending/', views.get_pending_requests),
    path('connections/send/<int:user_id>/', views.send_request),
    path('connections/accept/<int:user_id>/', views.accept_request),
    path('connections/reject/<int:user_id>/', views.reject_request),
    path('jobs/', views.get_jobs),
    path('conversations/', views.conversations, name='conversations'),
    path('messages/<int:conversation_id>/', views.get_messages, name='get-messages'),
    path('send-message/', views.send_message, name='send-message'),
]

