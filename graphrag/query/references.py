import re

import logging 
import pandas as pd
from typing import List, Set, Tuple, Optional
import os

# for future development need to deal with conversation history & maybe contextual references 

logger = logging.getLogger(__name__)


def text_unit_lookup(text_unit_ids: List[int], root_path: str) -> Set[str]:
    """Returns a set of document titles based on a list of text unit IDs."""
    documents_path = os.path.join(root_path, "output/documents.parquet")
    logger.debug(f"Looking up text units in: {documents_path}")
    try:
        documents_df = pd.read_parquet(documents_path)
        document_titles = set()
        
        for _, row in documents_df.iterrows():
            if any(text_unit_id in row['text_unit_ids'] for text_unit_id in text_unit_ids):
                document_titles.add(row['title'])

        if not document_titles:
            logger.info(f"No document titles found for text_unit_ids: {text_unit_ids}")
        else:
            logger.info(f"Found document titles for text_unit_ids {text_unit_ids}: {document_titles}")
        return document_titles
    except Exception as e:
        logger.exception(f"An error occurred in text_unit_lookup: {e}")  
        return set()


def entity_lookup(entity_indexes: List[int], root_path: str) -> List[Tuple[str, str, str, List[int], int]]:
    """Looks up entity details and returns a list of tuples (title, description, text_unit_ids)."""

    entities_path = os.path.join(root_path, "output/entities.parquet")
    logger.debug(f"Looking up entities in: {entities_path}")
    try:
        entities_df = pd.read_parquet(entities_path)
        results = []
        for idx in entity_indexes:
            if 0 <= idx < len(entities_df):
                row = entities_df.iloc[idx]
                results.append(("entity", row["title"], row["description"], row["text_unit_ids"], idx))
        logger.info(f"Found {len(results)} entities by index: {entity_indexes}")
        return results
    except Exception as e:
        logger.exception(f"An error occurred in entity_lookup: {e}")
        return []



def relationship_lookup(relationship_indexes: List[int], root_path: str) -> List[Tuple[str, str, str, List[int], int]]:
    """Looks up relationship details and returns a list of tuples (None, description, text_unit_ids)."""

    relationships_path = os.path.join(root_path, "output/relationships.parquet")
    logger.debug(f"Looking up relationships in: {relationships_path}")
    try:
        relationships_df = pd.read_parquet(relationships_path)
        results = []
        for idx in relationship_indexes:
            if 0 <= idx < len(relationships_df):
                row = relationships_df.iloc[idx]
                results.append(("relationship", None, row["description"], row["text_unit_ids"], idx))
        logger.info(f"Found {len(results)} relationships by index: {relationship_indexes}")
        return results
    except Exception as e:
        logger.exception(f"An error occurred in relationship_lookup: {e}")
        return []



def community_report_lookup(community_report_indexes: List[int], root_path: str) -> List[Tuple[str, str, str, List[int]]]:
    """Looks up community report details and returns a list of tuples (title, summary, text_unit_ids)."""
    community_reports_path = os.path.join(root_path, "output/community_reports.parquet")
    communities_path = os.path.join(root_path, "output/communities.parquet")
    logger.debug(f"Looking up community reports in: {community_reports_path}")
    try:
        community_reports_df = pd.read_parquet(community_reports_path)
        communities_df = pd.read_parquet(communities_path)
        results = []
        for idx in community_report_indexes:
            # Ensure we're looking up by index
            if 0 <= idx < len(community_reports_df):
                row = community_reports_df.iloc[idx]
                report_id = row["community"]
                title = row["title"]
                summary = row["summary"]

                community_row = communities_df[communities_df["community"] == report_id]

                if not community_row.empty:
                    text_unit_ids = community_row.iloc[0]["text_unit_ids"]
                else:
                    logger.warning(f"No matching community found for report ID {report_id}.")
                    text_unit_ids = []

                results.append(("community_report", title, summary, text_unit_ids, idx))

        logger.info(f"Found {len(results)} community reports by index: {community_report_indexes}")
        return results
    except FileNotFoundError:
        logger.error(f"Error: File not found at {community_reports_path}")
        return []
    except Exception as e:
        logger.exception(f"An error occurred in community_report_lookup: {e}")



def find_document_path(doc_title: str, root_path: str) -> Optional[str]:
    """Searches for the document in all subfolders and returns the path if found."""
    for dirpath, _, filenames in os.walk(os.path.join(root_path, "input")):
        for filename in filenames:
            if doc_title in filename:
                doc_path = os.path.join(dirpath, filename)
                return f"{doc_path}"
    logger.warning(f"Document {doc_title} not found in any subfolder.")
    return None



def in_text_references(query: str, root_path: str) -> Optional[str]:
    """Extracts references from the query and returns a DataFrame."""
    logger.info(f"Extracting in-text references from query: {query}")
    references: List[Tuple[str, Optional[str], str, List[int]]] = []


    reference_pattern = r"\[Data:\s*((?:Entities|Relationships|Reports)\s*\(\d+(?:,\s*\d+)*\)(?:;\s*(?:Entities|Relationships|Reports)\s*\(\d+(?:,\s*\d+)*\))*)\]"
    matches = re.findall(reference_pattern, query)

    logger.info(f"Found {len(matches)} references in the query: {matches}")
   
    unique_matches = {'Reports': set(), 'Entities': set(), 'Relationships': set()}
    for match in matches:
        for key in unique_matches.keys():
            numbers = re.findall(f'{key} \(([\d, ]+)\)', match)
            if numbers:
                unique_matches[key].update([int(num) for num in numbers[0].split(',')])

    logger.info(f"Unique references: {unique_matches}")

    if unique_matches['Entities']:
        entities = entity_lookup(unique_matches['Entities'], root_path)
        references.extend(entities)
    if unique_matches['Relationships']:
        relationships = relationship_lookup(unique_matches['Relationships'], root_path)
        references.extend(relationships)
    if unique_matches['Reports']:
        community_reports = community_report_lookup(unique_matches['Reports'], root_path)
        references.extend(community_reports)
   
    unique_document_references: Set[str] = set()
    
    df = pd.DataFrame(columns=["type of reference", "index", "title", "description", "document_title"])
    all_text_unit_ids: List[int] = []

    for ref_type, title, description, text_unit_ids, index in references:
        all_text_unit_ids = text_unit_ids  
        logger.info(f"Looking up document titles for text_unit_ids: {all_text_unit_ids}")
        document_titles = text_unit_lookup(all_text_unit_ids, root_path)  
        logger.info(f"Found document titles: {document_titles} for reference {title}")
 
    
        for doc_title in document_titles:

            doc_link = find_document_path(doc_title, root_path)
            if doc_link:
                reference_string = f"Reference: {doc_title}, Document: {doc_link}" 
                unique_document_references.add(reference_string)

            new_row = pd.DataFrame([{
                "type of reference": ref_type,
                "index": index,
                "title": title,
                "description": description,
                "document_title": doc_title,
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)

    df.drop_duplicates(inplace=True)
    output_dir = os.path.join(root_path, "output/references")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "in_text_citations.csv")
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"References successfully written to {output_path}")
    else:
        logger.info("No references found, no CSV written.")

    results_str = "\n".join(sorted(unique_document_references))

    if results_str:
        logger.info(f"Returning non-empty results string, {results_str}")
        return results_str
    else:
        logger.info("Results string is empty, returning None.")
        return None
