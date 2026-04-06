import pandas as pd
import io
import logging
import re
import json
from typing import Dict, Any, List
from .heuristics import extract_metadata

logger = logging.getLogger(__name__)

class FusionEngine:
    def __init__(self):
        pass

    def parse_florence_output(self, raw_text: str) -> pd.DataFrame:
        """
        Parses the output from Florence-2 extractor into a Pandas DataFrame.
        
        Handles:
        1. New JSON format with x_axis_labels, y_axis_labels, data_values
        2. Legacy pipe-separated format
        3. Legacy OCR text format
        """
        try:
            # First, try to parse as JSON (new structured format)
            if raw_text.strip().startswith('{'):
                try:
                    data = json.loads(raw_text)
                    return self._parse_structured_json(data)
                except json.JSONDecodeError:
                    pass
            
            # Legacy: Clean up potential artifacts
            text = raw_text.replace('</s>', '').replace('<s>', '').strip()
            text = text.replace('<EXTRACT_DATA>', '').replace('<OCR>', '').strip()
            text = re.sub(r'<\s*0[xX]0[aA]\s*>', '\n', text)
            
            logger.info(f"Cleaned text for parsing: {repr(text[:500])}")
            
            # Try parsing as pipe-separated values
            if '|' in text:
                return self._parse_pipe_separated(text)
            
            # Try parsing as CSV
            if ',' in text and '\n' in text:
                try:
                    return pd.read_csv(io.StringIO(text))
                except:
                    pass
            
            # Parse OCR output
            return self._parse_ocr_output(text)
            
        except Exception as e:
            logger.warning(f"Failed to parse Florence output as table: {e}")
            return pd.DataFrame()
    
    def _parse_structured_json(self, data: dict) -> pd.DataFrame:
        """
        Parse the new structured JSON format from extractor.
        
        Expected format:
        {
            "title": "...",
            "x_axis_labels": ["20", "40", ...],
            "y_axis_labels": ["0", "20", ...],
            "data_values": ["val1", "val2", ...]
        }
        """
        x_labels = data.get('x_axis_labels', [])
        y_labels = data.get('y_axis_labels', [])
        data_values = data.get('data_values', [])
        title = data.get('title', '')
        
        logger.info(f"Parsed JSON: X={len(x_labels)}, Y={len(y_labels)}, Data={len(data_values)}")
        
        # Build DataFrame based on what we have
        rows = []
        
        # If we have explicit data values and x_labels of same length, pair them as category:value
        if data_values and len(data_values) == len(x_labels):
            for label, value in zip(x_labels, data_values):
                rows.append({'Category': label, 'Value': value})
        
        # For bar/column charts: X-axis labels ARE often the bar values
        # E.g., a chart with bars labeled 20, 40, 60, 80, 100, 120
        elif x_labels:
            # Check if x_labels are numeric (indicates they're values, not categories)
            numeric_x_labels = []
            for label in x_labels:
                try:
                    numeric_x_labels.append(float(label))
                except (ValueError, TypeError):
                    numeric_x_labels = None
                    break
            
            if numeric_x_labels:
                # X-axis labels are numeric - treat as bar values
                for i, value in enumerate(numeric_x_labels):
                    rows.append({'Bar': i + 1, 'Value': value})
            else:
                # X-axis labels are text categories
                for i, label in enumerate(x_labels):
                    rows.append({'Category': label, 'Index': i + 1})
        
        # If we only have data values (text on bars)
        elif data_values:
            for i, val in enumerate(data_values):
                rows.append({'Index': i + 1, 'Value': val})
        
        # Fallback: create from y_labels (axis range)
        elif y_labels:
            # Y-axis labels are usually just the scale, not actual data
            # But include them for completeness
            for i, val in enumerate(y_labels):
                rows.append({'Y_Scale': val})
        
        if rows:
            df = pd.DataFrame(rows)
            # Try to convert numeric columns
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            logger.info(f"Built DataFrame with {len(df)} rows from structured JSON")
            return df
        
        return pd.DataFrame()
    
    def _parse_pipe_separated(self, text: str) -> pd.DataFrame:
        """Parse pipe-separated format like 'Category | Value'"""
        lines = text.strip().split('\n')
        rows = []
        for line in lines:
            line = line.strip()
            if not line or all(c in '|- \t' for c in line):
                continue
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if parts:
                rows.append(parts)
        
        if rows:
            max_cols = max(len(row) for row in rows)
            columns = [f"Column_{i+1}" for i in range(max_cols)]
            
            normalized_rows = []
            for row in rows:
                while len(row) < max_cols:
                    row.append('')
                normalized_rows.append(row[:max_cols])
            
            df = pd.DataFrame(normalized_rows, columns=columns)
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            
            logger.info(f"Parsed pipe format: {len(df)} rows, {len(df.columns)} columns")
            return df
        return pd.DataFrame()
    
    def _parse_ocr_output(self, text: str) -> pd.DataFrame:
        """
        Parse OCR output from charts.
        Extracts numeric values and associated labels.
        """
        lines = text.strip().split('\n')
        
        # Extract all numbers and labels
        numbers = []
        labels = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points and asterisks
            line = re.sub(r'^[\*\-\•]\s*', '', line)
            
            # Check if line is purely numeric
            num_match = re.match(r'^[\d.,]+$', line)
            if num_match:
                try:
                    num = float(line.replace(',', ''))
                    numbers.append(num)
                except:
                    labels.append(line)
            else:
                # Check for mixed content like "Label 123" or "123 Label"
                mixed = re.match(r'^(.+?)\s+(\d+[\d.,]*)$|^(\d+[\d.,]*)\s+(.+)$', line)
                if mixed:
                    if mixed.group(1) and mixed.group(2):
                        labels.append(mixed.group(1).strip())
                        try:
                            numbers.append(float(mixed.group(2).replace(',', '')))
                        except:
                            pass
                    elif mixed.group(3) and mixed.group(4):
                        try:
                            numbers.append(float(mixed.group(3).replace(',', '')))
                        except:
                            pass
                        labels.append(mixed.group(4).strip())
                else:
                    # Non-numeric line - could be a label, title, or axis label
                    if len(line) < 50:  # Probably a shorter label, not title/description
                        labels.append(line)
        
        logger.info(f"OCR extracted: {len(numbers)} numbers, {len(labels)} labels")
        
        # Build DataFrame
        if numbers:
            # If we have labels and numbers, pair them
            if labels and len(labels) >= 1:
                # Filter out likely axis values and titles
                data_labels = [l for l in labels if not any(
                    keyword in l.lower() for keyword in ['chart', 'title', 'axis', 'label', 'index']
                )]
                
                # Create rows with available data
                if len(data_labels) == len(numbers):
                    df = pd.DataFrame({
                        'Label': data_labels,
                        'Value': numbers
                    })
                else:
                    # Just return numbers with index
                    df = pd.DataFrame({
                        'Index': list(range(1, len(numbers) + 1)),
                        'Value': numbers
                    })
            else:
                # Just numbers
                df = pd.DataFrame({
                    'Index': list(range(1, len(numbers) + 1)),
                    'Value': numbers
                })
            
            logger.info(f"Built DataFrame with {len(df)} rows")
            return df
        
        # Fallback: return text as single column
        if lines:
            return pd.DataFrame({'Text': [l for l in lines if l.strip()]})
        
        return pd.DataFrame()

    def calculate_confidence(self, df: pd.DataFrame, heuristics: Dict[str, Any]) -> float:
        """
        Calculates a confidence score based on consistency between Model and Heuristics.
        Base Score: 1.0
        Penalties:
        - 0.3 if values coincide with Heuristic Range (widely off)
        - 0.1 if rows < 2
        - 0.2 if no generic numeric columns found (parsing fail)
        """
        score = 1.0
        
        if df.empty:
            return 0.0
            
        if len(df) < 2:
            score -= 0.1
            
        # Check numerical range
        y_min_h = heuristics.get('y_min', 0)
        y_max_h = heuristics.get('y_max', 0)
        
        # Identify numeric columns in DF
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) == 0:
             # Try to convert object cols to numeric
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True))
                except:
                    pass
            numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            # Check if values fall roughly within range
            # Heuristic range might be strict (min tick to max tick), data values should be INSIDE
            # But sometimes ticks are 0-100 and data is 50. That's fine.
            # If heuristic max is 100, and data has 5000, that's a problem.
            
            # Get max value in DF
            df_max = df[numeric_cols].max().max()
            
            # Allow some tolerance (e.g., heuristic missed the top tick)
            # If df_max is > 2x heuristic max (and heuristic max > 0), penalize
            if y_max_h > 0 and df_max > (y_max_h * 2.0):
                logger.info(f"Confidence Penalty: Data Max {df_max} >>> Heuristic Max {y_max_h}")
                score -= 0.3
        else:
            score -= 0.2 # No numbers found?
            
        return max(0.0, score)

    def process(self, image_path: str, florence_raw_text: str) -> Dict[str, Any]:
        """
        Main fusion process.
        """
        # Step 1: Heuristics extraction (Ground Truth / Metadata)
        heuristics_meta = extract_metadata(image_path)
        
        # Step 2: Parse Florence Text
        df = self.parse_florence_output(florence_raw_text)
        
        # Step 3: Validate and Score
        confidence = self.calculate_confidence(df, heuristics_meta)
        
        # Step 4: Validate Data Content vs Heuristics (Injection)
        # We inject the Title and Units from Heuristics into the response metadata
        # We do NOT overwrite the DF data, but we could filter it if we were more aggressive.
        
        result = {
            "data": df.fillna('').to_dict(orient='records'),
            "columns": df.columns.tolist(),
            "metadata": {
                "title": heuristics_meta.get('title', ''),
                "units": heuristics_meta.get('units', ''),
                "y_axis_range": {
                    "min": heuristics_meta.get('y_min'),
                    "max": heuristics_meta.get('y_max')
                }
            },
            "validation": {
                "confidence": confidence,
                "heuristic_check": heuristics_meta # Include full debug info
            }
        }
        
        return result
