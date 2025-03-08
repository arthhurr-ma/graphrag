# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the index subcommand."""

import asyncio
import logging
import sys
import warnings
from typing import Optional
import csv
from pathlib import Path

import graphrag.api as api
from graphrag.config.enums import CacheType, IndexingMethod
from graphrag.config.load_config import load_config
from graphrag.config.logging import enable_logging_with_config, enable_logging
from graphrag.callbacks.token_counter import Token_Counter 
from graphrag.index.utils.token_usage_to_csv import export_token_stats_to_csv
from graphrag.index.validate_config import validate_config_names
from graphrag.logger.base import ProgressLogger
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


token_counter = Token_Counter()

def _logger(logger: ProgressLogger):
    def info(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.info(msg)

    def error(msg: str, verbose: bool = False):
        log.error(msg)
        if verbose:
            logger.error(msg)

    def success(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.success(msg)

    return info, error, success


def _register_signal_handlers(logger: ProgressLogger):
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        logger.info(f"Received signal {signum}, exiting...")  # noqa: G004
        logger.dispose()
        for task in asyncio.all_tasks():
            task.cancel()
        logger.info("All tasks cancelled. Exiting...")

    # Register signal handlers for SIGINT and SIGHUP
    signal.signal(signal.SIGINT, handle_signal)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, handle_signal)


def index_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    dry_run: bool,
    skip_validation: bool,
    output_dir: Path | None,
    logging_enabled: bool,  
    log_path: str,
    index_method: str,
):
    """Run the pipeline with the given config."""
    cli_overrides = {}
    if output_dir:
        cli_overrides["output.base_dir"] = str(output_dir)
        cli_overrides["reporting.base_dir"] = str(output_dir)
        cli_overrides["update_index_output.base_dir"] = str(output_dir)
    config = load_config(root_dir, config_filepath, cli_overrides)
    logging_enabled, log_path = enable_logging_with_config(config, index_method="index", verbose=verbose)

    _run_index(
        config=config,
        method=method,
        is_update_run=False,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=logger,
        dry_run=dry_run,
        skip_validation=skip_validation,
        logging_enabled=logging_enabled,  
        log_path=log_path,
        index_method="index",
    )


def update_cli(
    root_dir: Path,
    method: IndexingMethod,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    skip_validation: bool,
    output_dir: Path | None,
    logging_enabled: bool,  
    log_path: str,
    index_method: str,  
):
    """Run the pipeline with the given config."""
    cli_overrides = {}
    if output_dir:
        cli_overrides["output.base_dir"] = str(output_dir)
        cli_overrides["reporting.base_dir"] = str(output_dir)
        cli_overrides["update_index_output.base_dir"] = str(output_dir)

    config = load_config(root_dir, config_filepath, cli_overrides)
    logging_enabled, log_path = enable_logging_with_config(config, index_method="update", verbose=verbose)

    _run_index(
        config=config,
        method=method,
        is_update_run=True,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=logger,
        dry_run=False,
        skip_validation=skip_validation,
        logging_enabled=logging_enabled,  
        log_path=log_path,
        index_method="update",
    )


def _run_index(
    config,
    method,
    is_update_run,
    verbose,
    memprofile,
    cache,
    logger: LoggerType,
    dry_run,
    skip_validation,
    logging_enabled,
    log_path,
    index_method,
):
    progress_logger = LoggerFactory().create_logger(logger)
    info, error, success = _logger(progress_logger)

    if not cache:
        config.cache.type = CacheType.none

    enabled_logging, log_path = enable_logging_with_config(config, index_method=index_method, verbose=verbose)
    if enabled_logging:
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {redact(config.model_dump())}",
            True,
        )

    if not skip_validation:
        validate_config_names(progress_logger, config)

    info(f"Starting pipeline run. {dry_run=}", verbose)
    info(
        f"Using default configuration: {redact(config.model_dump())}",
        verbose,
    )

    if dry_run:
        info("Dry run complete, exiting...", True)
        sys.exit(0)

    _register_signal_handlers(progress_logger)

    outputs = asyncio.run(
        api.build_index(
            config=config,
            method=method,
            is_update_run=is_update_run,
            memory_profile=memprofile,
            progress_logger=progress_logger,
        )
    )
    encountered_errors = any(
        output.errors and len(output.errors) > 0 for output in outputs
    )

    progress_logger.stop()
    if encountered_errors:
        error(
            "Errors occurred during the pipeline run, see logs for more details.", True
        )
    else:
        success("All workflows completed successfully.", True)
        token_counter.print_stats()
        try:
            export_token_stats_to_csv(token_counter, config.root_dir)
        except Exception as e:
            log.error(f"Error during export_token_stats_to_csv process: {e}")
        raise 

    sys.exit(1 if encountered_errors else 0)
