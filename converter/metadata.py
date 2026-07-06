import json
import logging

logger = logging.getLogger(__name__)


def _namespace_from_uri(uri: str) -> str:
    """
    Return the namespace part of a term URI (everything up to and including the
    last '#' or '/'). E.g. 'http://dbpedia.org/ontology/Surname' ->
    'http://dbpedia.org/ontology/'.
    """
    if not uri:
        return ""
    if "#" in uri:
        return uri.rsplit("#", 1)[0] + "#"
    if "/" in uri:
        return uri.rsplit("/", 1)[0] + "/"
    return uri


def _add_namespaces(data: dict, entries) -> None:
    """
    Ensure each (prefix -> namespace URI) pair exists in the @context namespaces
    map, so the prefixedName values written for the selected matches resolve.

    Existing prefixes are left untouched (the CoW base list wins).
    """
    ctx = data.get("@context")
    if not isinstance(ctx, list):
        return

    # The namespaces entry is the @context object that has non-'@' keys.
    ns_obj = next(
        (el for el in ctx
         if isinstance(el, dict) and any(not k.startswith("@") for k in el)),
        None,
    )
    if ns_obj is None:
        ns_obj = {}
        ctx.append(ns_obj)

    for prefix, uri in entries:
        if prefix and uri and prefix not in ns_obj:
            ns_obj[prefix] = uri
            logger.info(f"[Namespace] Added '{prefix}': '{uri}'")


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
    ns_entries = []
    for column in data.get('tableSchema', {}).get('columns', []):
        header = column.get('name')
        if header in all_results and header in index_lookup:
            match = all_results[header][index_lookup[header]]

            # Matches hold plain strings (see organize_results), no unwrapping needed.
            prefixed_name = match[0]
            uri = match[2]

            column.update({
                'name': header,
                'prefixedName': prefixed_name,
                '@id': uri,
                'propertyUrl': uri,
                'vocab': match[1],
                'type': match[3],
                'score': match[4],
            })

            # Register the namespace for the prefix used in prefixedName.
            prefix = prefixed_name.split(":", 1)[0] if ":" in str(prefixed_name) else match[1]
            ns_entries.append((prefix, _namespace_from_uri(uri)))

    # Add the namespaces of the selected vocabularies to @context.
    _add_namespaces(data, ns_entries)

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
                'propertyUrl': uri,       # uri
                'type': rdf_type,         # rdf type
                'score': score            # score
            })

            updated = True # If replaced update the flag
            logger.info(f"[Inserted] {header} -> {name} ({vocab})")

    # Register the namespace for the inserted match's prefix.
    if updated:
        prefix = name.split(":", 1)[0] if ":" in str(name) else vocab
        _add_namespaces(data, [(prefix, _namespace_from_uri(uri))])

    # Display warning
    if not updated:
        logger.warning(f"Insert Failed: Header '{header}' not found in metadata.")

    # Save the modified data to the file 
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"Metadata File Written: {path}")