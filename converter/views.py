from email import header
from django.shortcuts import render, redirect
from django.conf import settings
import os
from .utils import convert_with_cow, get_csv_headers 
from .metadata import update_metadata

import logging
from .engine import Engine
import csv
logger = logging.getLogger(__name__)


def convert_screen_view(request):
    preview_rows = []
    full_table = False

    # The uploaded CSV path should be passed via session or passed in request.GET
    csv_path = request.session.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        return render(request, "converter/error.html", {"message": "CSV file not found"})

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        all_rows = list(reader)
        headers = all_rows[0]
        data_rows = all_rows[1:]

        if request.GET.get("full") == "true":
            preview_rows = data_rows
            full_table = True
        else:
            preview_rows = data_rows[:20]

    return render(request, "converter/convert_screen.html", {
        "headers": headers,
        "rows": preview_rows,
        "full_table": full_table
    })


def welcome_view(request):
    """
    Main function that renders the starting page on the website. 
    It also stores the uploaded file and creates the metadata from it.
    Starts the vocabulary recommendation process.
    """

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
            
            # Initialize the engine
            engine = Engine(headers)

            sorted_vocabs, best_match_index, vocab_coverage_score, all_matches = engine.run_lov_requests()

            # Debugging code
            # print("==============================================")
            # logger.info(f"Vocab combiscore: {sorted_vocabs}")
            # print("==============================================")
            # logger.info(f"Vocab Coverage score: {vocab_coverage_score}")
            # print("==============================================")
            # logger.info(f"Final Matches: {best_match_index}")
            # print("==============================================")
            # logger.info(f"All matches: {all_matches}")

            logger.info(f"Best match for personID: {all_matches['personID'][0]}")

            #logger.info
            update_metadata(metadata_file_path, headers, all_matches, best_match_index, 'Homogenous', '')

            request.session['csv_path'] = csv_path

            # Redirect to converter screen
            return redirect('convert_screen')

    return render(request, 'converter/welcome.html', {
        'file_name': file_name,
        'metadata_generated': bool(metadata_file_path),
        'metadata_path': metadata_file_path,
    })
