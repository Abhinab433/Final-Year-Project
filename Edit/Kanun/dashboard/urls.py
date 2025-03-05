from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard'),
    path('view_users/', views.view_users, name='view_users'),  # Read-Only View
    path('manage_users/', views.manage_users, name='manage_users'),  # CRUD View
    path('manage_users/add/', views.add_user, name='add_user'),
    path('manage_users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('manage_users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('news/', views.news, name='news'),
    path('chat_logs/', views.user_chat_logs, name='user_chat_logs'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)