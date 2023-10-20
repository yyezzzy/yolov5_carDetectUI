from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'car'

urlpatterns = [
     path('', views.UploadImage.as_view(), name='carDetect'),
     path('upload_video/', views.VideoUploadView.as_view(), name='uploadVideo'),
      
]
