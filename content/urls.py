from django.urls import path
from .views import LEDContentAPIView, LEDContentDefView, LEDContentDefTestView

urlpatterns = [
    path('api/content/', LEDContentAPIView.as_view(), name='led-content-api'),
    path('api/content.txt', LEDContentDefView.as_view(), name='led-content-def'),
    path('api/test.txt', LEDContentDefTestView.as_view(), name='led-content-def-test'),
]