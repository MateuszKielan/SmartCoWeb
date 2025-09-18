from email import header
from django.shortcuts import render
from django.conf import settings
import os
from .utils import convert_with_cow, get_csv_headers 
import logging

logger = logging.getLogger(__name__)

def welcome_view(request):
    file_name = None
    metadata_file_path = None

    if request.method == 'POST':
        uploaded_file = request.FILES.get('csv_file')

        if uploaded_file:
            file_name = uploaded_file.name

            # Save uploaded file to server
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            csv_path = os.path.join(upload_dir, file_name)

            with open(csv_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            logger.info(f"[UPLOAD] File saved to: {csv_path}")

            # Reuse method to generate metadata
            metadata_path_obj = convert_with_cow(csv_path)

            if metadata_path_obj:
                metadata_file_path = str(metadata_path_obj)

            headers = get_csv_headers(csv_path)
            logger.info(f'[UPLOAD] Retrieved headers {headers}')

    return render(request, 'converter/welcome.html', {
        'file_name': file_name,
        'metadata_generated': bool(metadata_file_path),
        'metadata_path': metadata_file_path,
    })
