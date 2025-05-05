import os
import cv2
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.http import FileResponse, Http404
from .forms import *
from .models import *

# Create your views here.
def signup_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()  # This handles creating the user and hashing the password
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserForm()
    return render(request, 'registration/sign_up.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('landing_page')

def landing_page(request):
    return render(request, "real_time_object_tracking/landing_page.html")

# def home(request):
#     form = VideoUploadForm()
#     if request.method == 'POST':
#         form = VideoUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             video_file = form.cleaned_data['video']
#             video_path = f"/tmp/{video_file.name}"
#             request.session['video_path'] = video_path
#             cap = cv2.VideoCapture(video_path)
#             ret, frame = cap.read()
#             cap.release()
#             if ret:
#                 first_frame_path = os.path.join(settings.MEDIA_ROOT, 'first_frame.jpg')
#                 cv2.imwrite(first_frame_path, frame)
#                 request.session['video_path'] = video_path
#                 request.session['first_frame_url'] = os.path.join(settings.MEDIA_URL, 'first_frame.jpg')
            
#             return redirect('home')
#     else:
#         form = VideoUploadForm()
#     first_frame_url = request.session.get('first_frame_url', None)
#     return render(request, 'real_time_object_tracking/home.html', {'form': form, 'first_frame_url': first_frame_url})

@login_required
def home(request):
    if request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.cleaned_data["video"]
            path = os.path.join("real_time_object_tracking", "media", "uploaded_videos", video.name)
            with open(path, "wb+") as f:
                for chunk in video.chunks():
                    f.write(chunk)
                    
            request.session["video_path"] = path
            
            # Scale lineY from canvas to actual video height
            canvas_height = int(request.POST.get("canvasHeight", 480))  # Default canvas height
            raw_line_y = float(request.POST.get("lineY", 300))
            print(f"raw_line_y: {raw_line_y}")
            cap = cv2.VideoCapture(path)
            video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"video height: {video_height}")
            cap.release()
            
            # Convert canvas Y to actual video Y
            actual_line_y = int((raw_line_y / canvas_height) * video_height)
            request.session["line_y"] = actual_line_y
            print(f"Scaled line_y: {actual_line_y} from raw {raw_line_y} and canvasHeight {canvas_height}")

            return JsonResponse({"status": "uploaded"})
    else:
        form = VideoUploadForm()
    return render(request, "real_time_object_tracking/home.html", {"form": form})

def save_csv(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'Output_CSVs', 'results.csv')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='results.csv')
    else:
        raise Http404("CSV not found")