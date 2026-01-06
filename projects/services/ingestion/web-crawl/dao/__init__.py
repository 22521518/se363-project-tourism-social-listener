"""DAO package for web crawl ingestion module."""
from .crawl_history_dao import CrawlHistoryDAO
from .crawl_result_dao import CrawlResultDAO
from .json_file_writer import JsonFileWriter

__all__ = [
    "CrawlHistoryDAO",
    "CrawlResultDAO",
    "JsonFileWriter",
]
