from pathlib import Path
import time
import logging
import csv
import json
from cow_csvw.converter.csvw import build_schema, CSVWConverter
from shutil import copyfile

logger = logging.getLogger(__name__)


def detect_delimiter(file_path: str, default: str = ",") -> str:
    """
    Detect the column delimiter of a CSV file.

    Uses csv.Sniffer restricted to the common delimiters so a file like
    "a;b;c" is not mistaken for a single column. Falls back to ``default``
    when detection fails (e.g. a single-column file).
    """
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
            sample = csv_file.read(4096)
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except (csv.Error, OSError) as e:
        logger.warning(f"Delimiter detection failed for {file_path}: {e}. Using {default!r}.")
        return default


def _set_metadata_delimiter(metadata_path: Path, delimiter: str) -> None:
    """
    Ensure the metadata dialect uses the real CSV delimiter.

    CoW's build_schema detects the columns correctly but can record the wrong
    dialect delimiter (e.g. ',' for a ';'-separated file), which would make the
    N-Quads conversion split rows incorrectly. This corrects it in place.
    """
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dialect = data.setdefault("dialect", {})
        if dialect.get("delimiter") != delimiter:
            dialect["delimiter"] = delimiter
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"[CoW]: Corrected metadata dialect delimiter to {delimiter!r}")
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Could not patch metadata delimiter: {e}")


def convert_with_cow(csv_path: str):
    """
    Converts a CSV file into a JSON metadata file using CoW (CSV on the Web).
    """
    input_path = Path(csv_path)
    output_metadata_path = input_path.parent / f"{input_path.stem}-metadata.json"
    delimiter = detect_delimiter(str(input_path))

    if output_metadata_path.exists():
        logger.info("[CoW]: Metadata file already exists. Loading data.")
        _set_metadata_delimiter(output_metadata_path, delimiter)
        return output_metadata_path

    try:
        start_time = time.time()
        build_schema(str(input_path), str(output_metadata_path))
        duration = time.time() - start_time
        _set_metadata_delimiter(output_metadata_path, delimiter)
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

    delimiter = detect_delimiter(file_path)
    with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=delimiter)
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

        # Ensure CoW finds the (latest) metadata where it expects it. Always
        # overwrite so saved JSON edits and delimiter fixes are picked up, rather
        # than reusing a stale copy from a previous run.
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