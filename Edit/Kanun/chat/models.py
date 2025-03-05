from django.db import models
from django.conf import settings
import uuid

class ChatUsageLog(models.Model):
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)       
    query = models.TextField()
    response = models.TextField()
    token_usage = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    model = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.timestamp} - {self.model} - {self.token_usage} tokens - Session: {self.session_id}"

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    chat_history = models.JSONField(default=list)

    def __str__(self):
        return f"Conversation {self.id} - User {self.user.username}"

    class Meta:
        ordering = ["-updated_at"]

class GeneratedImage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    image_url = models.URLField()
    image_file = models.ImageField(upload_to="generated_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image by {self.user.username} - {self.prompt}"
