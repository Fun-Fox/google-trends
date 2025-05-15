# utils/ui_utils.py
import pandas as pd

def read_csv_file(csv_path):
    df = pd.read_csv(csv_path)
    return df[['hot_word', 'chinese', 'output']]