import csv
import os
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path


log = logging.getLogger(__name__)


# check for update file 
def load_parquet_data(base_dir: str, file_path: str) -> pd.DataFrame:

    update_output_dir = os.path.join(base_dir, "update_output")

    if os.path.isdir(update_output_dir):
        full_path = os.path.join(update_output_dir, file_path)
    else:
        full_path = os.path.join(base_dir, "output", file_path)

    try:
        return pd.read_parquet(full_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Parquet file not found: {full_path}")
    except Exception as e:
        raise Exception(f"Error reading parquet: {full_path}: {e}")


def export_token_stats_to_csv(token_counter, root_dir):

    try:
        token_directory = os.path.join(root_dir, "logs", "token_counts_index")
        Path(token_directory).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        csv_file_path = os.path.join(token_directory, f"token_stats_scaling_experiment.csv")

        headers = [
        "Batch", 
        "Documents", 
        "Chunks", 
        "Chat Input Tokens", 
        "Chat Output Tokens", 
        "Chat Total Tokens", 
        "Embedding Tokens",
        "Number of Entities (array based on type)", 
        "Number of Relationships", 
        "Number of Communities (array based on Community Level)"
        ]
        
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            try:
                documents = load_parquet_data(root_dir, find_parquet_file(root_dir, 'documents.parquet'))
                chunks = load_parquet_data(root_dir, find_parquet_file(root_dir, 'text_units.parquet'))
                relationships = load_parquet_data(root_dir, find_parquet_file(root_dir, 'relationships.parquet'))

                entities_df = load_parquet_data(root_dir, find_parquet_file(root_dir, 'entities.parquet'))
                entities = entities_df.groupby("type").size().to_dict() if 'type' in entities_df.columns else {}

                communities_df = load_parquet_data(root_dir, find_parquet_file(root_dir, 'communities.parquet'))
                communities = communities_df.groupby("level").size().to_dict() if 'level' in communities_df.columns else {}


                stats = token_counter.get_token_counts()
                chat_input_tokens = sum(stat["input_tokens"] for stat in stats.values())
                chat_output_tokens = sum(stat["output_tokens"] for stat in stats.values())
                chat_total_tokens = sum(stat["total_tokens"] for stat in stats.values())
                embedding_tokens = stats["embed_text_extractor"]["embedding_tokens"]
            
            except Exception as e:
                log.error(f"Error gathering token counts or reading parquet files: {e}")
                raise

            row = [
                timestamp,  
                documents,  
                chunks,  
                chat_input_tokens,  
                chat_output_tokens,  
                chat_total_tokens,  
                embedding_tokens,  
                entities,  
                relationships,  
                communities  
            ]
           
            writer.writerow(row)

        log.info(f"Token statistics exported to: {csv_file_path}")
    
    except Exception as e:
        log.error(f"Error during export process: {e}")
        raise

def find_parquet_file(root_dir, file_name):
    """New version of graphrag doesnt include 'create_final_' in parquet write."""
    file_path = os.path.join(root_dir, file_name)
    
    if not os.path.exists(file_path):
        file_name_with_prefix = f"create_final_{file_name}"
        file_path = os.path.join(root_dir, file_name_with_prefix)
    
    return file_path