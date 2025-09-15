from django.urls import path
from .views import LEDContentAPIView, LEDContentDefView

urlpatterns = [
    path('api/content/', LEDContentAPIView.as_view(), name='led-content-api'),
    path('api/content.txt', LEDContentDefView.as_view(), name='led-content-def'),
]