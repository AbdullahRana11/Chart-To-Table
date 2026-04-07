"""
PlotQA Local Training Script - Fine-tune Florence-2 on Local PlotQA Dataset
=============================================================================
Uses the local annotations.json and png/ folder.
Focuses on BAR and LINE charts (majority of dataset).
Converts annotations to structured markdown tables for training.
"""

import os
import sys
import torch
import json
import logging
import random
from PIL import Image
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM, 
    AutoProcessor, 
    TrainingArguments, 
    Trainer
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

# Fixes "flash_attn" import errors on Windows
sys.modules["flash_attn"] = None

# --- CONFIGURATION ---
MODEL_ID = "microsoft/Florence-2-large"
ADAPTER_PATH = "florence-chart-expert/final"
OUTPUT_DIR = "florence-chart-expert-v2"

ANNOTATIONS_PATH = "annotations.json"
PNG_DIR = "png"

# Training Hyperparameters
BATCH_SIZE = 2
GRAD_ACCUM = 8
MAX_STEPS = 2000
LEARNING_RATE = 2e-5
SAVE_STEPS = 500

# Target samples (filter by chart type)
MAX_SAMPLES = 5000
TARGET_TYPES = {
    'vbar_categorical': 0.35,   # Vertical bar charts
    'hbar_categorical': 0.15,   # Horizontal bar charts  
    'line': 0.30,               # Line charts
    'dot_line': 0.20,           # Dot-line charts
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def annotation_to_table(item: dict) -> str:
    """
    Convert PlotQA annotation to a markdown table.
    
    Annotation structure:
    - models: list of data series with 'name', 'x', 'y' values
    - general_figure_info.x_axis.major_labels.values: x-axis labels
    - type: chart type
    """
    try:
        # Extract chart info
        chart_type = item.get('type', 'unknown')
        title = item.get('general_figure_info', {}).get('title', {}).get('text', '')
        
        # Extract x-axis labels
        x_axis_info = item.get('general_figure_info', {}).get('x_axis', {})
        x_labels = x_axis_info.get('major_labels', {}).get('values', [])
        
        # Extract data series
        models = item.get('models', [])
        
        if not models:
            return ""
        
        # Build table based on data structure
        lines = []
        
        # Add title if present
        if title:
            lines.append(f"# {title}")
            lines.append("")
        
        # For single series, pair x with y
        if len(models) == 1:
            model = models[0]
            x_vals = model.get('x', x_labels)
            y_vals = model.get('y', [])
            
            if x_vals and y_vals:
                lines.append("X | Y")
                lines.append("--- | ---")
                for x, y in zip(x_vals, y_vals):
                    lines.append(f"{x} | {y}")
        
        # For multiple series, create multi-column table
        else:
            # Header: X + each series name
            header_parts = ["X"]
            for model in models:
                header_parts.append(model.get('name', 'Value'))
            lines.append(" | ".join(header_parts))
            lines.append(" | ".join(["---"] * len(header_parts)))
            
            # Get x values from first model or x_labels
            x_vals = models[0].get('x', x_labels) if models else x_labels
            
            # For each x value, get corresponding y from each series
            for i, x in enumerate(x_vals):
                row_parts = [str(x)]
                for model in models:
                    y_vals = model.get('y', [])
                    y_val = y_vals[i] if i < len(y_vals) else ""
                    row_parts.append(str(y_val))
                lines.append(" | ".join(row_parts))
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Failed to convert annotation: {e}")
        return ""


class PlotQALocalDataset(Dataset):
    """
    Dataset that reads from local annotations.json and png/ folder.
    """
    
    def __init__(self, annotations_path: str, png_dir: str, max_samples: int = 5000):
        self.png_dir = png_dir
        self.samples = []
        
        logger.info(f"📂 Loading PlotQA annotations from {annotations_path}...")
        
        try:
            with open(annotations_path, 'r', encoding='utf-8') as f:
                all_annotations = json.load(f)
            
            logger.info(f"   Total annotations: {len(all_annotations)}")
            
            # Group by type for balanced sampling
            type_groups = {}
            for item in all_annotations:
                chart_type = item.get('type', 'unknown')
                if chart_type not in type_groups:
                    type_groups[chart_type] = []
                type_groups[chart_type].append(item)
            
            logger.info(f"   Chart types found: {list(type_groups.keys())}")
            
            # Sample from each type based on quotas
            for chart_type, quota in TARGET_TYPES.items():
                target_count = int(max_samples * quota)
                
                if chart_type in type_groups:
                    available = type_groups[chart_type]
                    sample_count = min(target_count, len(available))
                    sampled = random.sample(available, sample_count)
                    
                    for item in sampled:
                        img_idx = item.get('image_index')
                        img_path = os.path.join(png_dir, f"{img_idx}.png")
                        
                        if not os.path.exists(img_path):
                            continue
                        
                        table_md = annotation_to_table(item)
                        if not table_md or len(table_md) < 10:
                            continue
                        
                        self.samples.append({
                            'image_path': img_path,
                            'table': table_md,
                            'type': chart_type
                        })
                    
                    logger.info(f"   {chart_type}: {len([s for s in self.samples if s['type'] == chart_type])} samples")
            
            # Fill remaining with other types
            remaining = max_samples - len(self.samples)
            if remaining > 0:
                other_items = []
                for chart_type, items in type_groups.items():
                    if chart_type not in TARGET_TYPES:
                        other_items.extend(items)
                
                if other_items:
                    sample_count = min(remaining, len(other_items))
                    sampled = random.sample(other_items, sample_count)
                    
                    for item in sampled:
                        img_idx = item.get('image_index')
                        img_path = os.path.join(png_dir, f"{img_idx}.png")
                        
                        if not os.path.exists(img_path):
                            continue
                        
                        table_md = annotation_to_table(item)
                        if not table_md or len(table_md) < 10:
                            continue
                        
                        self.samples.append({
                            'image_path': img_path,
                            'table': table_md,
                            'type': item.get('type', 'other')
                        })
            
            logger.info(f"✅ Loaded {len(self.samples)} samples total")
            
            # Sanity check first sample
            if self.samples:
                first = self.samples[0]
                logger.info(f"🔎 SANITY CHECK (First Sample):")
                logger.info(f"   Image: {first['image_path']}")
                logger.info(f"   Type: {first['type']}")
                logger.info(f"   Table Preview:\n{first['table'][:400]}...")
                
        except Exception as e:
            logger.error(f"Failed to load annotations: {e}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        try:
            image = Image.open(sample['image_path']).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to load image {sample['image_path']}: {e}")
            # Return a dummy
            image = Image.new('RGB', (100, 100))
        
        return {
            'image': image,
            'text': f"<EXTRACT_DATA>{sample['table']}"
        }


def main():
    logger.info(f"🚀 Florence-2 PlotQA (Local) Fine-Tuning on {torch.cuda.get_device_name(0)}")
    
    # 1. Load Processor & Base Model
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, 
        trust_remote_code=True, 
        torch_dtype=torch.float16,
        attn_implementation="eager"
    ).to("cuda")
    
    # 2. Load existing adapter OR create new
    if os.path.exists(ADAPTER_PATH):
        logger.info(f"📥 Loading existing adapter from {ADAPTER_PATH}...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH, is_trainable=True)
        logger.info("   Continuing training from existing adapter.")
    else:
        logger.info("🆕 Creating new LoRA adapter...")
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM, 
            inference_mode=False, 
            r=8, 
            lora_alpha=32, 
            lora_dropout=0.1,
            target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "linear", "Conv2d", "lm_head", "fc2"]
        )
        model = get_peft_model(model, peft_config)
    
    model.print_trainable_parameters()
    
    # 3. Load Local Dataset
    train_dataset = PlotQALocalDataset(
        annotations_path=ANNOTATIONS_PATH,
        png_dir=PNG_DIR,
        max_samples=MAX_SAMPLES
    )
    
    if len(train_dataset) == 0:
        logger.error("❌ No samples loaded! Exiting.")
        return
    
    # 4. Collate function
    def collate_fn(batch):
        questions, answers, images = [], [], []
        
        for item in batch:
            if not item['text'] or not item['image']:
                continue
            
            full_text = item['text']
            task_prompt = "<EXTRACT_DATA>"
            label = full_text.replace("<EXTRACT_DATA>", "").strip()
            
            questions.append(task_prompt)
            answers.append(label)
            images.append(item['image'])
        
        if not questions:
            return None
        
        inputs = processor(
            text=questions, 
            images=images, 
            return_tensors="pt", 
            padding=True,
            truncation=True,
            max_length=1024
        )
        
        labels = processor.tokenizer(
            text=answers, 
            return_tensors="pt", 
            padding=True, 
            return_token_type_ids=False,
            truncation=True,
            max_length=1024
        ).input_ids
        
        inputs["labels"] = labels
        return inputs
    
    # 5. Training Arguments
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LEARNING_RATE,
        max_steps=MAX_STEPS,
        logging_steps=50,
        save_steps=SAVE_STEPS,
        fp16=True,
        optim="adamw_torch",
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="tensorboard",
        dataloader_num_workers=0,
    )
    
    # 6. Start Training
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        data_collator=collate_fn
    )
    
    logger.info("🔥 Starting Fine-Tuning on PlotQA (Local)...")
    trainer.train()
    
    logger.info("✅ Training Complete. Saving Final Adapter...")
    model.save_pretrained(f"{OUTPUT_DIR}/final")
    processor.save_pretrained(f"{OUTPUT_DIR}/final")
    
    logger.info(f"📁 Model saved to {OUTPUT_DIR}/final")


if __name__ == "__main__":
    main()
