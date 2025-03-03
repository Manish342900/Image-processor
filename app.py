from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import pandas as pd
import re
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Store name and counter mappings
store_name_mapping = {
    ") Budh Vihar - N": 'Budh Vihar',
    'BUDH VIHAR-II-N': 'Budh Vihar-II',
    'Rohini Sec-9': 'Rohini Sec-9',
    'Rohini': 'Rohini Sec-24/25',
    'Shahbad Dairy - N': 'Shahbad Dairy',
    'Sultanpuri - N': 'Sultanpuri',
    'Holambi Kalan - N': 'Holambi Kalan',
    'Ishwar Colony': 'Ishwar Colony',
    ') KANJHAWLA': 'Kanjhawla',
    'Rama Vihar - N': 'Rama Vihar',
}

total_counter_mapping = {
    'Budh Vihar': 32,
    'Budh Vihar-II': 32,
    'Rohini Sec-9': 17,
    'Rohini Sec-24/25': 35,
    'Shahbad Dairy': 34,
    'Sultanpuri': 22,
    'Holambi Kalan': 20,
    'Ishwar Colony': 32,
    'Kanjhawla': 25,
    'Rama Vihar': 32
}

def replace_store_name(store_name):
    for key in store_name_mapping:
        if key in store_name:
            return store_name_mapping[key]
        elif store_name == "- N":
            return "Rohini Sec-9"
    return store_name

def extract_data_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    text = re.sub(r'\s+', ' ', text).strip()  
    text = text.replace(" -N", "-N")

    store_pattern = r'([A-Za-z\s\-()]+)\s+Today Billing : (\d+)\s+Rej-%\s*:?(\d+\.\d+)\s+Count:?\s*(\d+)'
    matches = re.findall(store_pattern, text)

    data = []
    for match in matches:
        store_name = replace_store_name(match[0].strip())
        billing = int(match[1].replace(',', ''))
        rej_percent = float(match[2])
        count = int(match[3]) if match[3] else 0  
        rej_amount = (billing * rej_percent) / 100

        data.append({
            'Store': store_name,
            'Billing Amount': billing,
            'Rejection Percentage': rej_percent,
            'Count': count,
            'Rejection Amount': rej_amount
        })

    return data

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    all_data = []
    for file in files:
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_path = f"temp_image_{file.filename}"
        file.save(file_path)

        try:
            data = extract_data_from_image(file_path)
            all_data.extend(data)  # Collect data from all files

        except Exception as e:
            return jsonify({"error": f"Error processing file {file.filename}: {str(e)}"}), 500
        finally:
            # Clean up the temporary file after processing
            if os.path.exists(file_path):
                os.remove(file_path)

    if not all_data:
        return jsonify({"message": "No data extracted from the images"}), 200

    # Process and aggregate the data
    df = pd.DataFrame(all_data)
    df_agg = df.groupby('Store', as_index=False).agg({
        'Billing Amount': 'sum',
        'Rejection Amount': 'sum',
        'Count': 'sum'
    })
    df_agg['Rejection Percentage'] = (df_agg['Rejection Amount'] / df_agg['Billing Amount'] * 100).apply(lambda x: "{:.2f}".format(x))
    df_agg['Total Counter'] = df_agg['Store'].map(total_counter_mapping).fillna(0).astype(int)

    return jsonify(df_agg.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
