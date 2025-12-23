import fitz
import joblib
import pandas as pd
import os
import sys
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def get_output_path(filename):
    """Handles output directory creation."""
    output_dir = "./data/raw"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)

def load_local_or_remote_model(model_path='src/models/export/layout_model.joblib'):
    """Loads the model, verifying existence."""
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}. Please run trainer.py first.")
        sys.exit(1)
    logger.info(f"Loading model from {model_path}...")
    return joblib.load(model_path)

def anonymize_text(text):
    """Replaces real text with Lorem Ipsum matching word count."""
    words = text.strip().split()
    if not words: return ""
    vocab = ["Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", 
             "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore", 
             "magna", "aliqua", "ut", "enim", "ad", "minim", "veniam"]
    
    result = []
    for i, _ in enumerate(words):
        word = vocab[i % len(vocab)]
        if words[i].endswith('.'): word += "."
        elif words[i].endswith(','): word += ","
        result.append(word)
        
    return " ".join(result)

def generate_professional_latex(pdf_path):
    """
    Reconstructs the PDF using the trained model and accurate positioning.
    """
    model = load_local_or_remote_model()
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Could not open PDF: {e}")
        return

    # LaTeX Header
    latex_content = [
        "\\documentclass{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage{geometry}",
        "\\usepackage[absolute,overlay]{textpos}", # Crucial for positioning
        "\\usepackage{xcolor}",
        "\\usepackage{helvet}", 
        "\\renewcommand{\\familydefault}{\\sfdefault}",
        "\\setlength{\\TPHorizModule}{1pt}",
        "\\setlength{\\TPVertModule}{1pt}",
        "\\textblockorigin{0pt}{0pt}",
        "\\begin{document}",
        "\\pagestyle{empty}"
    ]
    
    total_pages = len(doc)
    logger.info(f"Reconstructing {pdf_path} ({total_pages} pages)...")

    for page_num, page in enumerate(doc):
        w_pt, h_pt = page.rect.width, page.rect.height
        
        # Define page geometry match
        latex_content.append(f"\\newgeometry{{papersize={{{w_pt}pt,{h_pt}pt}},margin=0pt}}")
        if page_num > 0: latex_content.append("\\clearpage")
        latex_content.append("\\mbox{}") # Empty box to initialize page

        # Extract features (Matches Processor Logic)
        blocks = page.get_text("dict")["blocks"]
        page_data = []
        
        for b in blocks:
            # Images
            if b["type"] == 1:
                x0, y0, x1, y1 = b["bbox"]
                width = x1 - x0
                height = y1 - y0
                latex_content.append(
                    f"\\begin{{textblock*}}{{{width}pt}}({x0}pt,{y0}pt)"
                    f"\\fcolorbox{{gray!50}}{{gray!20}}{{\\vbox to {height}pt{{\\vfill\\centering IMAGE\\vfill}}}}"
                    f"\\end{{textblock*}}"
                )
                continue

            # Text (Line-based)
            if "lines" in b:
                for line in b["lines"]:
                    line_text_parts = []
                    sizes = []
                    bolds = []
                    
                    for s in line["spans"]:
                        line_text_parts.append(s["text"])
                        sizes.append(s["size"])
                        bolds.append("bold" in s["font"].lower())
                    
                    full_text = " ".join(line_text_parts).strip()
                    if not full_text: continue
                    
                    avg_size = sum(sizes)/len(sizes)
                    is_bold = sum(bolds) > (len(bolds)/2)
                    x0, y0, x1, y1 = line["bbox"]
                    
                    page_data.append({
                        'text': full_text,
                        'font_size': avg_size,
                        'is_bold': 1 if is_bold else 0,
                        'x0': x0, 'y0': y0,
                        'width': x1 - x0,
                        'height': y1 - y0,
                        'page_number': page_num
                    })

        # --- Prediction & LaTeX Generation ---
        if page_data:
            df = pd.DataFrame(page_data)
            
            # Feature Engineering (Matches Trainer)
            df['dist_prev_y'] = df['y0'].diff().fillna(0)
            df['center_dev'] = abs((w_pt/2) - (df['x0'] + df['width']/2))
            df['is_first_page'] = (df['page_number'] == 0).astype(int)
            
            std_size = df['font_size'].std()
            if np.isnan(std_size) or std_size == 0: std_size = 1
            df['rel_font_size'] = (df['font_size'] - df['font_size'].mean()) / std_size
            
            df['aspect_ratio'] = df['width'] / (df['height'] + 0.1)

            features = ['font_size', 'rel_font_size', 'is_bold', 'x0', 'y0', 
                        'width', 'dist_prev_y', 'center_dev', 'is_first_page', 'aspect_ratio']
            
            # Predict
            df['prediction'] = model.predict(df[features])

            for _, row in df.iterrows():
                fake_text = anonymize_text(row['text'])
                
                # Styles
                prefix = "{"
                suffix = "}"
                
                if row['prediction'] == 'title':
                    prefix = "\\huge\\textbf{"
                elif row['prediction'] == 'header':
                    prefix = "\\large\\textbf{"
                elif row['is_bold']:
                    prefix = "\\textbf{"

                # Prevent overlap: Use parbox inside textblock to force wrap or cut
                # We add a small buffer (+2pt) to width to handle font metric diffs
                block_width = row['width'] + 5

                latex_content.append(
                    f"\\begin{{textblock*}}{{{block_width}pt}}({row['x0']}pt,{row['y0']}pt)"
                    f"\\fontsize{{{row['font_size']}}}{{{row['font_size'] * 1.2}}}\\selectfont"
                    f"\\parbox{{{block_width}pt}}{{\\raggedright {prefix}{fake_text}{suffix}}}"
                    f"\\end{{textblock*}}"
                )
        
        logger.info(f"Page {page_num + 1} processed.")

    latex_content.append("\\end{document}")
    
    output_filename = os.path.basename(pdf_path).replace(".pdf", "_reconstructed.tex")
    output_file = get_output_path(output_filename)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_content))
    
    logger.info(f"Success! LaTeX saved at: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_professional_latex(sys.argv[1])
    else:
        print("Usage: python inference.py <pdf_path>")