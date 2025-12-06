from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .fields import ColorField, hex_to_rgb
import re


class LEDContent(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.TimeField(null=True, blank=True, verbose_name="Frame1", help_text="Daily start time (hh:mm)")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Frame0", help_text="Daily end time (hh:mm)")
    checksum = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    is_test = models.BooleanField(default=False, help_text="Mark as test content")

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other LEDContent instances
            LEDContent.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        if self.is_test:
            # Unmark all other LEDContent instances as test
            LEDContent.objects.filter(is_test=True).exclude(pk=self.pk).update(is_test=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentSession(models.Model):
    led_content = models.ForeignKey(LEDContent, related_name='sessions', on_delete=models.CASCADE)
    session_order = models.PositiveIntegerField()
    delay = models.PositiveIntegerField(default=100)  # Animation delay in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(blank=True, null=True, help_text="Optional: Start date (YYYY-MM-DD)")
    start_time = models.TimeField(blank=True, null=True, help_text="Optional: Start time (hh:mm)")
    end_date = models.DateField(blank=True, null=True, help_text="Optional: End date (YYYY-MM-DD)")
    end_time = models.TimeField(blank=True, null=True, help_text="Optional: End time (hh:mm)")

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


class Image(models.Model):
    """Master list of images stored in LED hardware firmware"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Image identifier (a-z, A-Z, 0-9, _, -)"
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        """Validate image name format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.name):
            raise ValidationError({
                'name': 'Image name can only contain letters, numbers, underscore and hyphen'
            })

    def __str__(self):
        return f"{self.name}" + (f" ({self.description})" if self.description else "")


class SessionAnimation(models.Model):
    """Animation configuration for a ContentSession"""
    content_session = models.OneToOneField(
        ContentSession,
        related_name='animation',
        on_delete=models.CASCADE
    )
    loop_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Loop Count",
        help_text="Number of times to display the animation"
    )
    time_between_images = models.PositiveIntegerField(
        default=100,
        verbose_name="Time Between Images (ms)",
        help_text="Delay between image changes in milliseconds"
    )
    image_names = models.CharField(
        max_length=500,
        verbose_name="Image Names",
        help_text="Comma-separated image names (e.g., image1,image2,image3)",
        blank=True
    )

    class Meta:
        verbose_name = "Session Animation"
        verbose_name_plural = "Session Animations"

    def clean(self):
        """Validate animation configuration"""
        errors = {}

        # Parse and validate image names
        if not self.image_names or not self.image_names.strip():
            errors['image_names'] = 'At least one image name is required'
        else:
            # Split and clean image names
            names = [name.strip() for name in self.image_names.split(',')]
            names = [name for name in names if name]  # Remove empty strings

            if not names:
                errors['image_names'] = 'At least one valid image name is required'
            else:
                # Validate each image name format
                for name in names:
                    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
                        errors['image_names'] = f'Invalid image name "{name}". Only letters, numbers, underscore and hyphen allowed'
                        break

                # Check if all images exist in database
                if 'image_names' not in errors:
                    existing_images = set(Image.objects.filter(name__in=names).values_list('name', flat=True))
                    missing_images = set(names) - existing_images
                    if missing_images:
                        errors['image_names'] = f'Images not found in database: {", ".join(sorted(missing_images))}'

        if errors:
            raise ValidationError(errors)

    def get_image_list(self):
        """Return list of cleaned image names"""
        if not self.image_names:
            return []
        return [name.strip() for name in self.image_names.split(',') if name.strip()]

    @property
    def image_count(self):
        """Return number of images in animation"""
        return len(self.get_image_list())

    def __str__(self):
        return f"{self.content_session} - Animation ({self.image_count} images)"
