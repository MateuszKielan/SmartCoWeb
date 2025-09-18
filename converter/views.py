from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)
# Create your views here.
def welcome_view(request):
    file_name = None

    if request.method == 'POST':
        uploaded_file = request.FILES.get('csv_file')
        api_endpoint = request.POST.get('api_endpoint')

        if uploaded_file:
            file_name = uploaded_file.name
            print(uploaded_file)
            #logger.debug(uploaded_file)
            # TODO: handle the uploaded file later

    return render(request, 'converter/welcome.html', {
        'file_name': file_name
    })