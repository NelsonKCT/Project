import pandas as pd
import hashlib
import os
import json
import importlib.util
import subprocess
from typing import List, Dict, Tuple, Set, Any
import numpy as np

def load_excel_data(file_path: str) -> pd.DataFrame:
    """
    Load Excel file into a pandas DataFrame
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {str(e)}")

def compute_record_hash(record: pd.Series, id_columns: List[str]) -> int:
    """
    Compute a hash of the record's identifier columns
    """
    # Concatenate values from id columns
    id_values = [str(record[col]) for col in id_columns]
    id_string = "_".join(id_values)
    
    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(id_string.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert to integer (using last 16 bytes to avoid overflows)
    hash_int = int(hash_hex[-16:], 16)
    return hash_int

def compute_blinded_hash(hash_int: int, private_key: int, prime: int) -> int:
    """
    Compute h^(private_key) mod prime
    """
    return pow(hash_int, private_key, prime)

def process_dataset(df: pd.DataFrame, id_columns: List[str], private_key: int, prime: int) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:
    """
    Process dataset to compute hashes and blinded values
    Returns:
    - h_to_c_map: mapping from original hash to blinded hash
    - h_to_record_map: mapping from original hash to original record
    """
    h_to_c_map = {}
    h_to_record_map = {}
    
    for _, record in df.iterrows():
        h = compute_record_hash(record, id_columns)
        c = compute_blinded_hash(h, private_key, prime)
        h_to_c_map[h] = c
        h_to_record_map[h] = record
    
    return h_to_c_map, h_to_record_map

def save_values_to_excel(values: List[int], output_file: str, column_name: str = "Value"):
    """
    Save a list of values to Excel file
    """
    df = pd.DataFrame({column_name: values})
    df.to_excel(output_file, index=False)

def save_values_to_json(values: List[int], output_file: str):
    """
    Save a list of values to JSON file (more efficient for large numbers)
    """
    with open(output_file, 'w') as f:
        json.dump(values, f)

def load_values_from_excel(input_file: str, column_name: str = "Value") -> List[int]:
    """
    Load a list of values from Excel file
    """
    df = pd.read_excel(input_file)
    return df[column_name].tolist()

def load_values_from_json(input_file: str) -> List[int]:
    """
    Load a list of values from JSON file
    """
    with open(input_file, 'r') as f:
        return json.load(f)

def compute_second_blinded_values(blinded_values: List[int], private_key: int, prime: int) -> List[int]:
    """
    Compute c^(private_key) mod prime for each c in blinded_values
    """
    return [pow(c, private_key, prime) for c in blinded_values]

def find_intersection(values_a: List[int], values_b: List[int]) -> Set[int]:
    """
    Find intersection between two lists of values
    """
    set_a = set(values_a)
    set_b = set(values_b)
    return set_a.intersection(set_b)

def extract_matching_records(
    intersection_keys: Set[int],
    h_to_k_map: Dict[int, int],
    h_to_record_map: Dict[int, pd.Series],
    data_columns: List[str]
) -> pd.DataFrame:
    """
    Extract matching records based on intersection keys
    """
    # Invert h_to_k_map to get k_to_h_map
    k_to_h_map = {k: h for h, k in h_to_k_map.items()}
    
    # Extract matching records
    records = []
    for k in intersection_keys:
        if k in k_to_h_map:
            h = k_to_h_map[k]
            if h in h_to_record_map:
                record = h_to_record_map[h]
                # Extract only the needed columns plus the hash as identifier
                record_data = {'hash_id': h}
                for col in data_columns:
                    if col in record:
                        record_data[col] = record[col]
                records.append(record_data)
    
    # Create DataFrame
    if records:
        return pd.DataFrame(records)
    else:
        # Return empty DataFrame with correct columns
        columns = ['hash_id'] + data_columns
        return pd.DataFrame(columns=columns)

def run_psi_step1(
    excel_path: str,
    id_columns: List[str],
    private_key: int,
    prime: int,
    output_dir: str
) -> Tuple[Dict[int, int], Dict[int, pd.Series], str]:
    """
    Run step 1 of the PSI protocol:
    - Load data
    - Compute hashes and blinded values
    - Save blinded values to file
    - Return mappings and file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = load_excel_data(excel_path)
    
    # Process dataset
    h_to_c_map, h_to_record_map = process_dataset(df, id_columns, private_key, prime)
    
    # Extract blinded values
    c_values = list(h_to_c_map.values())
    
    # Save to file
    c_file_path = os.path.join(output_dir, "c_values.json")
    save_values_to_json(c_values, c_file_path)
    
    return h_to_c_map, h_to_record_map, c_file_path

def run_psi_step2(
    h_to_c_map: Dict[int, int],
    partner_c_file_path: str,
    private_key: int,
    prime: int,
    output_dir: str
) -> Tuple[Dict[int, int], str]:
    """
    Run step 2 of the PSI protocol:
    - Load partner's blinded values
    - Compute second blinded values
    - Save second blinded values to file
    - Return mapping and file path
    """
    # Load partner's blinded values
    partner_c_values = load_values_from_json(partner_c_file_path)
    
    # Compute second blinded values
    k_values = compute_second_blinded_values(partner_c_values, private_key, prime)
    
    # Create h_to_k_map
    # We need to map our original hashes to the double-blinded values we'll match on
    h_to_k_map = {}
    c_to_h_map = {c: h for h, c in h_to_c_map.items()}
    
    # For each original hash, compute what the matching k would be
    for h, c in h_to_c_map.items():
        # This is equivalent to h^(ab) mod p
        our_k = pow(c, private_key, prime)
        h_to_k_map[h] = our_k
    
    # Save k values to file
    k_file_path = os.path.join(output_dir, "k_values.json")
    save_values_to_json(k_values, k_file_path)
    
    return h_to_k_map, k_file_path

def run_psi_step3(
    h_to_k_map: Dict[int, int],
    h_to_record_map: Dict[int, pd.Series],
    partner_k_file_path: str,
    data_columns: List[str],
    output_dir: str
) -> str:
    """
    Run step 3 of the PSI protocol:
    - Load partner's double-blinded values
    - Find intersection
    - Extract matching records
    - Save matching records to file
    - Return file path
    """
    # Load partner's k values
    partner_k_values = load_values_from_json(partner_k_file_path)
    
    # Get our k values
    our_k_values = list(h_to_k_map.values())
    
    # Find intersection
    intersection_keys = find_intersection(our_k_values, partner_k_values)
    
    # Extract matching records
    match_df = extract_matching_records(intersection_keys, h_to_k_map, h_to_record_map, data_columns)
    
    # Save to file
    match_file_path = os.path.join(output_dir, "match_data.xlsx")
    match_df.to_excel(match_file_path, index=False)
    
    return match_file_path

def run_psi_step4(
    our_match_file_path: str,
    partner_match_file_path: str,
    output_dir: str
) -> str:
    """
    Run step 4 of the PSI protocol:
    - Load our matching records
    - Load partner's matching records
    - Merge records based on hash_id
    - Save final result
    - Return file path
    """
    # Load our matching records
    our_match_df = pd.read_excel(our_match_file_path)
    
    # Load partner's matching records
    partner_match_df = pd.read_excel(partner_match_file_path)
    
    # Merge records
    if 'hash_id' in our_match_df.columns and 'hash_id' in partner_match_df.columns:
        # Rename columns in partner DataFrame to avoid duplicates
        partner_columns = {}
        for col in partner_match_df.columns:
            if col != 'hash_id':
                partner_columns[col] = f"partner_{col}"
        
        if partner_columns:
            partner_match_df = partner_match_df.rename(columns=partner_columns)
        
        # Perform inner join
        final_df = pd.merge(our_match_df, partner_match_df, on='hash_id', how='inner')
    else:
        # If hash_id is missing, create an empty DataFrame
        final_df = pd.DataFrame()
    
    # Save final result
    final_file_path = os.path.join(output_dir, "psi_result.xlsx")
    final_df.to_excel(final_file_path, index=False)
    
    return final_file_path

def upload_to_ipfs(file_path: str) -> str:
    """
    Upload file to IPFS and return CID
    Uses the existing upload_to_ipfs.py module
    """
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Import the upload_to_ipfs module
        upload_module_path = os.path.join(current_dir, "upload_to_ipfs.py")
        spec = importlib.util.spec_from_file_location("upload_to_ipfs", upload_module_path)
        upload_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(upload_module)
        
        # Call the upload function with the file path
        cid = upload_module.upload_file_to_ipfs(file_path)
        
        return cid
    except Exception as e:
        raise RuntimeError(f"Failed to upload to IPFS: {str(e)}")

def download_from_ipfs(cid: str, output_path: str) -> str:
    """
    Download file from IPFS using its CID
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use IPFS command-line tool to download the file
        result = subprocess.run(
            ["ipfs", "get", "-o", output_path, cid],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"IPFS get command failed: {result.stderr}")
        
        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download from IPFS: {str(e)}")

def run_psi_protocol(
    excel_path: str,
    id_columns: List[str],
    data_columns: List[str],
    private_key: int,
    prime: int,
    output_dir: str,
    partner_cid_c: str = None,
    partner_cid_k: str = None,
    partner_cid_match: str = None,
    step: int = 1
) -> Dict[str, Any]:
    """
    Run the PSI protocol from a specified step
    Returns a dictionary with results of the performed steps
    """
    result = {}
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    if step <= 1:
        # Step 1: Compute and share blinded hashes
        print("Running PSI Step 1: Computing blinded hashes...")
        h_to_c_map, h_to_record_map, c_file_path = run_psi_step1(
            excel_path, id_columns, private_key, prime, output_dir
        )
        
        # Upload to IPFS
        cid_c = upload_to_ipfs(c_file_path)
        
        result["step1"] = {
            "h_to_c_map": h_to_c_map,
            "h_to_record_map": h_to_record_map,
            "c_file_path": c_file_path,
            "cid_c": cid_c
        }
        
        print(f"Step 1 completed. Your CID for c values: {cid_c}")
        
        if step == 1:
            return result
    else:
        # Load data from previous steps
        try:
            h_to_c_map_file = os.path.join(output_dir, "h_to_c_map.json")
            h_to_record_map_file = os.path.join(output_dir, "h_to_record_map.json")
            
            with open(h_to_c_map_file, 'r') as f:
                h_to_c_map_data = json.load(f)
                # Convert string keys back to integers
                h_to_c_map = {int(k): v for k, v in h_to_c_map_data.items()}
            
            # Load record map (more complex, storing as pickle might be better)
            df = load_excel_data(excel_path)
            h_to_record_map = {}
            for _, record in df.iterrows():
                h = compute_record_hash(record, id_columns)
                h_to_record_map[h] = record
                
        except Exception as e:
            raise ValueError(f"Failed to load data from previous steps: {str(e)}")
    
    if step <= 2 and partner_cid_c:
        # Step 2: Download partner's blinded hashes and compute double-blinded values
        print("Running PSI Step 2: Computing double-blinded values...")
        
        # Download partner's c values
        partner_c_file_path = os.path.join(output_dir, "partner_c_values.json")
        download_from_ipfs(partner_cid_c, partner_c_file_path)
        
        # Compute second blinded values
        h_to_k_map, k_file_path = run_psi_step2(
            h_to_c_map, partner_c_file_path, private_key, prime, output_dir
        )
        
        # Save h_to_k_map for later use
        h_to_k_map_file = os.path.join(output_dir, "h_to_k_map.json")
        with open(h_to_k_map_file, 'w') as f:
            # Convert int keys to strings for JSON
            h_to_k_map_str = {str(k): v for k, v in h_to_k_map.items()}
            json.dump(h_to_k_map_str, f)
        
        # Upload to IPFS
        cid_k = upload_to_ipfs(k_file_path)
        
        result["step2"] = {
            "h_to_k_map": h_to_k_map,
            "k_file_path": k_file_path,
            "cid_k": cid_k
        }
        
        print(f"Step 2 completed. Your CID for k values: {cid_k}")
        
        if step == 2:
            return result
    else:
        # Load data from previous steps if continuing
        if step > 2:
            try:
                h_to_k_map_file = os.path.join(output_dir, "h_to_k_map.json")
                with open(h_to_k_map_file, 'r') as f:
                    h_to_k_map_data = json.load(f)
                    # Convert string keys back to integers
                    h_to_k_map = {int(k): v for k, v in h_to_k_map_data.items()}
            except Exception as e:
                raise ValueError(f"Failed to load k map from previous steps: {str(e)}")
    
    if step <= 3 and partner_cid_k:
        # Step 3: Find intersection and prepare matching data
        print("Running PSI Step 3: Finding intersection and preparing matching data...")
        
        # Download partner's k values
        partner_k_file_path = os.path.join(output_dir, "partner_k_values.json")
        download_from_ipfs(partner_cid_k, partner_k_file_path)
        
        # Find intersection and extract matching records
        match_file_path = run_psi_step3(
            h_to_k_map, h_to_record_map, partner_k_file_path, data_columns, output_dir
        )
        
        # Upload to IPFS
        cid_match = upload_to_ipfs(match_file_path)
        
        result["step3"] = {
            "match_file_path": match_file_path,
            "cid_match": cid_match
        }
        
        print(f"Step 3 completed. Your CID for match data: {cid_match}")
        
        if step == 3:
            return result
    
    if step <= 4 and partner_cid_match:
        # Step 4: Final data merge
        print("Running PSI Step 4: Merging matching data...")
        
        # Download partner's match data
        our_match_file_path = os.path.join(output_dir, "match_data.xlsx")
        partner_match_file_path = os.path.join(output_dir, "partner_match_data.xlsx")
        download_from_ipfs(partner_cid_match, partner_match_file_path)
        
        # Merge data
        final_file_path = run_psi_step4(
            our_match_file_path, partner_match_file_path, output_dir
        )
        
        result["step4"] = {
            "final_file_path": final_file_path
        }
        
        print(f"Step 4 completed. Final result saved to: {final_file_path}")
    
    return result 