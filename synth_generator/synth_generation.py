import os
import random
import csv
import uuid
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm

OUTPUT_DIR = "backend/data_pipeline/dataset"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
LBL_DIR = os.path.join(OUTPUT_DIR, "labels")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)

def generate_chart(index):
    # 1. Random Data
    chart_type = random.choice(["bar", "bar", "pie"]) # Bias towards Bar
    num_items = random.randint(3, 8)
    categories = [f"Item_{i+1}" for i in range(num_items)]
    values = [random.randint(10, 100) for _ in range(num_items)]
    
    unique_id = uuid.uuid4().hex[:8]
    filename = f"syn_{chart_type}_{unique_id}.jpg"
    img_path = os.path.join(IMG_DIR, filename)
    txt_path = os.path.join(LBL_DIR, f"syn_{chart_type}_{unique_id}.txt")
    
    # 2. Plotting
    plt.figure(figsize=(6, 4))
    
    if chart_type == "bar":
        colors = plt.cm.viridis(np.linspace(0, 1, num_items))
        plt.bar(categories, values, color=colors)
        plt.title(f"Synthetic Data {index}")
        plt.tight_layout()
        
    elif chart_type == "pie":
        plt.pie(values, labels=categories, autopct='%1.1f%%')
        plt.title(f"Synthetic Distribution {index}")
    
    plt.savefig(img_path)
    plt.close()
    
    # 3. Create Perfect Label (Pipe Format)
    # Format: Item_1 | 45 <0x0A> Item_2 | 22 ...
    rows = []
    for c, v in zip(categories, values):
        rows.append(f"{c} | {v}")
    
    # Florence-2 Training Format
    linearized_table = " <0x0A> ".join(rows)
    training_text = f"<EXTRACT_DATA> {linearized_table}"
    
    with open(txt_path, "w") as f:
        f.write(training_text)

if __name__ == "__main__":
    print("🚀 Generating 2,000 Synthetic Charts...")
    for i in tqdm(range(2000)):
        generate_chart(i)
    print("✅ Done. Synthetic data ready.")