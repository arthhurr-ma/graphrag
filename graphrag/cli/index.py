# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the index subcommand."""

import asyncio
import logging
import sys
import time
import warnings
from pathlib import Path

import graphrag.api as api
from graphrag.config.enums import CacheType
from graphrag.config.load_config import load_config
from graphrag.logger.callback import Token_Callback
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.validate_config import validate_config_names
from graphrag.config.logging import enable_logging_with_config, enable_logging
from graphrag.logger.base import ProgressLogger
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.utils.cli import redact

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


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
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    dry_run: bool,
    skip_validation: bool,
    output_dir: Path | None,
    logging_enabled: bool,  
    log_path: str,  

):
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    progress_logger = LoggerFactory().create_logger(logger, method="index")

    _run_index(
        config=config,
        verbose=verbose,
        resume=resume,
        memprofile=memprofile,
        cache=cache,
        logger=progress_logger,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output_dir,
        logging_enabled=logging_enabled,  
        log_path=log_path, 
    )


def update_cli(
    root_dir: Path,
    verbose: bool,
    memprofile: bool,
    cache: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    skip_validation: bool,
    output_dir: Path | None,
    logging_enabled: bool,  
    log_path: str,
):
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)
    progress_logger = LoggerFactory().create_logger(logger, method="update")


    logging_enabled, log_path = enable_logging_with_config(config, root_dir, method="update")


    # Check if update storage exist, if not configure it with default values
    if not config.update_index_storage:
        from graphrag.config.defaults import STORAGE_TYPE, UPDATE_STORAGE_BASE_DIR
        from graphrag.config.models.storage_config import StorageConfig

        config.update_index_storage = StorageConfig(
            type=STORAGE_TYPE,
            base_dir=UPDATE_STORAGE_BASE_DIR,
        )

    _run_index(
        config=config,
        verbose=verbose,
        resume=False,
        memprofile=memprofile,
        cache=cache,
        logger=progress_logger,
        dry_run=False,
        skip_validation=skip_validation,
        output_dir=output_dir,
        logging_enabled=logging_enabled,  
        log_path=log_path, 
    )


def _run_index(
    config,
    verbose,
    resume,
    memprofile,
    cache,
    logger,
    dry_run,
    skip_validation,
    output_dir,
    logging_enabled, 
    log_path, 
):
    info, error, success = _logger(logger)
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    log.info(f"Type of config: {type(config)}")
    log.info(f"config: {config}")

    # Check if output_dir is a valid path
    if output_dir is not None and not isinstance(output_dir, Path):
        try:
            output_dir = Path(output_dir)  # Try converting to Path
        except TypeError:
            raise TypeError("output_dir parameter must be a valid string or Path object.")

    # Ensure config.storage is not None and .base_dir is a string before conversion
    if hasattr(config, "storage") and config.storage and isinstance(config.storage.base_dir, (str, Path)):
        config.storage.base_dir = str(output_dir) if output_dir else str(config.storage.base_dir)  # Convert Path to str
    else:
        config.storage.base_dir = str(output_dir) if output_dir else ""

    # Ensure config.reporting is not None and .base_dir is a string before conversion
    if hasattr(config, "reporting") and config.reporting and isinstance(config.reporting.base_dir, (str, Path)):
        config.reporting.base_dir = (str(output_dir) if output_dir else str(config.reporting.base_dir) 
        )
    else:
        config.reporting.base_dir = str(output_dir) if output_dir else ""

    # Log resolved paths and their types for verification
    log.info(f"config.storage.base_dir: {config.storage.base_dir}, type: {type(config.storage.base_dir)}")
    log.info(f"config.reporting.base_dir: {config.reporting.base_dir}, type: {type(config.reporting.base_dir)}")    
    
    resolve_paths(config, run_id)

    if not cache:
        config.cache.type = CacheType.none

    log.info("Before enable_logging_with_config") 
    log.info(f"config.reporting.base_dir: {config.reporting.base_dir}, type: {type(config.reporting.base_dir)}")

    root_dir = Path("./scalingtest")
    enabled_logging, log_path = enable_logging_with_config(config, root_dir, method="index")
    log.info("After enable_logging_with_config") 
    if enabled_logging:
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {redact(config.model_dump())}",
            True,
        )
    log.info("Before skip_validation check")
    if skip_validation:
        validate_config_names(logger, config)
    log.info("After skip_validation check")

    info(f"Starting pipeline run for: {run_id}, {dry_run=}", verbose)
    info(
        f"Using default configuration: {redact(config.model_dump())}",
        verbose,
    )

    if dry_run:
        info("Dry run complete, exiting...", True)
        sys.exit(0)

    token_callback = Token_Callback()
    _register_signal_handlers(logger)

    outputs = asyncio.run(
        api.build_index(
            config=config,
            run_id=run_id,
            is_resume_run=bool(resume),
            memory_profile=memprofile,
            progress_logger=logger,
            token_callback=token_callback.extract_and_aggregate
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

    token_callback.print_stats()

    sys.exit(1 if encountered_errors else 0)
