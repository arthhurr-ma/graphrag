# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging utilities. A unified way for enabling logging."""

import logging
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.graph_rag_config import GraphRagConfig

log = logging.getLogger(__name__)


def enable_logging(log_filepath: str | Path, verbose: bool = False) -> None:
    """Enable logging to a file.

    Parameters
    ----------
    log_filepath : str | Path
        The path to the log file.
    verbose : bool, default=False
        Whether to log debug messages.
    """
    log_filepath = Path(log_filepath)
    try:
        log_filepath.parent.mkdir(parents=True, exist_ok=True)  
        log_filepath.touch(exist_ok=True) 
    except OSError as e:        
        log.error(f"Error creating log file or directory: {e}")
        raise

    try:
        logging.basicConfig(
            filename=log_filepath,
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG if verbose else logging.INFO,
        )
    except Exception as e:
        log.error("Error with enable logging")
        raise

def enable_logging_with_config(
    config: GraphRagConfig, 
    root_dir: Path,
    method: str
) -> tuple[bool, str]:
    """Enable logging to a file based on the config.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    timestamp_value : str
        The timestamp value representing the directory to place the log files.
    verbose : bool, default=False
        Whether to log debug messages.

    Returns
    -------
    tuple[bool, str]
        A tuple of a boolean indicating if logging was enabled and the path to the log file.
        (False, "") if logging was not enabled.
        (True, str) if logging was enabled.
    """

    if config is None:
        log.debug("Config is None, returning False")
        return False, ""

    if not isinstance(root_dir, Path):
        log.error("root_dir must be a Path object")
        return False, "" 

    if config.reporting.type == ReportingType.file:
        log_dir = root_dir / "logs" / method
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

        enable_logging(log_filepath, verbose=True)
        log.info(f"Logging to file enabled: {log_filepath}")
        return True, str(log_filepath)

    log.info("Reporting type is not 'file', returning False")
    return (False, "")
