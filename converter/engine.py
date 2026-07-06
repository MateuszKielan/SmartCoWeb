import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple

from .requests_t import get_recommendations, organize_results, retrieve_combiSQORE_recursion, get_average_score, calculate_combi_score, get_vocabs

logger = logging.getLogger(__name__)

# Cap on concurrent outbound requests to the LOV API. Keeps us from hammering
# the public endpoint while still collapsing N serial round-trips into a few.
# The executor is shared by all requests so the cap is service-wide: ten users
# uploading at once queue their header lookups here instead of opening
# 10 x MAX_LOV_WORKERS connections to LOV from one IP.
MAX_LOV_WORKERS = 16
_LOV_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_LOV_WORKERS)

class Engine:
    def __init__(self, headers) -> None:
        self.headers = headers
        self.vocabs = []
        self.all_results = {}
        self.sorted_vocabularies = []
        self.vocab_coverage_score = []
        self.final_matches = []
        self.execution_times = {}

    def construct_vocabulary_scoring(self, sorted_vocabularies, vocab_coverage_score, avg_scores):
        """
        Function that process the vocabulary data and creates one lookup index in the form of a map::
        {vocabulary: [avg_score, vocab_coverage_score, combi_score]}

        Params:
            sorted_vocabularies (Arr(Arr(2))): array of arrays that represents the vocabulary and its combi sqore
            vocab_coverage_score (Arr(Arr(2))): array of arrays that represents the vocabulary and its coverage score
            avg_scores (Arr(Arr(2))): array of arrays that represents the vocabulary and its single average score
        Return:
            vocabulary_data(Dict{vocab:Arr(avg_score, vocab_coverage_score, combi_score)})
        """

        vocabulary_data = {}

        for vocab_score in sorted_vocabularies:
            if (vocab_score[0] not in vocabulary_data):
                vocabulary_data[vocab_score[0]] = [vocab_score[1]]
            else:
                pass

        for i in range(0, len(avg_scores)):
            vocabulary_data[avg_scores[i][0]].insert(0, avg_scores[i][1])
        
        for i in range(0, len(vocab_coverage_score)):
            vocabulary_data[vocab_coverage_score[i][0]].insert(1, vocab_coverage_score[i][1])
        
        return vocabulary_data


    def run_lov_requests(self, match_limit=20):
        """
        Function that processes requests to the Linked Open Vocabularies and calculates the scores of retrieved matches

        Params:
            match_limit (int): maximum limit of retrieved matches per header. Default is 20
        Return:
            sorted_vocabularies
            final_matches

        """

        def fetch(header):
            """Fetch and organise recommendations for a single header."""
            try:
                recs = get_recommendations(header, match_limit)
                return header, organize_results(recs)
            except Exception as e:
                logger.warning(f"LOV error for header '{header}': {e}")
                return header, []

        # Query the LOV API for every header concurrently on the shared,
        # service-wide executor. The results are reassembled in the original
        # header order so downstream scoring is deterministic regardless of
        # which request finishes first.
        results_by_header = {}
        for header, matches in _LOV_EXECUTOR.map(fetch, self.headers):
            results_by_header[header] = matches

        self.all_results = {header: results_by_header[header] for header in self.headers}

        # Get list of vocabularies
        self.vocabs = get_vocabs(self.all_results)

        # Calculate average score and Combi Score
        avg_scores = get_average_score(self.vocabs, self.all_results)
        self.sorted_vocabularies, self.vocab_coverage_score = calculate_combi_score(self.all_results, avg_scores)

        self.sorted_vocabularies = sorted(self.sorted_vocabularies, key=lambda x: x[1], reverse=True)
        
        vocabulary_data = self.construct_vocabulary_scoring(self.sorted_vocabularies, self.vocab_coverage_score, avg_scores)

        # Get best match index for each header
        self.final_matches = retrieve_combiSQORE_recursion(
            self.all_results,
            self.sorted_vocabularies,
            len(self.headers)
        )

        return vocabulary_data, avg_scores, self.sorted_vocabularies, self.final_matches, self.vocab_coverage_score, self.all_results