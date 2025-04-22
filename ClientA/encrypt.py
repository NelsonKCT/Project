import random
import pandas as pd
import hashlib
import sympy
import os
import sys

def generate_private_key(prime):
    """Generate a random private key for encryption"""
    key = random.randint(2, prime-2)
    return key

def encrypt(input_filename, prime=None):
    """
    Encrypt an Excel file containing patient IDs
    
    Args:
        input_filename (str): Filename of the input Excel file (will be read from Test_Data/)
        prime (int): Prime number to use for encryption (default: generate a random prime)
    
    Returns:
        str: Path to the encrypted file
    """
    # Set up input and output paths
    input_file = os.path.join("Test_Data", input_filename)
    output_dir = "Encrypted_Data"
    output_file = os.path.join(output_dir, f"encrypted_{input_filename}")
    # Handle default prime
    if prime is None:
        prime = sympy.randprime(2**511, 2**512)
        # Save the prime for later use if needed
        with open("prime.txt", "w") as prime_file:
            prime_file.write(str(prime))
    
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return None
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Read the input file
        df = pd.read_excel(input_file)
        
        # Check if 'p_id' column exists
        if 'p_id' not in df.columns:
            print("Error: The input file must contain a 'p_id' column")
            return None
        
        # Create a new dataframe for the encrypted data
        df_encrypted = pd.DataFrame()
        
        # Generate encryption key
        key = generate_private_key(prime)

        
        # Encrypt the p_id column
        df_encrypted["p_id"] = df["p_id"].astype(str).apply(
            lambda x: pow(int(hashlib.sha256(x.encode()).hexdigest(), 16), key, prime)
        )
        
        # Save the encrypted data
        df_encrypted.to_excel(output_file, index=False)
        print(f"File encrypted successfully: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"Error encrypting file: {e}")
        return None

def main():
    """Main function to handle file encryption"""
    print("File Encryption Tool")
    print("====================")
    
    # Get input filename (without path)
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
    else:
        input_filename = input("Please enter the name of the file you want to encrypt (from Test_Data/): ")

    # Encrypt the file
    encrypted_file = encrypt(input_filename)
    
    if encrypted_file:
        print(f"Encryption complete. Encrypted file: {encrypted_file}")
    else:
        print("Encryption failed. Please check the error messages above.")

if __name__ == "__main__":
    main()