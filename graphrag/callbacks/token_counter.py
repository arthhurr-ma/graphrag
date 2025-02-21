import logging 
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict


log = logging.getLogger(__name__)

class Token_Counter:
    _instance = None


    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Token_Counter, cls).__new__(cls)
        return cls._instance


    def __init__(self):
        if not hasattr(self, 'initialized'):  
            self.initialized = True
            self.graph_extractor_input_tokens = 0
            self.graph_extractor_output_tokens = 0
            self.graph_extractor_total_tokens = 0

            self.description_summary_extractor_input_tokens = 0
            self.description_summary_extractor_output_tokens = 0
            self.description_summary_extractor_total_tokens = 0

            self.community_reports_extractor_input_tokens = 0
            self.community_reports_extractor_output_tokens = 0
            self.community_reports_extractor_total_tokens = 0

            self.embed_text_extractor_input_tokens = 0


    def _update_token_count(self, source: str, input_tokens: int, output_tokens: int = 0, total_tokens: int = 0) -> None:
        """Update the token count for a given source."""
        if source == "graph_extractor":
            self.graph_extractor_input_tokens += input_tokens
            self.graph_extractor_output_tokens += output_tokens
            self.graph_extractor_total_tokens += total_tokens
        elif source == "description_summary_extractor":
            self.description_summary_extractor_input_tokens += input_tokens
            self.description_summary_extractor_output_tokens += output_tokens
            self.description_summary_extractor_total_tokens += total_tokens
        elif source == "community_reports_extractor":
            self.community_reports_extractor_input_tokens += input_tokens
            self.community_reports_extractor_output_tokens += output_tokens
            self.community_reports_extractor_total_tokens += total_tokens
        elif source == "embed_text_extractor":
            self.embed_text_extractor_input_tokens += input_tokens

    def print_stats(self) -> None:
        """Log the total token counts for each LLM call type."""
        log.info(f"Graph Extractor - Input Tokens: {self.graph_extractor_input_tokens}")
        log.info(f"Graph Extractor - Output Tokens: {self.graph_extractor_output_tokens}")
        log.info(f"Graph Extractor - Total Tokens: {self.graph_extractor_total_tokens}")

        log.info(f"Description Summary Extractor - Input Tokens: {self.description_summary_extractor_input_tokens}")
        log.info(f"Description Summary Extractor - Output Tokens: {self.description_summary_extractor_output_tokens}")
        log.info(f"Description Summary Extractor - Total Tokens: {self.description_summary_extractor_total_tokens}")

        log.info(f"Community Reports Extractor - Input Tokens: {self.community_reports_extractor_input_tokens}")
        log.info(f"Community Reports Extractor - Output Tokens: {self.community_reports_extractor_output_tokens}")
        log.info(f"Community Reports Extractor - Total Tokens: {self.community_reports_extractor_total_tokens}")

        log.info(f"Embed Text Extractor - Input Tokens: {self.embed_text_extractor_input_tokens}")


    def get_token_counts(self) -> Dict[str, Dict[str, int]]:
        """Return token counts for each extraction method."""
        return {
            "graph_extractor": {
                "input_tokens": self.graph_extractor_input_tokens,
                "output_tokens": self.graph_extractor_output_tokens,
                "total_tokens": self.graph_extractor_total_tokens,
            },
            "description_summary_extractor": {
                "input_tokens": self.description_summary_extractor_input_tokens,
                "output_tokens": self.description_summary_extractor_output_tokens,
                "total_tokens": self.description_summary_extractor_total_tokens,
            },
            "community_reports_extractor": {
                "input_tokens": self.community_reports_extractor_input_tokens,
                "output_tokens": self.community_reports_extractor_output_tokens,
                "total_tokens": self.community_reports_extractor_total_tokens,
            },
            "embed_text_extractor": {
                "input_tokens": self.embed_text_extractor_input_tokens,
                "output_tokens": 0,  # Placeholder since we only track input tokens for embedding
                "total_tokens": self.embed_text_extractor_input_tokens,  # Same as input for this extractor
            },
        }
