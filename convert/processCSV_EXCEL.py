import pandas as pd
import os
import re
import io
from datetime import datetime, timedelta
import tempfile
from azure.storage.blob import BlobServiceClient
import logging
from azure.storage.blob import generate_account_sas,ResourceTypes, AccountSasPermissions
class ProcessCSV_EXCEL:
    
    def __init__(self,connection_string: str):
        self.connection_string = connection_string

    
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


    def is_numeric(self,value):
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

    def preprocess(self,df: pd.DataFrame):
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


    def save_to_excel(self,df: pd.DataFrame, grouped_df: pd.DataFrame, final_df: pd.DataFrame, output_file: str):
    # Save the original, grouped, and final DataFrames to Excel
        with pd.ExcelWriter(output_file) as writer:
            df.to_excel(writer, sheet_name='Original Data', index=False)
            grouped_df.to_excel(writer, sheet_name='Grouped Data', index=False)
            final_df.to_excel(writer, sheet_name='Final Data', index=False)

    def get_source_file_with_sas(self,container_name: str,blob_names: list[str]) -> dict[str,str]:
        """ Function to return the source file with a SAS token """
        account_name="khaistorageaccount"
        account_key="lRdzW6OEHeWQiL5nyo1KnXHtsTz5mJ8Bqi1Eog8NmsoztEw0IZyJzO/3/l0mDmI/DS4j9lubh6aw+AStCs0+hg=="
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        sas_urls = {}
        for blob_name in blob_names:
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
                source_file = blob_service_client.get_blob_client(container=container_name, blob=blob_name).url
                sas_urls[blob_name] = source_file + "?" + sas_token
            except Exception as error:
                logging.error(f"Unable to generate SAS token for source file: {str(error)}")
                return ""
        return sas_urls
    
    def last_save(self, filepaths: list[str]):
        processed_files = []
        download_links = []
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        output_container_name = 'processed'
        for file_path in filepaths:
            try:
                file_name, file_extension = os.path.splitext(os.path.basename(file_path))
                output_file = 'Output_' + file_name + '.xlsx'
                # Sử dụng thư mục tạm của hệ thống
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                    
                    local_output_path = temp_file.name

                    df = self.load_file(file_path)
                    grouped_df, final_df = self.preprocess(df)
                    
                    self.save_to_excel(df, grouped_df, final_df, local_output_path)
                    
                    # Tải lên Blob Storage
                    blob_client = blob_service_client.get_blob_client(container=output_container_name, blob=output_file)
                    with open(local_output_path, 'rb') as data:
                        blob_client.upload_blob(data, overwrite=True)
                    
                    # Thêm tên tệp đã xử lý vào danh sách
                    processed_files.append(output_file)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                processed_files.append(None)
            
            finally:
                # Xóa tệp tạm sau khi tải lên
                if local_output_path and os.path.exists(local_output_path):
                    os.remove(local_output_path)
        download_links = self.get_source_file_with_sas(output_container_name,processed_files)
        return {
            "status": "success" if all(file is not None for file in processed_files) else "failure",
            "processed_files": processed_files,
            "download_links": download_links,
            "container_name": output_container_name,
            "output_file": output_file
        }