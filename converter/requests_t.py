# This file takes care of the requect to the LOV api endpoint.
# It further implements the logic behind the combiSQORE vocabulary ranking algorithm.
# For more info on combiSQORE check: (LINK TO THE PAPER)



# -------- Imports Section ------------
import requests
from copy import deepcopy
import logging


# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# Lov api url
# MAYBE CHANGE THE NAME AS WELL
recommender_url = "https://lov.linkeddata.es/dataset/lov/api/v2/term/search"

# The public LOV endpoint is frequently slow (20s+ for a single query), so give
# it a generous timeout. Override with the LOV_TIMEOUT environment variable.
import os
REQUEST_TIMEOUT = int(os.environ.get("LOV_TIMEOUT", "30"))

# Empty-but-valid response shape so downstream code can always read ["results"].
_EMPTY_RESULT = {"results": []}


def get_recommendations(header: str, size: int) -> dict:
    """
    Function get_recommendations that receives headers and runs a get requests to the vocabulary api

    Args:
        headers (arr): headers of the csv file
    Returns:
        results (dict): results of the request for the given header.
                        On any failure returns {"results": []} so callers never
                        have to special-case the error path.
    """
    params = {
        "q": header,
        "category": "class",
        "page_size": size # Manually selected by users
    }
    try:
        response = requests.get(recommender_url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout when querying API for header: {header}")
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to the API.")
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error: {e}")

    return _EMPTY_RESULT



def display_results(result: dict, name: str):
    """
    HELPER fucntion display_results that takes query results and displays them in a readable format

    !Only used for debugging!
    
    Args:
        results (dict) : query results converted to json
        name (str): name of the header
    """
    matches = result['results']
    print(f"TOTAL OF {len(matches)} MATCHES FOR {name}")

    for count, match in enumerate(matches):
   
        print(f"-------Match {count + 1}--------")
        print(matches[count]['prefixedName'])
        print(matches[count]['vocabulary.prefix'])
        print(matches[count]['uri'])
        print(matches[count]['type'])
        print(matches[count]['score'])
    print("--------------------------------")



def organize_results(result: dict) -> list:
    """
    Function organize_results that converts the query result into below specified format.

    Args: 
        result: retrieved matches for the header

    Returns:
        match_arr (arr(arr)): array with the matches data
        

    TARGET format:

    all_results {
        header1: [match(i),match(i+1),...,match(i+n)]
        header2: [match(i),match(i+1),...,match(i+n)]
    }

    Function takes care of the following part: 
        match(i) = [prefixedName, vocabulary.prefix, uri, type, score]

    """

    # Initialize the array for matches
    match_arr = []
    matches = result['results']

    # For every match create a sub arary with retrieved coresponding data
    for id, match in enumerate(matches):

        sub_match = []
        sub_match.append(matches[id]['prefixedName'])
        sub_match.append(matches[id]['vocabulary.prefix'][0])
        sub_match.append(matches[id]['uri'])
        sub_match.append(matches[id]['type'])
        sub_match.append(matches[id]['score'])

        match_arr.append(sub_match)

    return match_arr



def get_vocabs(all_results: dict) -> list:
    """
    Function get_vocabs that finds all vocabularies in the recommendation matches.

    Args:
        - all_results (dict): dictionary with matches for all headers
    Returns:
        - vocabs (arr): array with unique vocabularies
    """

    # Initialize list of vocabularies
    vocabs = []

    # Add every unique vocabulary from the request result to the list
    for header in all_results:
        for match in all_results[header]:
            if match[1] in vocabs:
                continue
            else:
                vocabs.append(match[1])

    return vocabs



def get_average_score(vocabs: list, all_results: dict) -> list[tuple]:
    """
    Function get_average_score that computes average score for every distinct vocabulary.

    Args:
        - vocabs (arr): list of all vocabularies.
        - all_results (dict): dictinary with matches for all header.
    Returns:
        - vocab_scores (arr(tuple)): array with typles consisting of 
    """     
    # Initialize list of scores that will be filled with tuples of the following format:
    # (vocabulary_name, average_score)
    vocab_scores = []

    # Calculate the average score for every vocabulary and add to the list
    for vocab in vocabs:
        score = 0
        num = 0
        for header in all_results:
            for match in all_results[header]:
                if match[1] == vocab:
                    score += match[4]
                    num += 1
        avg_score = score / num
        vocab_scores.append((vocab, avg_score))

    # Sort the vocabulary list by their corresponding scores in descending order
    vocab_scores = sorted(vocab_scores, key=lambda x: x[1], reverse=True)
    return vocab_scores


def normalize_scores(scores: tuple[str, int]) -> tuple[str, int]:
    """
    Function normalize_scores that takes list of scroes and normalizes them according to the min max formula

    Args:
        scores (tuple(int,str)): tuple of vocabularies with corresponding scores
    Returns:
        scores (tuple(int,str)): tuple of voacbularies with corresponding normalized scores
    """
    scores_dict = dict(scores)

    # Nothing to normalize (e.g. the LOV API returned no matches at all).
    if not scores_dict:
        return []

    min_score = min(scores_dict.values())
    max_score = max(scores_dict.values())
    score_range = max_score - min_score

    for vocab in scores_dict:
        # When every score is equal the range is zero; treat all as 0 to avoid
        # dividing by zero.
        if score_range == 0:
            scores_dict[vocab] = 0.0
        else:
            scores_dict[vocab] = (scores_dict[vocab] - min_score) / score_range

    return list(scores_dict.items())


def calculate_combi_score(all_results: dict, vocab_scores: list[tuple]) -> list[tuple]:
    """
    Function calculate_combi_score that calculates combi score of every vocabulary based on:
        1. SS - Similarity score 
        2. QC - Query coverage 

        Query-Combinative-Ontology Similarity Score = SS * QC

    Args:
        all_results (dict(list())) - data of all headers and all matches.
        vocab_scores (list(tuple))  - list of vocabularies with their corresponding scores.
        necesary_vocabs (list(tuple)) - list of necessary vocabularies identified in necessary vocabs function.

    Returns:
        new_vocab_scores (list(tuple)) - list of vocabularies with the calculated combi score.
    """
    vocab_coverage_score = []
    new_vocab_scores = []

    vocab_data = {}

    for vocab in vocab_scores:
        
        vocab_name = vocab[0]
        vocab_similarity_score = vocab[1]
        vocab_query_coverage = 0
        vocab_combi_score = 0

        for header in all_results:
            for match in all_results[header]:

                if match[1] == vocab_name:
                    vocab_query_coverage += 1

        vocab_coverage_score.append((vocab[0], vocab_query_coverage))
        vocab_combi_score = vocab_similarity_score * vocab_query_coverage
    
        new_vocab_scores.append((vocab_name, vocab_combi_score))

    new_vocab_scores = normalize_scores(new_vocab_scores)

    return new_vocab_scores, vocab_coverage_score


def retrieve_combiSQORE(best_vocab: str, all_results: dict) -> list[tuple]:
    """
    Funciton retrieve_homogenous that retrieves the matches based on the best vocabulary based on combiSQORE

    Args:
        - best_vocab (str): best vocabulary  (see the combiSQORE function)
    Returns:
        - request_return (list(tuple)): array containing tuples with the following format:
            (header, match_index)

    Main logic:
        1. For every header check all the matches
        2. For every match check if it is from a best_vocab
            3. If yes add it to the list and move to the next header
        4. If the header has no matches with the best_vocab, select the first match 
    """

    request_return = []

    for header in all_results:
        choice = False
        for index, match in enumerate(all_results[header]):
            if match[1] == best_vocab:
                print(f'Header {header}: FOUND a match for {best_vocab}')
                choice = match
                request_return.append((header,index))
                # When match is found terminate immidiately
                break
            else:
                continue
        # If no match is found take the first match for the header 
        if choice == False:
            print(f"Header {header}: NOT FOUND a match for {best_vocab}")
            request_return.append((header, 0))

    return request_return


def retrieve_combiSQORE_recursion(all_results: dict, vocab_scores: list[tuple], num_headers: int, matched=None, unmatched=None) -> list[tuple]:
    """
    Recursive function to retrieve best matches for each header using lsit of ranked vocabularies.

    Args:
        - all_results (dict): {header: list of matches}
        - vocab_scores (list): (vocab_name, score), sorted descending
        - matched (list): list of already matched (header, index) pairs
        - unmatched (list): list of headers that still need to be matched

    Returns:
        - matched: list of (header, index) pairs representing best matches
    """
    if matched is None:
        matched = []
    if unmatched is None:
        unmatched = list(all_results.keys())

    if not vocab_scores:
        print("No more vocabularies to try.")
        return matched

    if len(matched) == num_headers:
        return matched
    
    current_vocab = vocab_scores[0][0]
    print(f"Trying vocabulary: {current_vocab}")

    still_unmatched = []
    
    for header in unmatched:
        found = False
        for idx, match in enumerate(all_results[header]):
            if match[1] == current_vocab:
                print(f"Matched header '{header}' with vocab '{current_vocab}'")
                matched.append((header, idx))
                found = True
                break
        if not found:
            print(f"No match for '{header}' in vocab '{current_vocab}'")
            still_unmatched.append(header)

    return retrieve_combiSQORE_recursion(all_results, vocab_scores[1:], num_headers, matched, still_unmatched)


def rank_with_priority(all_results: dict, sorted_vocabs: list, priority_list: list, num_headers: int) -> dict:
    """
    Re-select the best match per header, honouring a user-defined vocabulary
    priority order. User-prioritised vocabularies are tried first (in the given
    order); any remaining vocabularies follow in their original combiSQORE order.

    No new requests are made - this reuses the already-retrieved matches.

    Args:
        all_results (dict): {header: list of matches} (cached recommender output)
        sorted_vocabs (list): [(vocab, score), ...] ranked by combiSQORE
        priority_list (list): vocabulary names in the user's preferred order
        num_headers (int): number of headers/columns
    Returns:
        dict: {header: match_index} best-match selection
    """
    ranked = [v[0] for v in sorted_vocabs]

    # Priority vocabularies first (de-duplicated), then the rest by combi score.
    ordered = []
    for vocab in priority_list:
        vocab = (vocab or "").strip()
        if vocab and vocab not in ordered:
            ordered.append(vocab)
    for vocab in ranked:
        if vocab not in ordered:
            ordered.append(vocab)

    # The recursion iterates the list in order; the score field is unused here.
    vocab_scores = [(vocab, 0) for vocab in ordered]
    matched = retrieve_combiSQORE_recursion(all_results, vocab_scores, num_headers)
    return dict(matched)


#--------------------------------------------------------------

#--------------------------------------------------------------
