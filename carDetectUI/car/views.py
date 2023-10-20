from django.shortcuts import render
import io
from PIL import Image as im
import torch
from django.shortcuts import render
from django.views.generic.edit import CreateView
from .models import ImageModel
from .forms import ImageUploadForm
from django.conf import settings
import os
import numpy as np
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.http import HttpResponseRedirect 
from django.urls import reverse
import json
import uuid
from datetime import datetime
from django.views.generic.list import ListView

class UploadImage(CreateView, ListView):
    model = ImageModel
    template_name = 'car/car_detect.html'
    fields = ["image"]
    context_object_name = 'car_list' 
   
    def get(self, request, *args, **kwargs):
        # GET 요청을 처리할 때 이미지 목록을 초기화하고 페이지네이션을 설정
        result_images = ImageModel.objects.exclude(result_image='').order_by('-id')
       

       
        paginator = Paginator(result_images, 6)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if 'my_context' in request.session:
            context = request.session['my_context']
            context['page_obj'] = page_obj
        
        # 이제 context_data를 사용할 수 있습니다
       
        else:
            # 세션에 context가 없을 때의 처리
    
            context = {
                'form': ImageUploadForm(),  # 이미지 업로드 폼
                'result_images': result_images,  # 초기 이미지 목록
                'page_obj': page_obj,  # 페이지네이션

            }
        return render(request, 'car/car_detect.html', context)

    def post(self, request, *args, **kwargs):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = request.FILES.get('image')
            img_instance = ImageModel(
                image=img
            )
            img_instance.save()

            uploaded_img_qs = ImageModel.objects.filter().last()
            img_bytes = uploaded_img_qs.image.read()
            img = im.open(io.BytesIO(img_bytes))

            # yolov5모델로드
           
            model = torch.hub.load("yolov5", "best", source='local')

            # 객체 감지
            results = model(img, size=640)
            results.render()
            
            detected_classes = [results.names[int(pred[5])] for pred in results.pred[0]]
        #   confidences = [pred[4] * 100 for pred in results.pred[0]]

            # detected_classes에서 클래스 별로 카운트를 수행
            class_counts = {}
            for detected_class in detected_classes:
                if detected_class in class_counts:
                    class_counts[detected_class] += 1
                else:
                    class_counts[detected_class] = 1

            # 클래스와 해당 클래스의 카운트 출력
            for class_name, count in class_counts.items():
                print(f"Class: {class_name}, Count: {count}")

            # 결과이미지 저장 #########3db연동, 수정해야됨
            result_img = im.fromarray(np.uint8(results.render()[0]))
            result_img.save(os.path.join("static", 'img', 'image0.jpg'), format="JPEG")

            # 클래스 정보 및 개수 저장
            img_instance.detected_classes = detected_classes
            img_instance.class_counts = class_counts
            img_instance.save()
           

#############################DB에 웹서버에 저장된 파일경로 저장.

            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4().hex)
            file_extension = '.jpg'  # 파일 확장자 (원하는 확장자로 변경)
            file_name = f'{current_time}_{unique_id}{file_extension}'

            # 최종 파일 경로
            
            result_img.save(os.path.join("static", "results", file_name))

            
            img_instance.result_image = os.path.join(f"/static/results/{file_name}")
            img_instance.save()
###################################3


            inference_img = f"/static/results/{file_name}"
               # ImageModel의 모든 인스턴스 가져오기
         #   image_models = ImageModel.objects.all()

            result_images = ImageModel.objects.exclude(result_image='')
            result_images = list(result_images.values()) 

         #   result_images = [image.result_image for image in image_models]
            
        
            
            context = {
              #  "form": form,
                "inference_img": inference_img,
              #  "detected_class": detected_classes,    
              #  "confidences" :  confidences,
                'result_images': result_images,
                "class_counts": class_counts,
             #   'page_obj' : page_obj,
            }
            request.session['my_context'] = context

          #  form = ImageUploadForm()
           # return render(request, 'car/car_detect.html', context)
            return redirect('car:carDetect')
        else:      
            form = ImageUploadForm()
            context = {
                "form": form
            }
            return render(request, 'car/car_detect.html', context)



import cv2
from .models import ImageModel, VideoModel
from .forms import ImageUploadForm, VideoUploadForm
import subprocess
from django.views.generic.edit import FormView

def detect_objects(video_path):
    model = torch.hub.load("yolov5", "yolov5s", source ='local')
    model.eval()

    cap = cv2.VideoCapture(video_path)
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        #객체감지
        results = model(frame)
        detected_image = results.render()[0]

        #프레임별로 객체 클래스 및 갯수 출력
        class_names = results.names
        class_counts = {}
        for pred in results.pred[0]:
            class_index = int(pred[5])
            class_name = class_names[class_index]
            if class_name in class_counts:
                class_counts[class_name] += 1
            else:
                class_counts[class_name] = 1
        print("카운트:", class_counts)


        frames.append(detected_image)

    cap.release()
   
    return frames

class VideoUploadView(CreateView):
    model = VideoModel
    template_name = 'car/upload_video.html'
    form_class = VideoUploadForm

    def form_valid(self, form):
        video_instance = form.save()

        # 객체 감지
        frames = detect_objects(video_instance.video.path)

        # 결과 영상 저장
        output_video_path = "static/videos/result_video.mp4"  # 수정 필요
        out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))

        for frame in frames:
            out.write(frame)

        out.release()

        # 결과 영상 경로 저장
        video_instance.result_video = output_video_path
        video_instance.save()

        return HttpResponseRedirect(reverse('car:carDetect'))