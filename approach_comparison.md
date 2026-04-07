# Project Approach Analysis: Chart-to-Table Extraction

## Executive Summary
This document provides a comparative analysis between the originally proposed methodologies for the Chart-to-Table Extraction project and the final implemented solution. Our team successfully delivered a robust, automated system that converts scientific chart images into structured data tables. We adopted a **Hybrid AI-Neurosymbolic Approach**, effectively merging the "Reasoning MLLM" track with deterministic OCR precision to achieve high fidelity and reproducibility.

## 1. Original Proposed Approaches

The initial problem statement outlined two primary distinct paths for solving the chart extraction challenge:

### A. Heuristic Pipeline (Native CV)
*   **Methodology**: Relies on traditional Computer Vision (OpenCV) to detect geometric primitives.
*   **Workflow**:
    *   Detect chart type via lightweight CNN.
    *   Use OCR for text labels.
    *   Detect axes lines and tick marks via edge detection.
    *   Extract bars/lines/points using contour filtering and color clustering.
    *   Map pixels to data values using geometric logic.
*   **Pros**: Explicit control over every step; explainable geometry.
*   **Cons**: Extremely brittle; requires custom logic for every chart variation (stacked bars, multi-lines, different legends); struggles with occlusion and complex layouts.

### B. Reasoning MLLM Track (Vision-Language Models)
*   **Methodology**: Utilizes large pre-trained Vision-Language Models (VLMs) like UniChart or MatCha to directly "read" the chart and output a table.
*   **Workflow**:
    *   Feed image to VLM.
    *   Use tool-augmented prompting (providing OCR text as hints).
    *   Model generates CSV/JSON directly.
*   **Pros**: Handles high variability and semantic understanding (e.g., reading a legend without explicit bounding boxes) much better than heuristics.
*   **Cons**: Prone to "hallucination" (generating plausible but incorrect numbers); precise coordinate mapping can be fuzzy.

---

## 2. Our Implemented Solution: The DePlot + OCR Hybrid

We chose to build upon the **Reasoning MLLM Track**, identifying it as the most scalable solution for modern scientific charts, but we engineered a specific pipeline to mitigate its primary weakness (numerical precision).

### Core Architecture
Instead of a pure "black box" VLM or a brittle CV pipeline, we implemented a **DePlot-based Hybrid System**:

1.  **Semantic Engine (DePlot)**:
    *   We utilized **DePlot** (based on Google's MatCha/T5), a state-of-the-art model specifically fine-tuned for chart-to-table translation.
    *   **Role**: It acts as the "brain," understanding the chart's structure, the relationship between legends and data series, and the overall layout. It generates a linearized text representation of the underlying table.

2.  **Precision Layer (Tesseract OCR)**:
    *   We integrated **Tesseract OCR** as a parallel processing stream.
    *   **Role**: It acts as the "eyes," providing raw, ground-truth text extraction for axis labels, tick values, and titles.

3.  **Reconciliation Pipeline (The "Smart" Logic)**:
    *   Our custom post-processing algorithms merge the structural understanding from DePlot with the literal text from OCR.
    *   This allows us to correct DePlot's potential hallucinations (e.g., if DePlot predicts "10.5" but OCR clearly sees "10.8", we prioritize the OCR evidence while keeping DePlot's structure).

## 3. Comparative Advantage

| Feature | Heuristic Approach (Original A) | Pure MLLM (Original B) | **Our Hybrid Approach** |
| :--- | :--- | :--- | :--- |
| **Generalization** | Low (Needs rules for every chart type) | High (Learns from vast data) | **High** (Leverages DePlot's pre-training) |
| **Precision** | High (if geometry is perfect) | Moderate (Hallucination risk) | **High** (OCR corrects MLLM) |
| **Robustness** | Low (Fails on noise/occlusion) | High (Semantic understanding) | **High** (Best of both worlds) |
| **Maintenance** | High (Complex codebase of rules) | Low (Model weights) | **Moderate** (Pipeline logic + Model) |

## 4. Conclusion
Our approach effectively fulfills the "Reasoning MLLM track" suggestion while incorporating the "Ensembling" recommendation (blending CV values with MLLM output). By avoiding the brittle complexity of the Heuristic CV track and mitigating the precision risks of a pure VLM, we have delivered a system that is both **semantically smart** and **numerically accurate**, suitable for the rigorous demands of scientific data extraction.
