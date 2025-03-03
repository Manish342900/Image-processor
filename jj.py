import pytesseract
from PIL import Image
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import pyautogui


# Mapping store names with uppercase keys for case-insensitive matching
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

# Define custom Total Counter values for each store
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
    'Rama Vihar':32
}



def replace_store_name(store_name):
    # store_name = re.sub(r'\s*-\s*N$', '', store_name, flags=re.IGNORECASE).strip()  # Remove '- N'
    # store_name = re.sub(r'\s*\(\d+\)$', '', store_name).strip()  # Remove numbers in parentheses
    # normalized = store_name.upper()
    # print(store_name)
    for key in store_name_mapping:
        if key in store_name:
            # print(store_name_mapping[key])
            return store_name_mapping[key]
        elif store_name=='- N':
            return "Rohini Sec-9"

        # print(store_name)
    
    return store_name

def extract_data_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    text = re.sub(r'\s+', ' ', text).strip()  # Removes extra spaces & newlines
    text = text.replace(" -N", "-N")  # Fix spacing inconsistencies

    # print("Extracted Text:", text)
    store_pattern = r'([A-Za-z\s\-()]+)\s+Today Billing : (\d+)\s+Rej-%\s*:?(\d+\.\d+)\s+Count:?\s*(\d+)'
    
    matches = re.findall(store_pattern, text)
    # print("Matches:", matches)

    data = []
    for match in matches:
        store_name = replace_store_name(match[0].strip())
        billing = int(match[1].replace(',', ''))
        rej_percent = float(match[2])
        count = int(match[3]) if match[3] else 0  # Handle missing count
        rej_amount = (billing * rej_percent) / 100

        data.append({
            'Store': store_name,
            'Billing Amount': billing,
            'Rejection Percentage': rej_percent,
            'Count': count,
            'Rejection Amount': rej_amount
        })
    # print(data)

    return data

def open_file():
    filepaths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    if not filepaths:
        return

    all_data = []
    try:
        for path in filepaths:
            all_data.extend(extract_data_from_image(path))

        df = pd.DataFrame(all_data)
        if df.empty:
            messagebox.showinfo("Info", "No data extracted.")
            return

        # Aggregate data with accurate rejection calculation
        df_agg = df.groupby('Store', as_index=False).agg({
            'Billing Amount': 'sum',
            'Rejection Amount': 'sum',
            'Count': 'sum'
        })
        df_agg['Rejection Percentage'] = (df_agg['Rejection Amount'] / df_agg['Billing Amount'] * 100).round(2)

        # Add "Total Counter" column using the predefined mapping
        df_agg['Total Counter'] = df_agg['Store'].map(total_counter_mapping).fillna(0).astype(int)  # Default to 0 if not found

        # Calculate totals
        total_billing = df_agg['Billing Amount'].sum()
        total_rej = df_agg['Rejection Amount'].sum()
        total_count = df_agg['Count'].sum()
        total_counter_sum = df_agg['Total Counter'].sum()
        total_rej_percent = (total_rej / total_billing * 100).round(2) if total_billing else 0

        # Create totals row
        totals = pd.DataFrame([{
            'Store': 'Total',
            'Billing Amount': total_billing,
            'Rejection Percentage': total_rej_percent,
            'Count': total_count,
            'Total Counter': total_counter_sum
        }])

        # Combine with aggregated data
        df_final = pd.concat([df_agg, totals], ignore_index=True)

        show_table(df_final)
        # save_csv(df_final)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def save_csv(df):
    try:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            df.to_csv(path, index=False)
            messagebox.showinfo("Success", f"Data saved to {path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def save_snapshot():
    try:
        # Ask user where to save the image
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if not file_path:
            return
        
        # Get coordinates of the frame_table inside the Tkinter window
        root.update()
        x = frame_table.winfo_rootx()
        y = frame_table.winfo_rooty()
        width = frame_table.winfo_width()
        height = frame_table.winfo_height()

        # Take screenshot of the table area
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.save(file_path)
      
    
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_table(df):
    for widget in frame_table.winfo_children():
        widget.destroy()

    # Updated columns to include "Total Counter" but exclude "Rejection Amount"
    columns = ['Store', 'Billing Amount', 'Rejection Percentage', 'Count', 'Total Counter']
    
    # Headers
    for col_idx, col in enumerate(columns):
        tk.Label(frame_table, text=col, relief='solid', width=18, bg='yellow', font='bold').grid(row=0, column=col_idx)

    # Rows
    for row_idx, row in df.iterrows():
        is_last_row = row_idx == len(df) - 1  # Check if it's the last row
        font_style = ("Arial", 10) if is_last_row else ("Arial",10)
        bg_color = "lightgray" if is_last_row else "white"
        for col_idx, col in enumerate(columns):
            value = row[col]
            if isinstance(value, float):
                value = f"{value:.2f}"
            # tk.Label(frame_table, text=value, relief='solid', width=18).grid(row=row_idx+1, column=col_idx)
            tk.Label(frame_table, text=value, relief='solid', width=20, font=font_style, bg=bg_color).grid(row=row_idx+1, column=col_idx)

# GUI setup
root = tk.Tk()
root.title("Store Data Extractor")

btn_upload = tk.Button(root, text="Upload Images", command=open_file)
btn_upload.pack(pady=20)

frame_table = tk.Frame(root)
frame_table.pack(pady=10)

root.mainloop()
