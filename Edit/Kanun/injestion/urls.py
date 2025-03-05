from django.urls import path
from .views import upload_pdf_view

urlpatterns = [
    path("", upload_pdf_view, name="upload_pdf"),  # Use the correct name here
]
