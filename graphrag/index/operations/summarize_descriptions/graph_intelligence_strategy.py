# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_graph_intelligence,  run_resolve_entities and _create_text_list_splitter methods to run graph intelligence."""

from fnllm import ChatLLM
from typing import Any, Callable, Dict
import logging

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.llm.load_llm import load_llm, read_llm_params
from graphrag.index.operations.summarize_descriptions.description_summary_extractor import (
    SummarizeExtractor,
)
from graphrag.index.operations.summarize_descriptions.typing import (
    StrategyConfig,
    SummarizedDescriptionResult,
)


log = logging.getLogger(__name__)

async def run_graph_intelligence(
    id: str | tuple[str, str],
    descriptions: list[str],
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    args: StrategyConfig,
    token_callback: Callable[[Dict[str, int]], None] = None,
) -> SummarizedDescriptionResult:
    """Run the graph intelligence entity extraction strategy."""

    log.debug(f"run_graph_intelligence_SD called with token_callback: {token_callback}")

    llm_config = read_llm_params(args.get("llm", {}))
    llm = load_llm(
        "summarize_descriptions", llm_config, callbacks=callbacks, cache=cache
    )
    return await run_summarize_descriptions(llm, id, descriptions, callbacks, args)


async def run_summarize_descriptions(
    llm: ChatLLM,
    id: str | tuple[str, str],
    descriptions: list[str],
    callbacks: WorkflowCallbacks,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the entity extraction chain."""
    # Extraction Arguments
    summarize_prompt = args.get("summarize_prompt", None)
    entity_name_key = args.get("entity_name_key", "entity_name")
    input_descriptions_key = args.get("input_descriptions_key", "description_list")
    max_tokens = args.get("max_tokens", None)

    extractor = SummarizeExtractor(
        llm_invoker=llm,
        summarization_prompt=summarize_prompt,
        entity_name_key=entity_name_key,
        input_descriptions_key=input_descriptions_key,
        on_error=lambda e, stack, details: (
            callbacks.error("Entity Extraction Error", e, stack, details)
            if callbacks
            else None
        ),
        max_summary_length=args.get("max_summary_length", None),
        max_input_tokens=max_tokens,
    )

    result = await extractor(id=id, descriptions=descriptions)

    if hasattr(result, 'token_counts'):
        # If token counts are available, log them
        log.info(f"Token Usage for Summarizing {id}: {result.token_counts}")
    else:
        # If token counts are not available, log input/output estimates
        input_tokens = sum(len(description.split()) for description in descriptions)
        output_tokens = len(result.description.split()) if result.description else 0
        total_tokens = input_tokens + output_tokens
        
        log.info(f"Summarizing {id}: Input token count = {input_tokens}")
        log.info(f"Summarizing {id}: Output token count = {output_tokens}")
        log.info(f"Summarizing {id}: Total token count = {total_tokens}")

    return SummarizedDescriptionResult(id=result.id, description=result.description)
