import nested_admin
from django.contrib import admin
from .models import LEDContent, ContentSession, SessionText, SessionLine


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


class ContentSessionInline(nested_admin.NestedStackedInline):
    model = ContentSession
    extra = 1
    fields = ['session_order', 'delay']
    inlines = [SessionTextInline, SessionLineInline]


@admin.register(LEDContent)
class LEDContentAdmin(nested_admin.NestedModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['title']
    readonly_fields = ['created_at', 'checksum']
    fields = ['title', 'start_timestamp', 'end_timestamp', 'is_active']
    inlines = [ContentSessionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


