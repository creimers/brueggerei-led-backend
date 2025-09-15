from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .fields import ColorField, hex_to_rgb


class LEDContent(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    start_timestamp = models.DateTimeField(null=True, blank=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other LEDContent instances
            LEDContent.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentSession(models.Model):
    led_content = models.ForeignKey(LEDContent, related_name='sessions', on_delete=models.CASCADE)
    session_order = models.PositiveIntegerField()
    delay = models.PositiveIntegerField(default=100)  # Animation delay in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['session_order']
        unique_together = ['led_content', 'session_order']
    
    def __str__(self):
        return f"{self.led_content.title} - Session {self.session_order}"


class SessionText(models.Model):
    content_session = models.OneToOneField(ContentSession, related_name='text', on_delete=models.CASCADE)
    start_index = models.PositiveIntegerField()  # startIndex from API
    content = models.TextField()  # text content
    color = ColorField(default='#00ff00')  # Default green color
    
    @property
    def color_rgb(self):
        """Return color as RGB tuple for API serialization"""
        return hex_to_rgb(self.color)
    
    def __str__(self):
        return f"{self.content_session} - Text: {self.content[:30]}"


class SessionLine(models.Model):
    content_session = models.ForeignKey(ContentSession, related_name='lines', on_delete=models.CASCADE)
    start_index = models.PositiveIntegerField()  # startIndex from API
    color = ColorField(default='#ffff00')  # Default yellow color
    
    class Meta:
        unique_together = ['content_session', 'start_index']
    
    @property
    def color_rgb(self):
        """Return color as RGB tuple for API serialization"""
        return hex_to_rgb(self.color)
    
    def __str__(self):
        return f"{self.content_session} - Line {self.start_index}"
