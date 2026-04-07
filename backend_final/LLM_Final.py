#!/usr/bin/env python3
"""
LLM-Powered Chart-to-Table Converter using Gemini Vision
High accuracy extraction using advanced vision LLM
"""

import os
import re
import io
import argparse
import logging
import json
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

# Gemini SDK
try:
    from google import genai
    HAS_GEMINI_SDK = True
except Exception:
    genai = None
    HAS_GEMINI_SDK = False

# -------------------------
# Configuration
# -------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", 'Paste Your Own API Key')
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Initialize Gemini client
if HAS_GEMINI_SDK and GOOGLE_API_KEY:
    gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
else:
    gemini_client = None
    logging.error("Gemini SDK not available or API key not set!")

# -------------------------
# LLM-Based Table Extraction
# -------------------------

def extract_table_with_gemini(image: Image.Image, verbose: bool = False) -> Dict[str, Any]:
    """
    Use Gemini Vision to directly extract table data from chart.
    This is the primary method - highly accurate for all chart types.
    """
    if gemini_client is None:
        return {"success": False, "error": "Gemini client not available"}
    
    # Comprehensive prompt for maximum accuracy
    prompt = """Analyze this chart/graph image and extract ALL the data as a complete table.

INSTRUCTIONS:
1. Identify the chart type (bar chart, line chart, pie chart, etc.)
2. Extract EVERY data point with its label and value
3. If there are multiple series/categories, include all of them
4. Preserve the exact labels as shown in the chart
5. Extract numerical values as accurately as possible
6. If values have units (%, $, etc.), include them

OUTPUT FORMAT:
Return ONLY a valid JSON object with this structure:
{
  "chart_type": "type of chart",
  "title": "chart title if visible",
  "data": [
    {"label": "category1", "value": number, "series": "series_name"},
    {"label": "category2", "value": number, "series": "series_name"}
  ]
}

IMPORTANT:
- Return ONLY the JSON, no other text
- Include ALL data points you can see
- For pie charts, extract all slices
- For bar/line charts, extract all bars/points
- Be precise with numbers
- If a value is a percentage, include the number only (e.g., 25 not 25%)

Extract the data now:"""

    try:
        if verbose:
            logging.info("Calling Gemini Vision for table extraction...")
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[prompt, image]
        )
        
        text = getattr(response, "text", "") or ""
        
        if verbose:
            logging.info(f"Gemini raw response:\n{text}")
        
        # Clean up the response
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        
        # Try to parse as JSON
        try:
            data = json.loads(text)
            return {
                "success": True,
                "data": data,
                "raw": text
            }
        except json.JSONDecodeError as e:
            if verbose:
                logging.warning(f"Failed to parse JSON: {e}")
            
            # Fallback: try to extract data manually
            return {
                "success": False,
                "error": f"JSON parse error: {e}",
                "raw": text
            }
    
    except Exception as e:
        logging.error(f"Gemini extraction failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def extract_table_with_structured_prompt(image: Image.Image, verbose: bool = False) -> Dict[str, Any]:
    """
    Alternative approach: Use a more structured prompt that asks for CSV format
    """
    if gemini_client is None:
        return {"success": False, "error": "Gemini client not available"}
    
    prompt = """Look at this chart carefully and extract ALL the data into a CSV table format.

REQUIREMENTS:
- Extract EVERY category/label you see
- Extract EVERY value accurately
- Include column headers
- Format as proper CSV (comma-separated)
- Do NOT skip any data points

Return the data as a CSV table with headers. For example:
Category,Value
Item1,25
Item2,30
Item3,45

Now extract the complete data from this chart as CSV:"""

    try:
        if verbose:
            logging.info("Calling Gemini with CSV prompt...")
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[prompt, image]
        )
        
        text = getattr(response, "text", "") or ""
        
        if verbose:
            logging.info(f"Gemini CSV response:\n{text}")
        
        # Clean up response
        text = text.strip()
        
        # Remove markdown code blocks
        if "```" in text:
            text = re.sub(r"```(?:csv)?\n?", "", text)
            text = re.sub(r"\n?```", "", text)
        
        return {
            "success": True,
            "csv_text": text,
            "raw": text
        }
    
    except Exception as e:
        logging.error(f"Gemini CSV extraction failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def json_to_dataframe(json_data: dict, verbose: bool = False) -> Optional[pd.DataFrame]:
    """Convert Gemini JSON output to pandas DataFrame"""
    try:
        if "data" not in json_data:
            return None
        
        data_list = json_data["data"]
        if not data_list:
            return None
        
        # Check if we have series information
        has_series = any("series" in item for item in data_list)
        
        if has_series:
            # Multi-series data - pivot into wide format
            df = pd.DataFrame(data_list)
            
            # If series column exists, pivot
            if "series" in df.columns:
                df_pivot = df.pivot_table(
                    index="label",
                    columns="series",
                    values="value",
                    aggfunc="first"
                ).reset_index()
                return df_pivot
            else:
                # No series column, use as-is
                return df[["label", "value"]]
        else:
            # Simple data
            df = pd.DataFrame(data_list)
            
            # Ensure we have at least label and value columns
            if "label" in df.columns and "value" in df.columns:
                return df[["label", "value"]]
            else:
                return df
    
    except Exception as e:
        if verbose:
            logging.warning(f"JSON to DataFrame conversion failed: {e}")
        return None


def csv_text_to_dataframe(csv_text: str, verbose: bool = False) -> Optional[pd.DataFrame]:
    """Convert CSV text to pandas DataFrame"""
    try:
        # Use StringIO to read CSV
        from io import StringIO
        df = pd.read_csv(StringIO(csv_text))
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Try to convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
        
        return df
    
    except Exception as e:
        if verbose:
            logging.warning(f"CSV to DataFrame conversion failed: {e}")
        return None


# -------------------------
# Main Processing Function
# -------------------------

def process_chart_image(
    image_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Process chart image using LLM-first approach
    
    Returns dict with:
    - 'df': pandas DataFrame with extracted data
    - 'method': which method succeeded
    - 'raw': raw response from LLM  
    - 'success': bool
    """
    image = Image.open(image_path).convert("RGB")
    
    if verbose:
        logging.info(f"Processing image: {image_path}")
        logging.info(f"Image size: {image.size}")
    
    # Method 1: JSON-structured extraction (most accurate)
    if verbose:
        logging.info("Trying Method 1: JSON extraction...")
    
    result1 = extract_table_with_gemini(image, verbose=verbose)
    
    if result1.get("success"):
        df = json_to_dataframe(result1["data"], verbose=verbose)
        if df is not None and not df.empty:
            if verbose:
                logging.info("✓ Success with JSON method!")
            return {
                "success": True,
                "df": df,
                "method": "gemini_json",
                "raw": result1.get("raw", ""),
                "chart_type": result1["data"].get("chart_type", "unknown")
            }
            
    # OPTIMIZATION: If Method 1 failed due to Quota/Rate Limit, DO NOT try Method 2.
    # It will just fail again and waste time/requests.
    err_msg_1 = str(result1.get("error", ""))
    if "429" in err_msg_1 or "RESOURCE_EXHAUSTED" in err_msg_1 or "Quota" in err_msg_1:
        if verbose:
            logging.warning("Quota exceeded in Method 1. Skipping Method 2.")
        return {
            "success": False,
            "error": err_msg_1,
            "df": None
        }
    
    # Method 2: CSV extraction (fallback)
    if verbose:
        logging.info("Trying Method 2: CSV extraction...")
    
    result2 = extract_table_with_structured_prompt(image, verbose=verbose)
    
    if result2.get("success"):
        df = csv_text_to_dataframe(result2["csv_text"], verbose=verbose)
        if df is not None and not df.empty:
            if verbose:
                logging.info("✓ Success with CSV method!")
            return {
                "success": True,
                "df": df,
                "method": "gemini_csv",
                "raw": result2.get("raw", "")
            }
    
    # If both methods fail
    error_msg = f"Extraction failed. Method 1 error: {result1.get('error')}. Method 2 error: {result2.get('error')}"
    return {
        "success": False,
        "error": error_msg,
        "df": None
    }


# -------------------------
# CLI / Main
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LLM-Powered Chart-to-Table Converter (Gemini Vision)"
    )
    parser.add_argument("image", help="Path to chart image (png/jpg)")
    parser.add_argument("--out", "-o", help="Output CSV path", default="output.csv")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--json", action="store_true", help="Also save as JSON")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    # Check if Gemini is available
    if gemini_client is None:
        logging.error("ERROR: Gemini SDK not available or API key not set!")
        logging.error("Please install: pip install google-genai")
        logging.error("And set: GOOGLE_API_KEY environment variable")
        return 1
    
    print(f"\n{'='*60}")
    print("LLM-Powered Chart-to-Table Converter")
    print(f"{'='*60}\n")
    
    # Process image
    print(f"📊 Processing: {args.image}")
    result = process_chart_image(args.image, verbose=args.verbose)
    
    if not result["success"]:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return 1
    
    df = result["df"]
    method = result.get("method", "unknown")
    
    print(f"✓ Extraction method: {method}")
    if "chart_type" in result:
        print(f"✓ Chart type: {result['chart_type']}")
    
    # Save CSV
    df.to_csv(args.out, index=False)
    print(f"✓ Saved CSV: {args.out}")
    
    # Optionally save JSON
    if args.json:
        json_path = args.out.replace(".csv", ".json")
        df.to_json(json_path, orient="records", indent=2)
        print(f"✓ Saved JSON: {json_path}")
    
    # Display table
    print(f"\n📋 Extracted Data ({len(df)} rows, {len(df.columns)} columns):")
    print("="*60)
    print(df.to_string(index=False))
    print("="*60)
    
    print(f"\n✅ Success! Data extracted and saved.\n")
    return 0


if __name__ == "__main__":
    exit(main())
