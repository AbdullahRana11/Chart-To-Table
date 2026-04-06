import torch
from PIL import Image
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor

# --- CONFIGURATION ---
MODEL_ID = "google/deplot"

class ChartExtractor:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        print(f"🚀 Loading Google DePlot ({MODEL_ID})...")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"   Device: {self.device}")
            
            self.processor = Pix2StructProcessor.from_pretrained(MODEL_ID)
            self.model = Pix2StructForConditionalGeneration.from_pretrained(MODEL_ID).to(self.device)
            print("✅ DePlot Ready!")
        except Exception as e:
            print(f"❌ DePlot Load Failed: {e}")
            raise e

    def extract(self, image_path):
        """
        One-stop inference: Image -> Linearized Table
        """
        image = Image.open(image_path).convert("RGB")

        # DePlot prompt
        inputs = self.processor(
            images=image, 
            text="Generate underlying data table of the figure below:", 
            return_tensors="pt"
        ).to(self.device)

        # Generate
        predictions = self.model.generate(**inputs, max_new_tokens=512)
        raw_text = self.processor.decode(predictions[0], skip_special_tokens=True)
        
        return self.parse_deplot_output(raw_text)

    def parse_deplot_output(self, text):
        """
        Converts DePlot's "Pipe Format" into JSON
        """
        # DePlot usually separates rows with <0x0A> (New Line) and columns with " | "
        rows = text.split("<0x0A>")
        
        # Extract Header
        header = []
        data = []
        
        if len(rows) > 0:
            header_parts = rows[0].split(" | ")
            if len(header_parts) < 2:
                header = ["Category", "Value"]
            else:
                header = [h.strip() for h in header_parts]

        # Extract Data Rows
        for row in rows[1:]:
            parts = row.split(" | ")
            if len(parts) >= len(header):
                row_dict = {}
                for i, h in enumerate(header):
                    # Use index if available, else empty
                    val = parts[i].strip() if i < len(parts) else ""
                    row_dict[h] = val
                data.append(row_dict)
            elif len(parts) >= 2 and len(header) >= 2:
                # Fallback for simple 2-col mismatch
                data.append({header[0]: parts[0].strip(), header[1]: parts[1].strip()})

        # Calculate Heuristic Confidence
        confidence = self._calculate_confidence(header, data, text)

        return {
            "raw_text": text,
            "header": header,
            "data": data,
            "confidence": confidence
        }

    def _calculate_confidence(self, header, data, text):
        """
        Estimate confidence based on output structure.
        """
        if not data:
            return 0.0
            
        score = 1.0
        
        # Penalty 1: Empty or very short text
        if len(text) < 10:
            score -= 0.5
            
        # Penalty 2: Header mismatch (if header detected but no data rows match length)
        # (Already handled deeply in parsing loop, but we can check consistency)
        consistent_rows = sum(1 for row in data if len(row) == len(header))
        if len(data) > 0:
            consistency_ratio = consistent_rows / len(data)
            score *= consistency_ratio
            
        # Penalty 3: Numeric Values Check
        # Most charts have at least one numeric column.
        numeric_cells = 0
        total_cells = 0
        for row in data:
            for k, v in row.items():
                total_cells += 1
                # Remove common currency/percentage symbols before checking
                clean_v = v.replace('%', '').replace('$', '').replace(',', '').strip()
                if clean_v.replace('.', '', 1).isdigit():
                    numeric_cells += 1
        
        if total_cells > 0:
            numeric_ratio = numeric_cells / total_cells
            # If less than 30% of cells are numeric, it might be a bad parse (unless it's a text table)
            if numeric_ratio < 0.3:
                score *= 0.8
                
        return round(max(0.1, min(score, 1.0)), 2)

def get_chart_data(image_path):
    # Lazy Load on first request
    extractor = ChartExtractor.get_instance()
    return extractor.extract(image_path)