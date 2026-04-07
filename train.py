import os
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM, 
    AutoProcessor, 
    TrainingArguments, 
    Trainer
)
from peft import LoraConfig, get_peft_model, TaskType
from PIL import Image
import logging

# --- WINDOWS OPTIMIZATION ---
# Fixes "flash_attn" import errors on Windows
import sys
sys.modules["flash_attn"] = None

# --- CONFIGURATION ---
MODEL_ID = "microsoft/Florence-2-large"
DATA_DIR = "backend/data_pipeline/dataset"  # Your combined dataset folder
OUTPUT_DIR = "florence-chart-expert"

# Training Hyperparameters (Tuned for RTX 5060 Ti 8GB)
BATCH_SIZE = 2         # Small batch to fit VRAM
GRAD_ACCUM = 8         # Accumulate to simulate Batch Size = 16
MAX_STEPS = 1000       # Enough for 3,000 images (approx 5 epochs)
LEARNING_RATE = 5e-5   # Standard LoRA rate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartDataset(Dataset):
    def __init__(self, data_dir):
        self.images_dir = os.path.join(data_dir, "images")
        self.labels_dir = os.path.join(data_dir, "labels")
        
        # Filter for valid pairs only
        self.samples = []
        valid_exts = {".jpg", ".jpeg", ".png"}
        
        # Scan images and check for matching text file
        logger.info(f"📂 Scanning {self.images_dir}...")
        for f in os.listdir(self.images_dir):
            name, ext = os.path.splitext(f)
            if ext.lower() in valid_exts:
                txt_path = os.path.join(self.labels_dir, name + ".txt")
                if os.path.exists(txt_path):
                    self.samples.append((f, txt_path))
        
        logger.info(f"✅ Found {len(self.samples)} valid Image-Text pairs.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_file, txt_path = self.samples[idx]
        img_path = os.path.join(self.images_dir, img_file)
        
        # 1. Load Image
        image = Image.open(img_path).convert("RGB")
        
        # 2. Load Label
        with open(txt_path, "r", encoding="utf-8") as f:
            label_text = f.read().strip()
            
        return {"image": image, "text": label_text}

def main():
    logger.info(f"🚀 Initializing Training on {torch.cuda.get_device_name(0)}")
    
    # 1. Load Processor & Model
    # trust_remote_code=True is REQUIRED for Florence-2
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, 
        trust_remote_code=True, 
        torch_dtype=torch.float16,
        attn_implementation="eager" # <--- This bypasses the crash
    ).to("cuda")

    # 2. Add LoRA Adapter (The "Expert Brain")
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

    # 3. Prepare Dataset
    train_dataset = ChartDataset(DATA_DIR)
    
    def collate_fn(batch):
        questions, answers, images = [], [], []
        for item in batch:
            # Safety check: skip corrupt data
            if not item['text'] or not item['image']:
                continue
                
            full_text = item['text']
            
            # Split token from content
            if "<EXTRACT_DATA>" in full_text:
                task_prompt = "<EXTRACT_DATA>"
                label = full_text.replace("<EXTRACT_DATA>", "").strip()
            else:
                task_prompt = "<EXTRACT_DATA>"
                label = full_text
            
            questions.append(task_prompt)
            answers.append(label)
            images.append(item['image'])

        # --- FIX 1: Max Length Truncation ---
        # We enforce a hard limit of 1024 tokens to prevent indexing errors.
        
        # 1. Process Inputs (Prompt + Image)
        inputs = processor(
            text=questions, 
            images=images, 
            return_tensors="pt", 
            padding=True,
            truncation=True,      # <--- CUT OFF IF TOO LONG
            max_length=1024       # <--- HARD LIMIT
        )
        
        # 2. Process Labels (The Table Text)
        labels = processor.tokenizer(
            text=answers, 
            return_tensors="pt", 
            padding=True, 
            return_token_type_ids=False,
            truncation=True,      # <--- CUT OFF IF TOO LONG
            max_length=1024       # <--- HARD LIMIT
        ).input_ids
        
        inputs["labels"] = labels
        return inputs

    # 4. Training Arguments
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LEARNING_RATE,
        max_steps=MAX_STEPS,
        logging_steps=50,
        save_steps=500,
        fp16=True,             # Critical for 5060 Ti speed
        optim="adamw_torch",
        save_total_limit=2,    # Keep only last 2 models to save space
        remove_unused_columns=False,
        report_to="tensorboard"
    )
    
    # 5. Start Training
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        data_collator=collate_fn
    )
    
    logger.info("🔥 Starting Fine-Tuning...")
    trainer.train()
    
    logger.info("✅ Training Complete. Saving Final Adapter...")
    model.save_pretrained(f"{OUTPUT_DIR}/final")
    processor.save_pretrained(f"{OUTPUT_DIR}/final")

if __name__ == "__main__":
    main()