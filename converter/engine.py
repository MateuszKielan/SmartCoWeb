import logging
from typing import List, Dict, Tuple

from .requests_t import get_recommendations, organize_results, retrieve_combiSQORE_recursion, get_average_score, calculate_combi_score, get_vocabs

logger = logging.getLogger(__name__)

class Engine:
    def __init__(self, headers) -> None:
        self.headers = headers
        self.vocabs = []
        self.all_results = {}
        self.sorted_vocabularies = []
        self.vocab_coverage_score = []
        self.final_matches = []
        self.execution_times = {}

    def run_lov_requests(self, match_limit=20):
        """
        Function that processes requests to the Linked Open Vocabularies and calculates the scores of retrieved matches

        Params:
            match_limit (int): maximum limit of retrieved matches per header. Default is 20
        Return:
            sorted_vocabularies
            final_matches

        """

        for header in self.headers:
            try:
                recs = get_recommendations(header, match_limit)
                self.all_results[header] = organize_results(recs)
            except Exception as e:
                logger.warning(f"LOV error for header '{header}': {e}")
                self.all_results[header] = []

        # Get list of vocabularies
        self.vocabs = get_vocabs(self.all_results)

        # Calculate average score and Combi Score
        avg_scores = get_average_score(self.vocabs, self.all_results)
        self.sorted_vocabularies, self.vocab_coverage_score = calculate_combi_score(self.all_results, avg_scores)

        self.sorted_vocabularies = sorted(self.sorted_vocabularies, key=lambda x: x[1], reverse=True)
        
        # Get best match index for each header
        self.final_matches = retrieve_combiSQORE_recursion(
            self.all_results,
            self.sorted_vocabularies,
            len(self.headers)
        )

        return self.sorted_vocabularies, self.final_matches, self.vocab_coverage_score, self.all_results