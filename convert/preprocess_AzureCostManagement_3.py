import pandas as pd
import os
import re



def extract_month_name(file_path):
    """
    Extracts the month name from the file path based on the format provided.
    
    Args:
        file_path (str): The file path or name containing the month name.
    
    Returns:
        str: The extracted month name.
    """
    # Regular expression to match and extract the month name 'T4' from the file format
    match = re.search(r'-(T\d+)-\d{4}\.(xlsx|csv)$', file_path, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError(f"Month name not found in file path: {file_path}")

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



def preprocess(df: pd.DataFrame):
    # Group by ResourceId and Category
    grouped_df = df.groupby(['ServiceName', 'ResourceId']).agg({
    'CostUSD': 'sum',
    }).reset_index()

    # Create the dictionary structure
    category_dict = {}
    for category, group in grouped_df.groupby('ServiceName'):
        category_dict[category] = group[['ResourceId', 'CostUSD']].to_dict(orient='records')

    # Initialize an empty list to collect rows
    rows = []

    # Iterate over the dictionary to create rows
    for category, resources in category_dict.items():
        for i, resource in enumerate(resources):
            resource_name = resource['ResourceId'].split('/')[-1]
            ResourceGroupName = resource['ResourceId'].split('resourcegroups')[-1].split('/')[1]
            # For subsequent resources, leave the Category column blank
            rows.append({'Category': category, 'ResourceId': resource['ResourceId'],'ResourceName': resource_name, 'ResourceGroupName': ResourceGroupName, 'CostUSD': resource['CostUSD']})

    # Create the DataFrame
    final_df = pd.DataFrame(rows, columns=['Category', 'ResourceId','ResourceName', 'ResourceGroupName', 'CostUSD'])
    print(final_df.head(10))

    return grouped_df, final_df


def save_to_excel(df: pd.DataFrame, grouped_df: pd.DataFrame, final_df: pd.DataFrame, output_file: str):
    # Save the original, grouped, and final DataFrames to Excel
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, sheet_name='Original Data', index=False)
        grouped_df.to_excel(writer, sheet_name='Grouped Data', index=False)
        final_df.to_excel(writer, sheet_name='Final Data', index=False)


if __name__ == "__main__":
    file_paths = [
    'D:/New folder/compare-python/test/CostManagement_Microsoft Azure_2024-08-12-1714-T4-2024.xlsx',
    'D:/New folder/compare-python/test/CostManagement_Microsoft Azure_2024-08-12-1714-T5-2024.xlsx'
    ]
    for file_path in file_paths:
        try:
            # Trích xuất tên tháng từ tên tệp
            file_name = os.path.splitext(file_path)[0].split('/')[-1]
            
            # month_name = extract_month_name(file_path)
            output_file = 'Output_' + file_name + '.xlsx'

            # Tải dữ liệu từ tệp
            df = load_file(file_path)

            # Tiền xử lý dữ liệu
            grouped_df, final_df = preprocess(df)

            # Lưu kết quả vào tệp Excel riêng biệt
            save_to_excel(df, grouped_df, final_df, output_file)
            print(f"Processed and saved {output_file}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")


