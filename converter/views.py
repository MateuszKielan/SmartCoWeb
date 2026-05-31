# DONT FORGET TO SORT THE IMPORTS PLS 
from re import X
from turtle import update
from django.shortcuts import render, redirect
from django.conf import settings
import os
import json
from .utils import convert_with_cow, get_csv_headers, convert_json_to_nquads, detect_delimiter
from .metadata import update_metadata, insert_instance
from pathlib import Path
import logging
from .engine import Engine
from .requests_t import rank_with_priority
from . import storage
import csv
from django.http import JsonResponse, FileResponse
from django.urls import reverse
from .models import Support



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
            return JsonResponse({
                "status": "success",
                "message": "Converted to N-Quads successfully.",
                "download_url": reverse("download_nquads"),
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def replace_all(request):
    """
    Represents functionality of "Replace All" button
    Call the update_metadata function to overwrite the metadata file with best matches
    """
    if request.method == "POST":

        job_data = storage.get_recommender_data(request.session)

        update_metadata(
            request.session.get('metadata_file_path', ''),
            job_data.get('headers', []),
            job_data.get('all_matches', {}),
            job_data.get('best_match_index', {}),
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


    # Open and process the csv file (detect the delimiter so e.g. ';' files
    # are not collapsed into a single column).
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=detect_delimiter(csv_path))
        all_rows = list(reader)
        headers = all_rows[0]
        data_rows = all_rows[1:]

        # full and preview rows for the converter screen      
        full_table = data_rows
        preview_rows = data_rows[:20]

    # Retrieve the recommender payload from the cache (not the session).
    job_data = storage.get_recommender_data(request.session)
    all_matches = job_data.get('all_matches', {})

    # Retrieve num of matches for each header
    matches_count = {header: len(all_matches[header]) for header in all_matches }

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
        "all_matches": all_matches,
        "request_type": request.session.get('request_type'),
        "vocab_coverage_score": job_data.get('vocab_coverage_score'),
        "sorted_vocabs": job_data.get('sorted_vocabs'),
        "best_match_index": job_data.get('best_match_index'),
        'vocabulary_data': job_data.get("vocabulary_data"),
        "matches_count": matches_count
    })



# -------------------------Starting Screen---------------------------- 
# Responsible for rendering the home / start screen of the project
# Handles the file submission and processing
# Calls on the vocabulary recommender engine for processing the csv headers
# After the conversion the welcome_view renders the main converter screen of SmartCow 
#---------------------------------------------------------------------

def _user_upload_dir(request):
    """
    Return a per-session upload directory, creating it if needed.

    Isolating each visitor's files under their session id prevents one user's
    upload from overwriting another's when they happen to share a filename
    (e.g. two people both uploading "data.csv" on the shared server).
    """
    if not request.session.session_key:
        request.session.create()
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', request.session.session_key)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


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

            # Save the uploaded file to this user's private upload folder.
            upload_dir = _user_upload_dir(request)
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
            vocabulary_data, avg_scores, sorted_vocabs, best_match_index, vocab_coverage_score, all_matches = engine.run_lov_requests()

            best_match_index = {header:index for header, index in best_match_index}

            vocab_coverage_score = sorted(vocab_coverage_score, key=lambda score: score[1], reverse=True)

            # Fresh upload: drop any cached results from a previous job.
            storage.clear_job(request.session)

            # Keep only small identifiers in the session.
            request.session['request_type'] = 'Homogenous'
            request.session['metadata_file_path'] = metadata_file_path
            request.session['custom_endpoint'] = ""
            request.session['csv_path'] = csv_path

            # Store the heavy recommender payload in the cache, not the session.
            storage.save_recommender_data(request.session, {
                'headers': headers,
                'all_matches': all_matches,
                'best_match_index': best_match_index,
                'vocab_coverage_score': vocab_coverage_score,
                'sorted_vocabs': sorted_vocabs,
                'vocabulary_data': vocabulary_data,
            })

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


# -------------------------- htmx partial endpoints --------------------------
# These return small HTML fragments that htmx swaps into the page, replacing the
# old client-side DOM building and the large json_script blobs.
# ----------------------------------------------------------------------------

def _row_payload(match):
    """Flatten a raw match into display cells + a JSON string for the insert flow."""
    cells = [c[0] if isinstance(c, list) and c else c for c in match]
    return {"cells": cells, "json": json.dumps(cells)}


def header_matches(request):
    """Return the match table fragment for a single header (htmx GET)."""
    header = request.GET.get('header', '').strip()
    job_data = storage.get_recommender_data(request.session)
    all_matches = job_data.get('all_matches', {})
    best_match_index = job_data.get('best_match_index', {})

    if header not in all_matches:
        return render(request, "converter/partials/match_table.html", {
            "header": header,
            "not_found": True,
        })

    matches = all_matches[header]
    best_idx = best_match_index.get(header, 0)

    return render(request, "converter/partials/match_table.html", {
        "header": header,
        "rows": [_row_payload(m) for m in matches],
        "best_row": _row_payload(matches[best_idx]) if matches else None,
        "columns": ["prefixedName", "vocabulary.prefix", "uri", "type", "score"],
    })


def vocab_ranking(request):
    """Return the vocabulary ranking table fragment (htmx GET)."""
    job_data = storage.get_recommender_data(request.session)
    vocabulary_data = job_data.get('vocabulary_data', {})

    # vocabulary_data maps vocab -> [avg_score, coverage, combi_score]
    rows = [
        {"vocab": vocab, "avg": values[0], "coverage": values[1], "combi": values[2]}
        for vocab, values in vocabulary_data.items()
    ]
    rows.sort(key=lambda r: r["combi"], reverse=True)

    return render(request, "converter/partials/vocab_table.html", {"rows": rows})


def insert_match(request):
    """
    Insert a single selected match into the metadata file (htmx POST).

    Receives the row values and header directly in the request body, writes them
    to the metadata JSON, and returns the refreshed JSON preview fragment so the
    right-hand panel updates in place.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)
    row = data.get("row", [])
    header = data.get("header", "")
    metadata_path = request.session.get("metadata_file_path", "")

    if not (row and header and metadata_path):
        return JsonResponse({"error": "Missing row, header or metadata path"}, status=400)

    insert_instance(metadata_path, row, header)

    content = ""
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as json_file:
            content = json_file.read()

    return JsonResponse({"status": "success", "json": content})


def save_file(request):
    """Persist edited JSON from the preview textarea (htmx POST)."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    json_text = request.POST.get('json_text', '')
    metadata_path = request.session.get('metadata_file_path', '')

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return JsonResponse({"status": "error", "message": f"Invalid JSON: {e}"}, status=400)

    if data and metadata_path:
        with open(metadata_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)
        logger.info("Successfully saved the file")

    return JsonResponse({"status": "success", "message": "Saved."})


def download_nquads(request):
    """Serve the generated N-Quads file as a download."""
    csv_path = request.session.get('csv_path')
    if not csv_path:
        return JsonResponse({"status": "error", "message": "No file in session."}, status=400)

    nquads_path = Path(f"{csv_path}.nq")
    if not nquads_path.exists():
        return JsonResponse({"status": "error", "message": "Convert the file first."}, status=404)

    return FileResponse(
        open(nquads_path, "rb"),
        as_attachment=True,
        filename=nquads_path.name,
        content_type="application/n-quads",
    )


def submit_support(request):
    """Handle support form submissions (htmx POST)."""
    if request.method == "POST":
        try:
            Support.objects.create(
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                contact=request.POST.get('contact') or None
            )
            return JsonResponse({"status": "success", "message": "Thanks! Your request was submitted."})
        except Exception:
            return JsonResponse({
                "status": "error",
                "message": "Sorry, there was an error submitting your request."
            }, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def process_priority_list(request):
    """
    Apply a user-defined vocabulary priority order to the cached recommender
    results, rewrite the metadata, and return the refreshed JSON (POST).
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        priority_list = data.get('priority_list', [])
    except json.JSONDecodeError:
        priority_list = []

    request.session['vocab_priority_list'] = priority_list
    logger.info(f"Vocabulary priority list: {priority_list}")

    job_data = storage.get_recommender_data(request.session)
    all_matches = job_data.get('all_matches', {})
    sorted_vocabs = job_data.get('sorted_vocabs', [])
    headers = job_data.get('headers', [])
    metadata_path = request.session.get('metadata_file_path', '')

    if not all_matches or not metadata_path:
        return JsonResponse(
            {"status": "error", "message": "No dataset loaded to apply the priority to."},
            status=400,
        )

    # Re-select the best match per header using the priority order, then persist.
    best_match_index = rank_with_priority(all_matches, sorted_vocabs, priority_list, len(headers))
    storage.save_recommender_data(request.session, {'best_match_index': best_match_index})

    # Rewrite the metadata columns with the re-ranked best matches.
    update_metadata(
        metadata_path,
        headers,
        all_matches,
        best_match_index,
        'Homogenous',
        request.session.get('custom_endpoint', ''),
    )

    content = ""
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as json_file:
            content = json_file.read()

    return JsonResponse({"status": "success", "json": content, "priority_list": priority_list})