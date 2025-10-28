import json
import logging

logger = logging.getLogger(__name__)


def update_metadata(path, headers, all_results, request_results, mode, custom_endpoint):
    """
    Function update_metadata that overwrites the metadata file with the best matches.

    Args:
        headers (str): list of all headers
        all_results (list): list of all matches for every header
        request_results (list): best match index for each header
        mode (str): request mode
        custom_endpoint (str): url to the custom enpoint
    """

    # Open and read the file 
    with open(path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Build the lookup index based on the type of request
    index_lookup = {
        header: (idx if mode == 'Homogenous' else 0)
        for header, idx in request_results.items()
    }

    # Insert the best match
    for column in data.get('tableSchema', {}).get('columns', []):
        header = column.get('name')
        if header in all_results and header in index_lookup:
            match = all_results[header][index_lookup[header]]

            column.update({
                'name': header,
                'prefixedName': match[0][0] if custom_endpoint == "" else match[0],
                '@id': match[2][0] if custom_endpoint == "" else match[2],
                'propertyUrl': match[2][0] if custom_endpoint == "" else match[2],
                'vocab': match[1],
                'type': match[3],
                'score': match[4],
            })

    # Write new data into the file
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    return path


def insert_instance(path, row, header):
    """
    Inserts the selected match into the metadata file for the current header.

    Args:
        table (MDDataTable): full table data
        row (list): data of the selected row
    """

    # REMEMBER WRITE A CLEANUP FUNCTION
    # Parse and clean the row values
    name = row[0]
    vocab = row[1]
    uri = row[2]
    rdf_type = row[3]
    score = float(row[4])


    # Open the csv file for reading
    with open(path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Initialize the flag to track success of the update
    updated = False

    # Loop through all columns in the tableSchema
    for column in data.get('tableSchema', {}).get('columns', []):
        if column.get('name') == header:
            column.update({
                'prefixedName': name,     # prefixed name 
                '@id': uri,               # uri
                'vocab': vocab,           # vocabulary 
                'propertyUrl': uri,        # uri
                'type': rdf_type,         # rdf type
                'score': score            # score
            })

            updated = True # If replaced update the flag
            logger.info(f"[Inserted] {header} -> {name} ({vocab})")

    # Display warning
    if not updated:
        logger.warning(f"Insert Failed: Header '{header}' not found in metadata.")

    # Save the modified data to the file 
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"Metadata File Written: {path}")