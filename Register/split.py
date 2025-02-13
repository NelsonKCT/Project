import pandas as pds
def init():
    file_path = "Test_Data/test_data_1.xlsx"
    file_path2 = "Test_Data/test_data_2.xlsx"
    try:
        with open(file_path, 'x') as file:
            print("file1 created")
    except FileExistsError:
        print("file1 exists")
    try:
        with open(file_path2,"x") as file:
            print("file2 created")
    except FileExistsError:
        print("file2 exists")
    
def split():
    file_path = "Test_Data/std_mol_record.xlsx"
    file_path1= "Test_Data/test_data_1.xlsx"
    file_path2 = "Test_Data/test_data_2.xlsx"
    # file1 s_id p_id s_sex
    df = pds.read_excel(file_path)
    project_df1 = df[["s_id", "p_id", "s_sex","county","region"]]
    project_df1.to_excel(file_path1, index = False)
    # file2 s_id p_id s_sex company_number mol_s_id
    project_df2 = df[["s_id", "p_id", "s_sex","i_year","i_semester","leave_semester","dept_name","mol_s_id", "company_number","company_name"]]
    project_df2.to_excel(file_path2, index = False)
def main():
    init()
    split()
if __name__ == "__main__":
    main()