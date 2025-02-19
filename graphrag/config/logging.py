# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities. A unified way for enabling logging."""

import logging
from pathlib import Path
from datetime import datetime

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig

log = logging.getLogger(__name__)


def enable_logging(log_filepath: str | Path) -> None:
    """Enable logging to a file.

    Parameters
    ----------
    log_filepath : str | Path
        The path to the log file.
    """
    log_filepath = Path(log_filepath)
    try:
        log_filepath.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        log_filepath.touch(exist_ok=True)  # Create file if it doesn't exist
    except OSError as e:
        log.error(f"Error creating log file or directory: {e}")
        return  # Or raise the exception if you prefer

    try:
        logging.basicConfig(
            filename=log_filepath,
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
        )
    except Exception as e:
        log.error("Error with enable logging")
        return


def enable_logging_with_config(config: GraphRagConfig, method: str) -> tuple[bool, str]:
    """Enable logging dynamically based on the method (index, update, query) and config."""

    config.reporting.base_dir = "logs"

    if config.reporting.type == ReportingType.file:

        if method == "index":
            log_subdir = "index"
        elif method == "update":
            log_subdir = "update"
        elif method == "query":
            log_subdir = "query"       
        else:
            log.error(f"Invalid method: {method}")
            return False, ""  

        log_dir = Path(config.reporting.base_dir) / log_subdir
        log.info(f"log_dir: {log_dir}, type: {type(log_dir)}")
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"Created log directory: {log_dir}")
        except OSError as e:
            log.error(f"Error creating log directory: {e}")
            return False, ""

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_name = f"{method}_{timestamp}.log"
        log_filepath = log_dir / log_file_name
        log.info(f"log_filepath: {log_filepath}, type: {type(log_filepath)}")
    else:
        log.error("Reporting type is not 'file', returning False")
        return False, ""


    enable_logging(log_filepath)
    log.debug(f"Logging to file enabled: {log_filepath}")
    return True, str(log_filepath)
   
