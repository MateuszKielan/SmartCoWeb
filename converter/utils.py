from pathlib import Path
import time
import logging
import csv
from cow_csvw.converter.csvw import build_schema, CSVWConverter
from shutil import copyfile

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


def convert_json_to_nquads(selected_file):
    # Check if the file exists
    if not selected_file.exists():
        logger.error(f"System: CSV file does not exist at: {selected_file}")
    else:
        logger.info(f"System: CSV file does exist at: {selected_file}")

    metadata_file = selected_file.with_name(f"{selected_file.stem}-metadata.json")

    # Check if the metadata file exists
    if not metadata_file.exists():
        logger.error(f"System: Metadata file not found: {metadata_file}")
    else:
        logger.info(f"System: Metadata file found: {metadata_file}")

    try:
        start_time_converter = time.time()
        # Extract file paths
        input_csv_path = str(selected_file)
        correct_metadata_path = selected_file.with_name(f"{selected_file.stem}-metadata.json")
        cow_expected_path = selected_file.with_name(f"{selected_file.name}-metadata.json")

        # Ensure CoW finds the metadata file where it expects it
        if not cow_expected_path.exists():
            copyfile(correct_metadata_path, cow_expected_path)
            logger.info(f"System: Copied metadata to CoW-expected path: {cow_expected_path}")
        
        # Instantiate and run the converter
        converter = CSVWConverter(
            file_name=input_csv_path,
            processes=1,
            output_format="nquads",
            base="https://example.com/id/"  
        )

        converter.convert()

        logger.info("CoW: Conversion to N-Quads completed successfully.")
        end_time_converter = time.time()
        total_execution_time_converter = end_time_converter - start_time_converter
        logger.info(f"Total execution time of conversion: {total_execution_time_converter} seconds")
    except Exception as e:
        logger.error(f"CoW: Error during conversion: {e}")