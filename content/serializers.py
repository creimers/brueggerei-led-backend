from rest_framework import serializers
from .models import LEDContent, ContentSession, SessionText, SessionLine


class SessionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionLine
        fields = ['start_index', 'color']
    
    def to_representation(self, instance):
        return {
            'startIndex': instance.start_index,
            'color': list(instance.color_rgb)
        }


class SessionTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionText
        fields = ['start_index', 'content', 'color']
    
    def to_representation(self, instance):
        return {
            'startIndex': instance.start_index,
            'content': instance.content,
            'color': list(instance.color_rgb)
        }


class ContentSessionSerializer(serializers.ModelSerializer):
    text = SessionTextSerializer(read_only=True)
    lines = SessionLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = ContentSession
        fields = ['text', 'lines', 'delay']


class LEDContentSerializer(serializers.ModelSerializer):
    sessions = ContentSessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = LEDContent
        fields = ['sessions', 'checksum']
    
    def to_representation(self, instance):
        return {
            'sessions': [session for session in ContentSessionSerializer(instance.sessions.all(), many=True).data],
            'checksum': instance.checksum
        }