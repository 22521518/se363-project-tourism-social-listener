"""
Export Utilities for ASCA.

Functions to export approved records to CSV format for training.
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def export_approved_to_csv(
    dao,
    output_path: str,
    limit: int = 10000
) -> int:
    """
    Export approved ASCA records to CSV for model training.
    
    Args:
        dao: ASCAExtractionDAO instance
        output_path: Path to output CSV file
        limit: Maximum records to export
        
    Returns:
        Number of records exported
    """
    from projects.services.processing.tasks.asca.dto import CategoryType, SentimentType
    
    approved_records = dao.get_approved(limit=limit)
    
    if not approved_records:
        logger.warning("No approved records to export")
        return 0
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header matching ASCA training format
        writer.writerow(['comment', 'category', 'sentiment'])
        
        for record in approved_records:
            # Use approved_result if available, otherwise use extraction_result
            if record.approved_result:
                aspects = record.approved_result.get('aspects', [])
            else:
                aspects = [a.model_dump() for a in record.extraction_result.aspects]
            
            # Write one row per aspect
            for aspect in aspects:
                category = aspect.get('category', 'SERVICE')
                sentiment = aspect.get('sentiment', 'neutral')
                
                writer.writerow([record.raw_text, category, sentiment])
                exported_count += 1
    
    logger.info(f"Exported {exported_count} aspect records to {output_path}")
    return exported_count


def export_for_training(
    dao,
    output_dir: str,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    limit: int = 10000
) -> dict:
    """
    Export approved records split into train/val/test CSV files.
    
    Args:
        dao: ASCAExtractionDAO instance
        output_dir: Directory for output files
        train_ratio: Proportion for training set
        val_ratio: Proportion for validation set
        test_ratio: Proportion for test set
        limit: Maximum records to export
        
    Returns:
        Dictionary with counts for each split
    """
    import random
    
    approved_records = dao.get_approved(limit=limit)
    
    if not approved_records:
        logger.warning("No approved records to export")
        return {"train": 0, "val": 0, "test": 0}
    
    # Shuffle records
    random.shuffle(approved_records)
    
    # Split indices
    n = len(approved_records)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    train_records = approved_records[:train_end]
    val_records = approved_records[train_end:val_end]
    test_records = approved_records[val_end:]
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export each split
    def write_split(records, filename):
        filepath = output_path / filename
        count = 0
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['comment', 'category', 'sentiment'])
            
            for record in records:
                if record.approved_result:
                    aspects = record.approved_result.get('aspects', [])
                else:
                    aspects = [a.model_dump() for a in record.extraction_result.aspects]
                
                for aspect in aspects:
                    writer.writerow([
                        record.raw_text,
                        aspect.get('category', 'SERVICE'),
                        aspect.get('sentiment', 'neutral')
                    ])
                    count += 1
        
        return count
    
    result = {
        "train": write_split(train_records, "train.csv"),
        "val": write_split(val_records, "val.csv"),
        "test": write_split(test_records, "test.csv")
    }
    
    logger.info(f"Exported splits to {output_dir}: {result}")
    return result


def export_with_timestamp(
    dao,
    output_dir: str = "data/exports",
    limit: int = 10000
) -> str:
    """
    Export approved records with timestamp in filename.
    
    Args:
        dao: ASCAExtractionDAO instance
        output_dir: Base directory for exports
        limit: Maximum records to export
        
    Returns:
        Path to exported file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"approved_{timestamp}.csv"
    
    export_approved_to_csv(dao, str(output_path), limit)
    
    return str(output_path)
