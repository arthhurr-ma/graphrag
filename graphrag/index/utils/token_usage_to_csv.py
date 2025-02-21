import csv
import os
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path


log = logging.getLogger(__name__)

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
                documents = len(pd.read_parquet(os.path.join(root_dir, 'output', 'create_final_documents.parquet')))
                chunks = len(pd.read_parquet(os.path.join(root_dir, 'output', 'create_final_text_units.parquet')))
                relationships = len(pd.read_parquet(os.path.join(root_dir, 'output', 'create_final_relationships.parquet')))

                entities_df = pd.read_parquet(os.path.join(root_dir, 'output', 'create_final_entities.parquet'), columns=['type'])
                entities = entities_df.groupby("type").size().to_dict()  

                communities_df = pd.read_parquet(os.path.join(root_dir, 'output', 'create_final_communities.parquet'), columns=['title'])
                communities = communities_df.groupby("title").size().to_dict() 

                stats = token_counter.get_token_counts()
                chat_input_tokens = sum(stat["input_tokens"] for stat in stats.values())
                chat_output_tokens = sum(stat["output_tokens"] for stat in stats.values())
                chat_total_tokens = sum(stat["total_tokens"] for stat in stats.values())
                embedding_tokens = stats["embed_text_extractor"]["input_tokens"]
            
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


