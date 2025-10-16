from rest_framework import generics
from rest_framework.response import Response
from django.http import HttpResponse
from .models import LEDContent
from .serializers import LEDContentSerializer


class LEDContentAPIView(generics.RetrieveAPIView):
    queryset = LEDContent.objects.filter(is_active=True)
    serializer_class = LEDContentSerializer
    
    def get_object(self):
        # Return the most recent active LED content
        return LEDContent.objects.filter(is_active=True).order_by('-created_at').first()
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({'sessions': [], 'checksum': ''})
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class LEDContentDefView(generics.GenericAPIView):
    queryset = LEDContent.objects.filter(is_active=True)
    
    def get_object(self):
        # Return the most recent active LED content
        return LEDContent.objects.filter(is_active=True).order_by('-created_at').first()
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return HttpResponse('', content_type='text/plain; charset=utf-8')

        def_content = self.generate_def_format(instance)

        return HttpResponse(def_content, content_type='text/plain; charset=utf-8')
    
    def generate_def_format(self, led_content):
        """Generate the .def format text from LEDContent instance"""
        lines = []

        # Add global Frame1 (daily start) if configured
        if led_content.start_time:
            lines.append(f'Frame1={led_content.start_time.strftime("%H:%M")}')

        # Add global Frame0 (daily end) if configured
        if led_content.end_time:
            lines.append(f'Frame0={led_content.end_time.strftime("%H:%M")}')

        sessions = led_content.sessions.all().order_by('session_order')

        for i, session in enumerate(sessions):
            # Add Start= line if date or time is specified
            start_parts = []
            if session.start_date:
                start_parts.append(session.start_date.strftime('%Y-%m-%d'))
            if session.start_time:
                start_parts.append(session.start_time.strftime('%H:%M'))
            if start_parts:
                lines.append(f'Start={" ".join(start_parts)}')

            # Add End= line if date or time is specified
            end_parts = []
            if session.end_date:
                end_parts.append(session.end_date.strftime('%Y-%m-%d'))
            if session.end_time:
                end_parts.append(session.end_time.strftime('%H:%M'))
            if end_parts:
                lines.append(f'End={" ".join(end_parts)}')

            # Add lines for this session
            for line in session.lines.all().order_by('start_index'):
                r, g, b = line.color_rgb
                lines.append(f'Line={line.start_index},{r},{g},{b}')

            # Add text configuration
            if hasattr(session, 'text') and session.text:
                text = session.text
                lines.append(f'Text={text.start_index},{text.content}')

                # Add color configuration
                r, g, b = text.color_rgb
                lines.append(f'Color={r},{g},{b}')

            # Add delay
            lines.append(f'Delay={session.delay}')

            # Add 'Next' separator (except for the last session)
            if i < len(sessions) - 1:
                lines.append('Next')

        return '\n'.join(lines)


class LEDContentDefTestView(LEDContentDefView):
    """View for serving test LED content in .def format"""

    def get_object(self):
        # Return the test LED content
        return LEDContent.objects.filter(is_test=True).first()
