import pandas as pd
import os
import re



def extract_month_year(file_path):
    """
    Extracts the month and year from the file path based on the format provided.
    
    Args:
        file_path (str): The file path or name containing the month and year.
    
    Returns:
        str: The extracted month and year in the format 'T12_2023'.
    """
    # Regular expression to match and extract the month (T12) and year (2023) from the file name
    match = re.search(r'-T(\d+)-(\d{4})\.xlsx$', file_path)
    if match:
        month = f"T{match.group(1).strip()}"  # Extracts 'T12'
        year = match.group(2).strip()         # Extracts '2023'
        return f"{month}_{year}"              # Combines into 'T12_2023'
    else:
        raise ValueError(f"Month and year not found in file path: {file_path}")

def load_file(file_path, sheet_name: str = 'Data'):
    """
    Loads a CSV or Excel file into a DataFrame.
    
    Args:
        file_path (str): The file path.
    
    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.xlsx':
        # Load the first sheet of an Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
    elif file_ext == '.csv':
        # Load a CSV file
        df = pd.read_csv(file_path, header=0)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    return df


def is_numeric(value):
    """
    Checks if a value is numeric.
    
    Args:
        value: The value to check.
    
    Returns:
        bool: True if value is numeric, False otherwise.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False
    
def format_final_df(grouped_df: pd.DataFrame):
    # Create the dictionary structure
    category_dict = {}
    for category, group in grouped_df.groupby('Category'):
        list_cols = grouped_df.columns.to_list()[1:]
        category_dict[category] = group[list_cols].to_dict(orient='records')
    # Initialize an empty list to collect rows
    rows = []

    # # Iterate over the dictionary to create rows
    for category, resources in category_dict.items():
        for i, resource in enumerate(resources):
            resource_name = resource['ResourceId'].split('/')[-1]
            ResourceGroupName = resource['ResourceId'].split('resourcegroups')[-1].split('/')[1]
            dict_map = {'Category': category, 'ResourceId': resource['ResourceId'], 'ResourceName': resource_name, 'ResourceGroupName': ResourceGroupName}
            # Sort keys by the numeric suffix (T1, T2, ..., T12)
            sorted_keys = sorted(
                (key for key in resource.keys() if key.startswith('CostUSD')),
                key=lambda x: int(x.split('_T')[-1])
            )
            for key in sorted_keys:
                if key not in dict_map:
                    dict_map[key] = resource[key]
            
            rows.append(dict_map)
    # Create the final formatted DataFrame
    formatted_df = pd.DataFrame(rows, columns=list(dict_map.keys()))
    return formatted_df

def compare_costs(file_paths, output_file):
    # Initialize an empty list to store DataFrames
    dfs = []

    for i, file_path in enumerate(file_paths, 1):
        # Load and process each file
        df = pd.read_excel(file_path)
        grouped_df = pd.read_excel(file_path, sheet_name='Grouped Data', header=0)

        month_year = extract_month_year(file_path)
        # Rename the CostUSD column to include the file number
        grouped_df.rename(columns={'CostUSD': f'CostUSD_{month_year}'}, inplace=True)
        
        # Append to the list
        dfs.append(grouped_df)

    # Merge all DataFrames on 'ServiceName' and 'ResourceId' using outer join
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on=['ServiceName', 'ResourceId'], how='outer')

    # Rename 'ServiceName' to 'Category' for the final output
    merged_df.rename(columns={'ServiceName': 'Category'}, inplace=True)

    # # Format the final DataFrame
    formatted_df = format_final_df(merged_df)
    print(formatted_df.head(10))
    # # Save the merged DataFrame to a CSV file
    formatted_df.to_csv(output_file, index=False)

# Example usage
# file_paths = ['/home/ntkien/test/Output_CostManagement_Microsoft Azure_2024-08-12-1714-T4-2024.xlsx', '/home/ntkien/test/Output_CostManagement_Microsoft Azure_2024-08-12-1714-T5-2024.xlsx']  # Add paths to your Excel files
# compare_costs(file_paths, 'comparison_output.csv')


if __name__ == "__main__":
    
    # Example usage
    file_paths = [
        'D:/New folder/compare-python/convert/Output_CostManagement_Microsoft Azure_2024-08-12-1714-T4-2024.xlsx',
        'D:/New folder/compare-python/convert/Output_CostManagement_Microsoft Azure_2024-08-12-1714-T5-2024.xlsx'
        ]
    outputfilename = 'D:/New folder/compare-python/convert/comparison_output_'
    for i, file in enumerate(file_paths, 1):
        if i == 2:
            outputfilename += '_to_'
        outputfilename += extract_month_year(file)
    print(outputfilename)
    compare_costs(file_paths, f'{outputfilename}.csv')