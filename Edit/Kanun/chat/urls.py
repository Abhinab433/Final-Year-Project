from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from .views import generate_image, download_image

urlpatterns = [
    path("", views.chat_list_view, name="chat_list"),  # List all conversations
    path("chat/new/", views.chat_create_view, name="chat_create"),  # Create a new chat
    path('chat/<int:conversation_id>/', views.chat_view, name='chat'), # View an individual conversation
    path("dashboard/", views.dashboard_view, name="dashboard"),  # Dashboard for usage statistics
    path('image/generate/', views.generate_image, name='generate_image'),
    path("download/<int:image_id>/", download_image, name="download_image"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)