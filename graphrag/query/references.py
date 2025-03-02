import pandas as pd
import re
from typing import List, Set, Dict, Union

# for future development need to deal with conversation history 

# this needs to be gerneralizable for 4 functions below, should be able to retrieve text_unit_ids 
def _extract_ids_from_table_string(table_string: str) -> List[str]:
    """Extracts IDs from a pipe-delimited table string (first column)."""
    ids = []
    lines = table_string.strip().split('\n')
    if len(lines) > 1:  
        for line in lines[1:]:  
            try:
                unit_id, _ = line.split('|', 1)  
                ids.append(unit_id)
            except ValueError:
                print(f"Warning: Could not parse line: {line}")
                continue  
    return ids



def text_unit_lookup(text_unit_ids: List[Union[str, int]], df_text_units: pd.DataFrame) -> Set[int]:
    """Looks up text_unit_ids in the text units DataFrame and returns a set of matching text_unit_ids (as integers)."""
    casted_ids = []    
    for unit_id in text_unit_ids:
        try:
            casted_ids.append(int(unit_id))
        except ValueError:
            print(f"Warning: Invalid text_unit_id: {unit_id}. Skipping.")
            continue 

return set(df_text_units[df_text_units['text_unit_id'].isin(casted_ids)]['text_unit_id'].tolist())



def entity_lookup(entity_ids: List[str], df_entities: pd.DataFrame) -> Set[int]:
    """Looks up entity_ids in the entities DataFrame and returns a set of associated text_unit_ids (as integers)."""
    text_unit_ids = set()
    for entity_id in entity_ids:
        matching_rows = df_entities[df_entities['short_id'] == entity_id] 
        for _, row in matching_rows.iterrows():
            text_unit_ids_str = row['text_unit_ids']
            if pd.notna(text_unit_ids_str) and isinstance(text_unit_ids_str, str):
                try: 
                    ids = eval(text_unit_ids_str) # Safely evaluate string as list
                    if isinstance(ids, list):
                        text_unit_ids.update(int(i) for i in ids) # Ensure int
                except (SyntaxError, NameError, TypeError):
                    print(f"Warning: Could not parse text_unit_ids for entity {entity_id}: {text_unit_ids_str}")
                    # Skip the entity if we can not parse text_unit_ids    return text_unit_ids


def relationship_lookup(relationship_ids: List[str], df_relationships: pd.DataFrame) -> Set[int]:
    """Looks up relationship_ids in the relationships DataFrame, finds associated entities,
       and returns a set of text_unit_ids (from those entities).
    """
    text_unit_ids = set()
    for rel_id in relationship_ids:
        matching_rows = df_relationships[df_relationships['short_id'] == rel_id]  # Assuming 'short_id'
        for _, row in matching_rows.iterrows():
            #get the entities attached to this rel
            source = row["source"]
            target = row["target"]


        #now look up these source and target entities in the entity dataframe to extact the text units
        matching_entities = df_entities[(df_entities['title'] == source) | (df_entities['title'] == target)]
        for _, entity_row in matching_entities.iterrows():
             # Handle cases where text_unit_ids might be a string representation of a list or nan
            text_unit_ids_str = entity_row['text_unit_ids']
            if pd.notna(text_unit_ids_str) and isinstance(text_unit_ids_str, str):
                try:
                    ids = eval(text_unit_ids_str)
                    if isinstance(ids, list):                            
                    text_unit_ids.update(int(i) for i in ids)  # Ensure int, add to set
                except (SyntaxError, NameError, TypeError):
                    print(f"Warning: Could not parse text_unit_ids for relationship {rel_id}, entity: {entity_row['title']}")

return text_unit_ids



def community_report_lookup(community_report_ids: List[str], df_community_reports: pd.DataFrame) -> Set[int]:
    """Looks up community_report_ids in the community reports DataFrame, finds associated entities,
       and returns a set of text_unit_ids (from those entities).
    """
    text_unit_ids = set()
    for comm_id in community_report_ids:
        matching_rows = df_community_reports[df_community_reports['short_id'] == comm_id] # Assuming short_id
        for _, row in matching_rows.iterrows():
            #get the entities attached to this community
            title = row["title"]


        #find matching entities in entities dataframe
        matching_entities = df_entities[(df_entities['title'] == title)]
        for _, entity_row in matching_entities.iterrows():
            # Handle cases where text_unit_ids might be a string representation of a list
            text_unit_ids_str = entity_row['text_unit_ids']
            if pd.notna(text_unit_ids_str) and isinstance(text_unit_ids_str, str):
                try:
                    ids = eval(text_unit_ids_str)
                    if isinstance(ids, list):
                        text_unit_ids.update(int(i) for i in

 ids)  # Ensure int
                    except (SyntaxError, NameError, TypeError):
                        print(f"Warning: Could not parse text_unit_ids for community {comm_id}, entity: {entity_row['title']}")
    return text_unit_ids




def retrieve_reference_ids(method: str, context_data: 'ContextBuilderResult',
                           df_entities: pd.DataFrame, df_relationships: pd.DataFrame,
                           df_community_reports: pd.DataFrame, df_text_units: pd.DataFrame) -> Set[int]:
    """Retrieves all relevant text_unit_ids based on the context building method."""


all_text_unit_ids: Set[int] = set()

if method == "basic":
    context_string = context_data.context_chunks
    text_unit_ids = _extract_ids_from_table_string(context_string)
    all_text_unit_ids.update(text_unit_lookup(text_unit_ids, df_text_units))

elif method == "local":
    context_records = context_data.context_records

    # --- Entities ---
    if 'entities' in context_records and not context_records['entities'].empty:
        entity_ids = _extract_ids_from_table_string(context_data.context_chunks.split("-----Entities-----")[1].split("-----")[0])
        all_text_unit_ids.update(entity_lookup(entity_ids, df_entities))

    # --- Relationships ---
    if 'relationships' in context_records and not context_records['relationships'].empty :
        relationship_ids = _extract_ids_from_table_string(context_data.context_chunks.split("-----Relationships-----")[1].split("-----")[0])
        all_text_unit_ids.update(relationship_lookup(relationship_ids, df_relationships))

    # --- Community Reports ---
    if 'reports' in context_records and not context_records['reports'].empty:
        community_ids = _extract_ids_from_table_string(context_data.context_chunks.split("-----Reports-----")[1].split("-----")[0])
        all_text_unit_ids.update(community_report_lookup(community_ids, df_community_reports))
    # --- Text Units ---
    if 'sources' in context_records and not context_records['sources'].empty:
        text_unit_ids = _extract_ids_from_table_string(context_data.context_chunks.split("-----Sources-----")[1].split("-----")[0])
        all_text_unit_ids.update(text_unit_lookup(text_unit_ids, df_text_units))


else:
    raise ValueError(f"Unsupported method: {method}")

return all_text_unit_ids






def in_text_references():
    
    #pass in the context data
    #perform lookups to get references to the context data
    
    pass    