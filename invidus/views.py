from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import os
import mimetypes

# Create your views here.
def home(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)
        
        # Get the file type
        file_type, _ = mimetypes.guess_type(file.name)
        if file_type is None:
            file_type = 'application/octet-stream'
            
        return JsonResponse({
            'status': 'success',
            'file_url': file_url,
            'file_name': file.name,
            'file_type': file_type
        })
    return render(request, 'home.html')