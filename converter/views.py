# DONT FORGET TO SORT THE IMPORTS PLS 
from re import X
from turtle import update
from django.shortcuts import render, redirect
from django.conf import settings
import os
import json
from .utils import convert_with_cow, get_csv_headers, convert_json_to_nquads 
from .metadata import update_metadata, insert_instance
from pathlib import Path
import logging
from .engine import Engine
import csv
from django.http import JsonResponse



logger = logging.getLogger(__name__)


def convert_to_nquads_view(request):
    """a
    This function converts the JSON metadata file to N-Quads
    """
    if request.method == "POST":
        csv_path_str = request.session.get('csv_path')

        if not csv_path_str:
            return JsonResponse({"status": "error", "message": "No CSV file found in session."}, status=400)

        csv_path = Path(csv_path_str)

        try:
            convert_json_to_nquads(csv_path)
            return JsonResponse({"status": "success", "message": "Converted to N-Quads successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def replace_all(request):
    """
    Represents functionality of "Replace All" button
    Call the update_metadata function to overwrite the metadata file with best matches
    """
    if request.method == "POST":
        
        update_metadata(     
            request.session.get('metadata_file_path', ''), 
            request.session.get('headers', []),
            request.session.get('all_matches', {}),
            request.session.get('best_match_index', 0),
            request.session.get('request_type', 'Homogenous'),
            request.session.get('custom_endpoint', '')
        )
        
    return redirect('convert_screen')
        #return JsonResponse({"status": "success", "message": "The button has been clicked"})


def set_request_type(request, request_type):
    """
    Function that changes the request type mode in the session based on which button the user pressed.
    """
    if request.method == "POST":
        request.session['request_type'] = request_type
        logger.info(f"Request mode change detected: {request.session['request_type']}")

    return redirect('convert_screen')


# -------------------------Converter Screen----------------------------
# Responsible for the rendering of the page and passing the vocabulary recommender results to HTML forms
# Loads the full dataset into the HTML table 
# Loads the converted JSON file and passes it to the HTML template
# ---------------------------------------------------------------------

def convert_screen_view(request):
    preview_rows = []
    full_table = False
    json_content = ""

    # The uploaded CSV path should be passed via session or passed in request.GET
    csv_path = request.session.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        return render(request, "converter/error.html", {"message": "CSV file not found"})


    # Open and process the csv file
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        all_rows = list(reader)
        headers = all_rows[0]
        data_rows = all_rows[1:]

        # full and preview rows for the converter screen      
        full_table = data_rows
        preview_rows = data_rows[:20]

    # Load JSON metadata file 
    json_path = csv_path.replace('.csv', '-metadata.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                json_content = json_file.read()
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            json_content = "Error loading JSON metadata file"
    else:
        json_content = "No JSON metadata file found"

    # Return the html page and variables used in layout generation
    return render(request, "converter/convert_screen.html", {
        "headers": headers,
        "rows": preview_rows,
        "full_table": full_table,
        "json_content": json_content,
        "all_matches": request.session.get("all_matches", {}),
        "request_type": request.session.get('request_type'),
        "vocab_coverage_score": request.session.get('vocab_coverage_score'),
        "sorted_vocabs": request.session.get('sorted_vocabs'),
        "best_match_index": request.session.get('best_match_index')
    })



# -------------------------Starting Screen---------------------------- 
# Responsible for rendering the home / start screen of the project
# Handles the file submission and processing
# Calls on the vocabulary recommender engine for processing the csv headers
# After the conversion the welcome_view renders the main converter screen of SmartCow 
#---------------------------------------------------------------------

def welcome_view(request):
    """
    Main function that renders the starting page on the website. 
    It also stores the uploaded file and creates the metadata from it.
    Starts the vocabulary recommendation process.
    """

    file_name = None
    metadata_file_path = None

    # Receive the file from the cache
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

            # Compute necessary scores + retrieve the matches from recommender engine
            sorted_vocabs, best_match_index, vocab_coverage_score, all_matches = engine.run_lov_requests()
            
            best_match_index = {header:index for header, index in best_match_index}
           
            vocab_coverage_score = sorted(vocab_coverage_score, key=lambda score: score[1], reverse=True)

            # Store vocabulary-recommender related parameters in session for retrieval
            request.session['request_type'] = 'Homogenous'
            request.session['metadata_file_path'] = metadata_file_path
            request.session['headers'] = headers
            request.session['all_matches'] = all_matches
            request.session['best_match_index'] = best_match_index
            request.session['custom_endpoint'] = ""
            request.session['csv_path'] = csv_path
            request.session['vocab_coverage_score'] = vocab_coverage_score
            request.session['sorted_vocabs'] = sorted_vocabs

            logger.info(request.session['request_type'])
            logger.info(request.session['metadata_file_path'])

            # Overwrite the template metadata file with the best matches
            update_metadata(metadata_file_path, headers, all_matches, best_match_index, 'Homogenous', '')

            return redirect('convert_screen')

    return render(request, 'converter/welcome.html', {
        'file_name': file_name,
        'metadata_generated': bool(metadata_file_path),
        'metadata_path': metadata_file_path,
    })


def store_selected_row(request):
    """
    Function store_selected_row that 
    """
    if request.method == "POST":
        data = json.loads(request.body)

        selected_row = data.get('selected_row', [])
        current_header = data.get('current_header', [])

        request.session['selected_row'] = selected_row
        request.session['current_header'] = current_header
        request.session['redirect_link'] = selected_row[2] # The 3rd element of every row is URI

        return JsonResponse({
            'status': 'ok',
            'redirect_link': selected_row[2]
            })
    
    if request.method == "GET":
        redirect_link = request.session.get('redirect_link')

        return JsonResponse({
            'status': 'ok',
            'redirect_link': redirect_link
        })
    
    return JsonResponse({"error": 'Invalid request'}, status=400)


def insert_match(request):
    """
    This function inserts the selected match
    """
    
    if request.method == "POST":

        # Retrieve required data from the session
        metadata_path = request.session.get('metadata_file_path', '')
        row_data = request.session.get('selected_row', [])
        header = request.session.get('current_header', '')


        # Insert the match into metadata 
        insert_instance(metadata_path, row_data, header)

        return redirect('convert_screen')
    return JsonResponse({"error": 'Invalid request'}, status=400)
        

def save_file(request):
    """
    This function saves the file 
    """

    if request.method == "POST":
        
        # Get data from the form
        json_text = request.POST.get('json_text', '')
        metadata_path = request.session.get('metadata_file_path', '')

        data = json.loads(json_text)

        # Write to the file
        if data:
            with open(metadata_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=2, ensure_ascii=False)

        logger.info("Successfully saved the file")


        return redirect('convert_screen')