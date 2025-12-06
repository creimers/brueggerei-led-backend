import nested_admin
from django.contrib import admin
from django import forms
from .models import LEDContent, ContentSession, SessionText, SessionLine, Image, SessionAnimation


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    fields = ['name', 'description']


class SessionAnimationForm(forms.ModelForm):
    """Custom form for SessionAnimation with image selection"""

    # Create a custom field for selecting images
    selected_images = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select images to include in animation"
    )

    class Meta:
        model = SessionAnimation
        fields = ['loop_count', 'time_between_images', 'selected_images', 'image_names']
        widgets = {
            'image_names': forms.TextInput(attrs={'size': 60})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate choices from Image table
        self.fields['selected_images'].choices = [
            (img.name, f"{img.name}" + (f" - {img.description}" if img.description else ""))
            for img in Image.objects.all()
        ]

        # Pre-populate selected_images if editing existing animation
        if self.instance and self.instance.pk and self.instance.image_names:
            self.fields['selected_images'].initial = self.instance.get_image_list()

        # Make image_names readonly (will be auto-populated from checkboxes)
        # self.fields['image_names'].widget.attrs['readonly'] = True
        self.fields['image_names'].help_text = 'Auto-generated from selected images. You can also manually edit the order here.'

    def clean(self):
        cleaned_data = super().clean()
        selected_images = cleaned_data.get('selected_images', [])

        # Convert selected images to comma-separated string
        if selected_images:
            cleaned_data['image_names'] = ','.join(selected_images)

        return cleaned_data


class SessionLineInline(nested_admin.NestedTabularInline):
    model = SessionLine
    extra = 0
    max_num = 13
    fields = ['start_index', 'color']


class SessionTextInline(nested_admin.NestedStackedInline):
    model = SessionText
    fields = ['start_index', 'content', 'color']
    max_num = 1
    min_num = 0
    extra = 0


class SessionAnimationInline(nested_admin.NestedStackedInline):
    model = SessionAnimation
    form = SessionAnimationForm
    fields = ['loop_count', 'time_between_images', 'selected_images', 'image_names']
    max_num = 1
    min_num = 0
    extra = 0


class ContentSessionInline(nested_admin.NestedStackedInline):
    model = ContentSession
    extra = 1
    fields = ['session_order', 'start_date', 'start_time', 'end_date', 'end_time', 'delay']
    inlines = [SessionTextInline, SessionAnimationInline, SessionLineInline]


@admin.register(LEDContent)
class LEDContentAdmin(nested_admin.NestedModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active', 'is_test']
    list_filter = ['is_active', 'is_test', 'created_at', 'created_by']
    search_fields = ['title']
    readonly_fields = ['created_at', 'checksum']
    fields = ['title', 'start_time', 'end_time', 'is_active', 'is_test']
    inlines = [ContentSessionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


