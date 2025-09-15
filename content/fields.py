import re
from django import forms
from django.db import models
from django.core.exceptions import ValidationError


class ColorWidget(forms.TextInput):
    input_type = 'color'
    
    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        # Convert RGB tuple/list to hex
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return '#{:02x}{:02x}{:02x}'.format(*value)
        return value


class ColorField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 7)
        kwargs.setdefault('default', '#00ff00')  # Default green color
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['widget'] = ColorWidget
        return super().formfield(**kwargs)

    def clean(self, value, model_instance):
        value = super().clean(value, model_instance)
        if value:
            # Validate hex color format
            if not re.match(r'^#[0-9a-fA-F]{6}$', value):
                raise ValidationError('Color must be in format #RRGGBB')
        return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str):
            return value
        # Handle RGB tuple/list conversion
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return '#{:02x}{:02x}{:02x}'.format(*value)
        return str(value)

    def get_prep_value(self, value):
        return self.to_python(value)


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    if not hex_color or not hex_color.startswith('#'):
        return (0, 255, 0)  # Default green
    
    hex_color = hex_color[1:]  # Remove #
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 255, 0)  # Default green


def rgb_to_hex(r, g, b):
    """Convert RGB values to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, r)),
        max(0, min(255, g)), 
        max(0, min(255, b))
    )