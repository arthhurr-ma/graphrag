import logging 
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict


log = logging.getLogger(__name__)

class Token_Callback():
    def init(self):
        """A class to aggregate token usage from various LLM calls."""
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
        self.embed_text_extractor_output_tokens = 0
        self.embed_text_extractor_total_tokens = 0


    def extract_and_aggregate(self, metrics: Dict[str, Any], source: str) -> None:
        """Extract and aggregate token usage from a structured metrics object."""
        try:
            if source == "graph_extractor":
                input_tokens, output_tokens, total_tokens = self._extract_tokens(metrics)
                self._update_token_count("graph_extractor", input_tokens, output_tokens, total_tokens)

            elif source == "description_summary_extractor":
                input_tokens, output_tokens, total_tokens = self._extract_tokens(metrics)
                self._update_token_count("description_summary_extractor", input_tokens, output_tokens, total_tokens)

            elif source == "community_reports_extractor":
                input_tokens, output_tokens, total_tokens = self._extract_tokens(metrics)
                self._update_token_count("community_reports_extractor", input_tokens, output_tokens, total_tokens)

            elif source == "embed_text":
                # Handle embedding tokens differently, as they may not have output tokens
                input_tokens, output_tokens, total_tokens = self._extract_embedding_tokens(metrics)
                self._update_token_count("embed_text_extractor", input_tokens, output_tokens, total_tokens)

            else:
                log.warning(f"Unrecognized source: {source}")

        except Exception as e:
            log.error(f"Error extracting tokens from source: {source}. Error: {e}")

    def _extract_tokens(self, metrics: Dict[str, Any]) -> tuple[int, int, int]:
        """Extract input, output, and total tokens from a metrics object."""
        try:
            usage = metrics.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            return input_tokens, output_tokens, total_tokens
        except Exception as e:
            log.error(f"Error extracting token counts: {e}")
            return 0, 0, 0


    def _extract_embedding_tokens(self, metrics: Dict[str, Any]) -> tuple[int, int, int]:
        """Extract input, output, and total tokens from a metrics object for embeddings."""
        try:
            input_tokens = metrics.get("estimated_input_tokens", 0)
            # For embeddings, often output tokens are not directly available
            return input_tokens, 0, input_tokens
        except Exception as e:
            log.error(f"Error extracting embedding token counts: {e}")
            return 0, 0, 0  

    def _update_token_count(self, source: str, input_tokens: int, output_tokens: int, total_tokens: int) -> None:
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
            self.embed_text_extractor_output_tokens += output_tokens
            self.embed_text_extractor_total_tokens += total_tokens

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
        log.info(f"Embed Text Extractor - Output Tokens: {self.embed_text_extractor_output_tokens}")
        log.info(f"Embed Text Extractor - Total Tokens: {self.embed_text_extractor_total_tokens}")
