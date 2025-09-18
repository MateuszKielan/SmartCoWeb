from pathlib import Path
import time
import logging
import csv
from cow_csvw.converter.csvw import build_schema

logger = logging.getLogger(__name__)

def convert_with_cow(csv_path: str):
    """
    Converts a CSV file into a JSON metadata file using CoW (CSV on the Web).
    """
    input_path = Path(csv_path)
    output_metadata_path = input_path.parent / f"{input_path.stem}-metadata.json"

    if output_metadata_path.exists():
        logger.info("[CoW]: Metadata file already exists. Loading data.")
        return output_metadata_path

    try:
        start_time = time.time()
        build_schema(str(input_path), str(output_metadata_path))
        duration = time.time() - start_time
        logger.info(f"[CoW]: Metadata saved to {output_metadata_path}")
        logger.info(f"[Conversion time]: {duration:.2f} seconds")
        return output_metadata_path
    except Exception as e:
        logger.error("[CoW]: Metadata generation failed")
        logger.exception(e)
        return None


def get_csv_headers(file_path: str) -> list:
    """
    Function get_csv_header that opens a file and extracts headers from the csv for parsing into the vocabulary

    Args:
        file_path (str) : path of the file
    Returns:
        headers (arr) : headers of the csv
    """

    with open(file_path, "r", encoding="utf-8") as csv_file:
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect)
        headers = next(reader)
    return headers