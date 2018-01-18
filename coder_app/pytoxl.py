import os
from openpyxl import Workbook
from common.s3_and_file_operations import upload_local_file_to_s3_and_delete_local, download_s3_file_to_local, remove_s3_file

def process_ae_data(ae_data):
    wb = Workbook()
    ws = wb.active

    project_name = ae_data[0]['project_name']
    title = "Adverse Event Data " + project_name
    ws.title = title

    headers = ["Date/Time Posted", "URL", "Author", "Contents", "Source", "Date", "Time"]

    ws.append(headers)

    for ae in ae_data:

        ae_row = [ae['date_posted'], ae['url'], ae['author'], ae['contents'], ae['source'], ae['date'], ae['time']]

        ws.append(ae_row)

    base_path = os.getcwd() + '/'
    save_path = 'files/coder_app/'

    title = title.split(' ')
    title = '_'.join(title)
    filename = title + '.xlsx'

    full_save_path = base_path + save_path + filename

    wb.save(full_save_path)

    upload_local_file_to_s3_and_delete_local(save_path + filename)

    return save_path + filename