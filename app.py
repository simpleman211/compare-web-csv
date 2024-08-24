from flask import Flask, render_template, request, send_file,Response, send_file, jsonify
from convert.compareCSV_EXCEL import CompareCSV_EXECL
from convert.processCSV_EXCEL import ProcessCSV_EXCEL
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from werkzeug.utils import secure_filename
import os
import io
import tempfile
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESS_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'csv'}

constr = "DefaultEndpointsProtocol=https;AccountName=khaistorageaccount;AccountKey=lRdzW6OEHeWQiL5nyo1KnXHtsTz5mJ8Bqi1Eog8NmsoztEw0IZyJzO/3/l0mDmI/DS4j9lubh6aw+AStCs0+hg==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(constr)

# Create container uploads to save file uploads in front end
uploads_container_name = "uploads"
container_client = blob_service_client.get_container_client(uploads_container_name)
if not container_client.exists():
    blob_service_client.create_container(uploads_container_name)
    print(f"Container '{uploads_container_name}' created successfully.")
else:
    print(f"Container '{uploads_container_name}' already exists.")

# Create container processed to store file after process
processed_container_name = "compare"
container_client = blob_service_client.get_container_client(processed_container_name)

if not container_client.exists():
    blob_service_client.create_container(processed_container_name)
    print(f"Container '{processed_container_name}' created successfully.")
else:
    print(f"Container '{processed_container_name}' already exists.")

compare_container_name = "processed"
container_client = blob_service_client.get_container_client(compare_container_name)

if not container_client.exists():
    blob_service_client.create_container(compare_container_name)
    print(f"Container '{compare_container_name}' created successfully.")
else:
    print(f"Container '{compare_container_name}' already exists.")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def upload():
    if 'file[]' not in request.files:
        return 'No file part'
    
    files = request.files.getlist('file[]')
    if not files:
        return 'No files selected'
   
    file_paths = {}
    processCSV = ProcessCSV_EXCEL(constr)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            blob_client = blob_service_client.get_blob_client(container="uploads", blob=filename)
            blob_client.upload_blob(file,overwrite=True)
            file_paths[filename] = filename

    if not file_paths:
        return 'No valid files to process'
    file_name = []
    for file_path in file_paths:
        try:
            file_name_text = os.path.splitext(file_path)[0].split('\\')[-1]
            file_name.append(file_name_text)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    combined_file_names = ' '.join(file_name).split()  
    temp_files = []
    
    try:
        for i, (original_file, processed_file) in enumerate(file_paths.items()):
            try:
                # Tạo Blob client để tải file từ container 'uploads'
                blob_client = blob_service_client.get_blob_client(container="uploads", blob=original_file)
                
                # Tải file từ Blob Storage về bộ nhớ tạm
                download_stream = blob_client.download_blob()
                file_content = io.BytesIO(download_stream.readall())
                file_content.seek(0)
                
                # Lấy đuôi file từ tên blob
                _, file_extension = os.path.splitext(original_file)
                
                # Xác định tên tệp tạm từ danh sách combined_file_names hoặc tạo tên mới
                if i < len(combined_file_names):
                    temp_file_name = combined_file_names[i] + file_extension
                else:
                    temp_file_name = f"temp_{i}{file_extension}"
                
                # Tạo đường dẫn tệp tạm
                temp_file_path = os.path.join(tempfile.gettempdir(), temp_file_name)
                
                # Tạo tệp tạm với tên cụ thể và lưu vào danh sách
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(file_content.getvalue())
                    temp_files.append(temp_file_path)
            except Exception as e:
                print(f"Error processing upload {original_file}: {e}")
        # Sau khi tất cả file tạm đã được tạo, gọi phương thức last_save với danh sách file tạm
        processed_data = processCSV.last_save(temp_files)
        print(processed_data)
        # Xóa các file t
        for temp_file in temp_files:
            print(temp_file)
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                else:
                    print(f"Tệp tạm {temp_file} không tồn tại.")
            except Exception as e:
                print(f"Không thể xóa tệp tạm {temp_file}: {e}")
                
    except Exception as e:
        print(f"Error during the overall processing: {e}")
    return render_template('index.html', 
        status=processed_data['status'],
        processed_files=processed_data['processed_files'], 
        download_links=processed_data['download_links'],
        container_name=processed_data['container_name'],
        output_file=processed_data['output_file'])
   
@app.route('/compare', methods=['POST'])
def compare():
    if 'file[]' not in request.files:
        return 'No file part'
    
    files = request.files.getlist('file[]')
    if not files:
        return 'No files selected'
    file_paths = {}
    compare_files = CompareCSV_EXECL(constr)
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            blob_client = blob_service_client.get_blob_client(container="uploads", blob=filename)
            blob_client.upload_blob(file,overwrite=True)
            file_paths[filename] = filename

    if not file_paths:
        return 'No valid files to process'
    file_name = []
    for file_path in file_paths:
        try:
            file_name_text = os.path.splitext(file_path)[0].split('\\')[-1]
            file_name.append(file_name_text)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    combined_file_names = ' '.join(file_name).split()  
    temp_files = []

    try:
        for i, (original_file, processed_file) in enumerate(file_paths.items()):
            try:
                # Tạo Blob client để tải file từ container 'uploads'
                blob_client = blob_service_client.get_blob_client(container="uploads", blob=original_file)
                
                # Tải file từ Blob Storage về bộ nhớ tạm
                download_stream = blob_client.download_blob()
                file_content = io.BytesIO(download_stream.readall())
                file_content.seek(0)
                
                # Lấy đuôi file từ tên blob
                _, file_extension = os.path.splitext(original_file)
                
                # Xác định tên tệp tạm từ danh sách combined_file_names hoặc tạo tên mới
                if i < len(combined_file_names):
                    temp_file_name = combined_file_names[i] + file_extension
                else:
                    temp_file_name = f"temp_{i}{file_extension}"
                
                # Tạo đường dẫn tệp tạm
                temp_file_path = os.path.join(tempfile.gettempdir(), temp_file_name)
                
                # Tạo tệp tạm với tên cụ thể và lưu vào danh sách
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(file_content.getvalue())
                    temp_files.append(temp_file_path)
            except Exception as e:
                print(f"Error processing upload {original_file}: {e}")
        compare_data = compare_files.compare_costs(temp_files)
        for temp_file in temp_files:
            print(temp_file)
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                else:
                    print(f"Tệp tạm {temp_file} không tồn tại.")
            except Exception as e:
                print(f"Không thể xóa tệp tạm {temp_file}: {e}")
        print(compare_data)
    except Exception as e:
        print(f"Error during the overall processing: {e}")
    return render_template('index.html',
                           status=compare_data['status'],
                            blob_name=compare_data['blob_name'],
                            download_links=compare_data['download_links'],
                            output_container_name=compare_data['container_name'])
@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['PROCESS_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return 'No file available for download'

@app.route('/preview/<containerName>/<blobName>', methods=['GET'])
def preview_file(containerName, blobName):
    try:
        blob_client = blob_service_client.get_blob_client(container=containerName, blob=blobName)
        blob_data = blob_client.download_blob()
        file_data = blob_data.readall()

        # Giữ BytesIO stream mở
        byte_stream = BytesIO(file_data)

        # Xác định định dạng tệp từ phần mở rộng
        if blobName.lower().endswith('.csv'):
            # Xử lý file CSV và trả về dưới dạng văn bản
            csv_content = byte_stream.getvalue().decode('utf-8')
            return Response(csv_content, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename={blobName}"})
        elif blobName.lower().endswith('.xlsx'):
            # Xử lý file Excel
            xls = pd.ExcelFile(byte_stream, engine='openpyxl')
            html_tables = []
            for sheet_name in xls.sheet_names:
                print(f"Processing sheet: {sheet_name}")
                df = pd.read_excel(xls, sheet_name=sheet_name)
                html_table = df.to_html(classes='table table-striped', index=False)
                html_tables.append(f"<h3>{sheet_name}</h3>{html_table}")
            full_html = ''.join(html_tables)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # Đóng stream sau khi đã hoàn thành
        byte_stream.close()

        if blobName.lower().endswith('.xlsx'):
            return full_html
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/cleanup')
def cleanup():
    # Xóa tất cả các file trong thư mục 'processed'
    for file_name in os.listdir(app.config['PROCESS_FOLDER']):
        file_path = os.path.join(app.config['PROCESS_FOLDER'], file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Xóa tất cả các file trong thư mục 'uploads'
    for file_name in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return 'Cleanup completed'

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
