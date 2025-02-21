import random
import pandas as pd
import hashlib
import sympy
def generate_private_key(prime):
    key = random.randint(2,prime-2)
    return key

def Encrypt(file1, file2, prime):
    #file1 is the one that needs to be encrypted
    file_path = "Data/"
    e_file_path = "Encrypt_Data/"
    df = pd.read_excel(file_path + file1)
    df_hashed = pd.DataFrame()
    key = generate_private_key(prime)
    df_hashed["p_id"] = df["p_id"].astype(str).apply(
        lambda x : pow(int(hashlib.sha256(x.encode()).hexdigest(),16),key,prime)
    )
    df_hashed.to_excel(e_file_path + file2)

def init():
    e_file_path = "Encrypt_Data/"
    file_name = input("Please Enter File name you want to encrypt:")
    try:
        with open(e_file_path + "Hashed_"+file_name, 'x') as file:
            print(e_file_path + "Hashed_"+file_name +"created")
    except Exception as e:
        print(f"{e}")
    Encrypt(file1=file_name, file2 ="Hashed_"+file_name,prime =  sympy.randprime(2**511, 2**512))
def main():
    init()
if __name__ == "__main__":
    main()