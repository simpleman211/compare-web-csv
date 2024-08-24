import pandas as pd
import os
import re
import pandas as pd
import os
import re
import io
from datetime import datetime, timedelta
import tempfile
from azure.storage.blob import BlobServiceClient
import logging
from azure.storage.blob import generate_account_sas,ResourceTypes, AccountSasPermissions

class CompareCSV_EXECL:
    def __init__(self,connection_string: str):
        self.connection_string = connection_string
    
    def extract_month_year(self,file_path):
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
        
    def load_file(self,file_path, sheet_name: str = 'Data'):
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

    def is_numeric(self, value):
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

    def format_final_df(self, grouped_df: pd.DataFrame):
        """
        Formats the final DataFrame.
        
        Args:
            grouped_df (pd.DataFrame): The grouped DataFrame to format.
        
        Returns:
            pd.DataFrame: The formatted DataFrame.
        """
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
    
    def get_source_file_with_sas(self,container_name: str,blob_names: list[str]) -> dict[str,str]:
        """ Function to return the source file with a SAS token """
        account_name="khaistorageaccount"
        account_key="lRdzW6OEHeWQiL5nyo1KnXHtsTz5mJ8Bqi1Eog8NmsoztEw0IZyJzO/3/l0mDmI/DS4j9lubh6aw+AStCs0+hg=="
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        sas_urls = {}
        try:
            sas_token = generate_account_sas(
                account_name,
                account_key,
                resource_types=ResourceTypes(object=True, service=True, container=True),
                permission=AccountSasPermissions(
                    read=True,
                    write=True,
                    list=True,
                    delete=False,
                    add=True,
                    create=True,
                    update=True,
                    process=False,
                ),
                expiry=datetime.utcnow() + timedelta(hours=1),
            )
            source_file = blob_service_client.get_blob_client(container=container_name, blob=blob_names).url
            sas_urls[blob_names] = source_file + "?" + sas_token
        except Exception as error:
            logging.error(f"Unable to generate SAS token for source file: {str(error)}")
            return ""
        return sas_urls
    

    def compare_costs(self, file_paths):
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        output_container_name = 'compare'
        dfs = []

        for file_path in file_paths:
            df = pd.read_excel(file_path)
            grouped_df = pd.read_excel(file_path, sheet_name='Grouped Data', header=0)
            month_year = self.extract_month_year(file_path)
            grouped_df.rename(columns={'CostUSD': f'CostUSD_{month_year}'}, inplace=True)
            dfs.append(grouped_df)

        merged_df = dfs[0]
        for df in dfs[1:]:
            merged_df = pd.merge(merged_df, df, on=['ServiceName', 'ResourceId'], how='outer')

        merged_df.rename(columns={'ServiceName': 'Category'}, inplace=True)
        formatted_df = self.format_final_df(merged_df)

        # Đặt tên file cố định
        blob_name = 'comparison_output.csv'

        # Sử dụng 'with' để đảm bảo file được đóng sau khi sử dụng
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file_name = temp_file.name
            # Save the merged DataFrame to the temporary CSV file
            formatted_df.to_csv(temp_file_name, index=False)
            print(f"Comparison saved to temporary file {temp_file_name}")

        try:
            # Upload the file to Blob Storage
            blob_client = blob_service_client.get_blob_client(container=output_container_name, blob=blob_name)
            with open(temp_file_name, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"File uploaded to Blob Storage in container '{output_container_name}' as '{blob_name}'")
        except Exception as e:
            print(f"Failed to upload to Blob Storage: {e}")
        finally:
            # Đảm bảo file tạm thời được xóa sau khi tải lên
            os.remove(temp_file_name)

        download_links = self.get_source_file_with_sas(output_container_name, blob_name)
        return {
            "status": "success",
            "blob_name": blob_name,
            "download_links": download_links,
            "container_name": output_container_name
        }
