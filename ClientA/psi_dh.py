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
    id_values = []
    
    for col in id_columns:
        if col not in record:
            print(f"WARNING: Column '{col}' not found in record. Available columns: {record.index.tolist()}")
            continue
        
        # Convert to string and strip whitespace to standardize format
        value = str(record[col]).strip().lower()
        id_values.append(value)
    
    # Join with a clear separator that won't appear in typical data
    id_string = "||".join(id_values)
    
    # Print the ID string for debugging (only for first few records)
    # print(f"ID string: {id_string}")
    
    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(id_string.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert to integer
    hash_int = int(hash_hex, 16)
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
    
    # Check if id_columns exist in the dataframe
    missing_columns = [col for col in id_columns if col not in df.columns]
    if missing_columns:
        print(f"WARNING: The following ID columns are missing from the dataframe: {missing_columns}")
        print(f"Available columns: {df.columns.tolist()}")
    
    # Only show first 3 records for debugging to avoid excessive output
    debug_limit = 3
    record_count = 0
    
    for _, record in df.iterrows():
        record_count += 1
        debug_mode = record_count <= debug_limit
        
        # if debug_mode:
        #     print(f"\nProcessing record {record_count}:")
        
        h = compute_record_hash(record, id_columns)
        c = compute_blinded_hash(h, private_key, prime)
        
        # if debug_mode:
        #     print(f"Hash: {h}, Blinded hash: {c}")
        
        h_to_c_map[h] = c
        h_to_record_map[h] = record
    
    # print(f"Processed {record_count} records")
    # print(f"Generated {len(h_to_c_map)} unique hashes")
    
    # If the number of unique hashes is less than the number of records, there might be duplicates
    if len(h_to_c_map) < record_count:
        print(f"WARNING: Found {record_count - len(h_to_c_map)} duplicate hashes")
    
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
    intersection = set_a.intersection(set_b)
    # print(f"Found {len(intersection)} matching values in intersection")
    return intersection

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
    # print(f"Processing {len(intersection_keys)} intersection keys")
    # print(f"Have {len(k_to_h_map)} keys in k_to_h_map")
    # print(f"Have {len(h_to_record_map)} keys in h_to_record_map")
    
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
            else:
                print(f"Warning: Hash {h} not found in original record map")
        else:
            print(f"Warning: Key {k} not found in k_to_h_map")
    
    # Create DataFrame
    if records:
        # print(f"Created DataFrame with {len(records)} records")
        return pd.DataFrame(records)
    else:
        # Return empty DataFrame with correct columns
        print("Warning: No matching records found")
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
    # print(f"Loaded {len(partner_c_values)} partner blinded values")
    
    # Show a sample of partner's values for debugging
    # if partner_c_values:
    #     print(f"Sample of partner blinded values: {partner_c_values[:3]}")
    
    # Compute second blinded values k = c^private_key mod prime
    # These are the values we'll upload to IPFS for the partner to download
    k_values = compute_second_blinded_values(partner_c_values, private_key, prime)
    # print(f"Computed {len(k_values)} second blinded values")
    
    # Show a sample of computed values for debugging
    # if k_values:
    #     print(f"Sample of computed double-blinded values: {k_values[:3]}")
    
    # Create h_to_k_map for matching in step 3
    # This maps our original hashes to the expected matching values (h^(ab) mod p)
    h_to_k_map = {}
    
    # For each of our original hashes, we need to calculate the expected double-blind value
    # that will match with what our partner will compute
    for h, our_c in h_to_c_map.items():
        # Important: We don't apply our private key again to our c value!
        # The correct value will be generated by the partner when they compute c^b
        # We're calculating what we expect to find in the intersection in step 3
        
        # For correct matching in step 3, we need to set h_to_k_map[h] to what we expect
        # the partner to compute for this hash, which is partner's c^(our_private_key) = h^(ab)
        
        # But we don't know which of partner's c values corresponds to this hash h
        # So we'll have to wait until step 3 to find matches based on the k values we compute
        # and the k values our partner computes
        
        # For now, set a placeholder that will be filled during intersection finding
        h_to_k_map[h] = None  # Will be populated during intersection in step 3
    
    # Compute all possible double-blind values from partner's c values
    # These are what we'll compare against in step 3
    partner_c_to_k = {}
    for partner_c in partner_c_values:
        # Apply our private key to partner's c value
        k = pow(partner_c, private_key, prime)
        partner_c_to_k[partner_c] = k
    
    # Save k values to file - these are what we'll share with partner
    k_file_path = os.path.join(output_dir, "k_values.json")
    save_values_to_json(k_values, k_file_path)
    
    # Save partner_c_to_k for use in step 3
    partner_c_to_k_file = os.path.join(output_dir, "partner_c_to_k.json")
    # Convert keys to strings for JSON
    partner_c_to_k_str = {str(c): k for c, k in partner_c_to_k.items()}
    with open(partner_c_to_k_file, 'w') as f:
        json.dump(partner_c_to_k_str, f)
    
    # print(f"Calculated and saved {len(partner_c_to_k)} double-blind values for step 3")
    
    return h_to_k_map, k_file_path

def run_psi_step3(
    h_to_c_map: Dict[int, int],
    h_to_k_map: Dict[int, int],
    h_to_record_map: Dict[int, pd.Series],
    partner_k_file_path: str,
    data_columns: List[str],
    output_dir: str
) -> str:
    # 載入我們的 partner_c 到 k 的映射
    partner_c_to_k_file = os.path.join(output_dir, "partner_c_to_k.json")
    if os.path.exists(partner_c_to_k_file):
        with open(partner_c_to_k_file, 'r') as f:
            partner_c_to_k_str = json.load(f)
            partner_c_to_k = {int(c): k for c, k in partner_c_to_k_str.items()}
        # print(f"載入了 {len(partner_c_to_k)} 個 partner c->k 映射")
    else:
        partner_c_to_k = {}

    # 載入對方的 k 值
    partner_k_values = load_values_from_json(partner_k_file_path)
    # print(f"載入了 {len(partner_k_values)} 個對方雙盲值")

    # 我們的 k 值
    our_k_values = list(partner_c_to_k.values())
    # print(f"我們有 {len(our_k_values)} 個雙盲值")

    # 計算交集
    intersection_keys = set(our_k_values).intersection(set(partner_k_values))
    # print(f"找到了 {len(intersection_keys)} 個交集值")

    # 獲取 h 的有序列表，假設其順序與 c_values 一致
    h_list = list(h_to_c_map.keys())  # 按插入順序

    # 檢查 partner_k_values 的長度是否與 h_list 匹配
    if len(partner_k_values) != len(h_list):
        raise ValueError(f"partner_k_values 長度 ({len(partner_k_values)}) 與 h_list 長度 ({len(h_list)}) 不匹配")

    # 根據 partner_k_values 的順序映射回 h
    match_records = []
    for i, k in enumerate(partner_k_values):
        if k in intersection_keys:
            h = h_list[i]
            record = h_to_record_map[h]
            # 提取所需欄位
            record_data = {'hash_id': h}
            for col in data_columns:
                if col in record:
                    record_data[col] = record[col]
            match_records.append(record_data)

    # 創建 DataFrame
    if match_records:
        match_df = pd.DataFrame(match_records)
        # print(f"創建了包含 {len(match_df)} 條記錄的 DataFrame")
    else:
        print("No matching records found")
        match_df = pd.DataFrame(columns=['hash_id'] + data_columns)

    # 保存到檔案
    match_file_path = os.path.join(output_dir, "match_data.xlsx")
    match_df.to_excel(match_file_path, index=False)
    # print(f"匹配資料已保存至 {match_file_path}")

    return match_file_path

def extract_matching_records_fixed(
    intersection_keys: Set[int],
    k_to_h_map: Dict[int, int],
    h_to_record_map: Dict[int, pd.Series],
    data_columns: List[str]
) -> pd.DataFrame:
    """
    Extract matching records based on intersection keys using k_to_h_map
    """
    records = []
    print(f"Processing {len(intersection_keys)} intersection keys")
    print(f"Have {len(k_to_h_map)} keys in k_to_h_map")
    print(f"Have {len(h_to_record_map)} keys in h_to_record_map")
    
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
            else:
                print(f"Warning: Hash {h} not found in original record map")
        else:
            print(f"Warning: Key {k} not found in k_to_h_map")
    
    # Create DataFrame
    if records:
        # print(f"Created DataFrame with {len(records)} records")
        return pd.DataFrame(records)
    else:
        # Return empty DataFrame with correct columns
        print("Warning: No matching records found")
        columns = ['hash_id'] + data_columns
        return pd.DataFrame(columns=columns)

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
    # print(f"Loaded our match data with {len(our_match_df)} records")
    
    # Load partner's matching records
    partner_match_df = pd.read_excel(partner_match_file_path)
    # print(f"Loaded partner match data with {len(partner_match_df)} records")
    
    # Merge records
    if 'hash_id' in our_match_df.columns and 'hash_id' in partner_match_df.columns and len(our_match_df) > 0 and len(partner_match_df) > 0:
        # Ensure hash_id is treated consistently (convert to string to be safe)
        our_match_df['hash_id'] = our_match_df['hash_id'].astype(str)
        partner_match_df['hash_id'] = partner_match_df['hash_id'].astype(str)
        
        # Rename columns in partner DataFrame to avoid duplicates
        partner_columns = {}
        for col in partner_match_df.columns:
            if col != 'hash_id':
                partner_columns[col] = f"partner_{col}"
        
        if partner_columns:
            partner_match_df = partner_match_df.rename(columns=partner_columns)
        
        # Perform inner join
        final_df = pd.merge(our_match_df, partner_match_df, on='hash_id', how='inner')
        # print(f"Merged data contains {len(final_df)} records")
    else:
        # If hash_id is missing or dataframes are empty, create an empty DataFrame
        print("Warning: Could not merge data - missing hash_id column or empty dataframes")
        final_df = pd.DataFrame()
    
    # Save final result
    final_file_path = os.path.join(output_dir, "psi_result.xlsx")
    final_df.to_excel(final_file_path, index=False)
    print(f"Saved final result to {final_file_path}")
    
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
        print(f"Downloading from IPFS: {cid} to {output_path}")
        result = subprocess.run(
            ["ipfs", "get", "-o", output_path, cid],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"IPFS get command failed: {result.stderr}")
        
        # If the output_path doesn't exist but a file with the CID name does,
        # rename it to the expected output_path
        expected_downloaded_file = os.path.join(os.path.dirname(output_path), cid)
        if not os.path.exists(output_path) and os.path.exists(expected_downloaded_file):
            os.rename(expected_downloaded_file, output_path)
            print(f"Renamed downloaded file from {expected_downloaded_file} to {output_path}")
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"Downloaded file not found at {output_path}")
        
        print(f"Successfully downloaded file to {output_path}")
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
    request_id: str = "",
    partner_cid_c: str = None,
    partner_cid_k: str = None,
    partner_cid_match: str = None,
    step: int = 1
) -> Dict[str, Any]:
    """
    Run the PSI protocol for a specific step
    
    Args:
        excel_path: Path to the Excel file containing the data
        id_columns: List of column names that form the identifier
        data_columns: List of column names to include in the final result
        private_key: Private key for the Diffie-Hellman PSI protocol
        prime: Shared prime number for the protocol
        output_dir: Directory to store output files
        request_id: The unique identifier for the merge request
        partner_cid_c: Partner's CID for c values (for step 2)
        partner_cid_k: Partner's CID for k values (for step 3)
        partner_cid_match: Partner's CID for match data (for step 4)
        step: Which step of the protocol to run (1-4)
        
    Returns:
        Dictionary with results from the executed step
    """
    result = {"request_id": request_id}
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Declare h_to_c_map at the function level so it's available across steps
    h_to_c_map = {}
    h_to_record_map = {}
    
    if step <= 1:
        # Step 1: Compute and share blinded hashes
        print("Running PSI Step 1: Computing blinded hashes...")
        h_to_c_map, h_to_record_map, c_file_path = run_psi_step1(
            excel_path, id_columns, private_key, prime, output_dir
        )
        
        # Upload to IPFS
        cid_c = upload_to_ipfs(c_file_path)
        
        # Save h_to_c_map for later steps
        h_to_c_map_file = os.path.join(output_dir, "h_to_c_map.json")
        with open(h_to_c_map_file, 'w') as f:
            # Convert int keys to strings for JSON
            h_to_c_map_str = {str(k): v for k, v in h_to_c_map.items()}
            json.dump(h_to_c_map_str, f)
        
        # We can't easily serialize record_map directly, but we'll save the info needed to recreate it
        psi_config_file = os.path.join(output_dir, "psi_config.json")
        with open(psi_config_file, 'w') as f:
            config = {
                "excel_path": excel_path,
                "id_columns": id_columns,
                "data_columns": data_columns,
                "private_key": private_key,
                "prime": prime,
                "request_id": result.get("request_id", "")
            }
            json.dump(config, f)
        
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
            psi_config_file = os.path.join(output_dir, "psi_config.json")
            
            # Load h_to_c_map
            with open(h_to_c_map_file, 'r') as f:
                h_to_c_map_data = json.load(f)
                # Convert string keys back to integers
                h_to_c_map = {int(k): v for k, v in h_to_c_map_data.items()}
            
            # print(f"Loaded h_to_c_map with {len(h_to_c_map)} entries")
            
            # Load configuration if excel_path is not provided
            if not excel_path and os.path.exists(psi_config_file):
                with open(psi_config_file, 'r') as f:
                    config = json.load(f)
                    excel_path = config.get("excel_path", excel_path)
                    id_columns = config.get("id_columns", id_columns)
                    data_columns = config.get("data_columns", data_columns)
                    private_key = config.get("private_key", private_key)
                    prime = config.get("prime", prime)
            
            # Load record map (regenerate from the original Excel file)
            print(f"Loading original data from Excel file: {excel_path}")
            df = load_excel_data(excel_path)
            h_to_record_map = {}
            for idx, record in df.iterrows():
                h = compute_record_hash(record, id_columns)
                h_to_record_map[h] = record
            
            print(f"Loaded {len(h_to_record_map)} records from Excel file")
                
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
                # print(f"Loaded h_to_k_map with {len(h_to_k_map)} entries")
            except Exception as e:
                raise ValueError(f"Failed to load k map from previous steps: {str(e)}")
    
    if step <= 3 and partner_cid_k:
        # Step 3: Find intersection and prepare matching data
        print("Running PSI Step 3: Finding intersection and preparing matching data...")
        
        # Make sure h_to_c_map is loaded
        if not h_to_c_map:
            h_to_c_map_file = os.path.join(output_dir, "h_to_c_map.json")
            if os.path.exists(h_to_c_map_file):
                with open(h_to_c_map_file, 'r') as f:
                    h_to_c_map_data = json.load(f)
                    # Convert string keys back to integers
                    h_to_c_map = {int(k): v for k, v in h_to_c_map_data.items()}
                # print(f"Loaded h_to_c_map with {len(h_to_c_map)} entries for step 3")
            else:
                print("ERROR: h_to_c_map file not found. Cannot proceed with step 3.")
                return result
        
        # Download partner's k values
        partner_k_file_path = os.path.join(output_dir, "partner_k_values.json")
        download_from_ipfs(partner_cid_k, partner_k_file_path)
        
        # Find intersection and extract matching records
        match_file_path = run_psi_step3(
            h_to_c_map, h_to_k_map, h_to_record_map, partner_k_file_path, data_columns, output_dir
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