import fitz
import joblib
import pandas as pd
import os
import sys
import urllib.request

def get_output_path(filename):
    docker_output = "/app/output"
    local_output = "./output"
    if os.path.exists(docker_output):
        return os.path.join(docker_output, filename)
    if not os.path.exists(local_output):
        os.makedirs(local_output, exist_ok=True)
    return os.path.join(local_output, filename)

def load_model(model_url):
    local_model_path = 'src/models/export/layout_model.joblib'
    
    if not os.path.exists(local_model_path):
        print(f"Model not found locally. Downloading from: {model_url}")
        os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
        try:
            urllib.request.urlretrieve(model_url, local_model_path)
            print("Model downloaded successfully.")
        except Exception as e:
            print(f"Error downloading model: {e}")
            sys.exit(1)
            
    return joblib.load(local_model_path)

def anonymize_text(text):
    words = text.strip().split()
    if not words: return ""
    placeholders = ["Lorem", "Ipsum", "Dolor", "Sit", "Amet"]
    return " ".join([placeholders[i % len(placeholders)] for i in range(len(words))])

def generate_professional_latex(pdf_path, model_url):
    model = load_model(model_url)
    doc = fitz.open(pdf_path)
    
    latex_content = [
        "\\documentclass{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{geometry}",
        "\\usepackage[absolute,overlay]{textpos}",
        "\\usepackage{xcolor}",
        "\\setlength{\\TPHorizModule}{1pt}",
        "\\setlength{\\TPVertModule}{1pt}",
        "\\textblockorigin{0pt}{0pt}",
        "\\begin{document}",
        "\\pagestyle{empty}"
    ]
    
    total_pages = len(doc)
    print(f"Starting reconstruction: {total_pages} pages identified")

    for page_num, page in enumerate(doc):
        w_pt, h_pt = page.rect.width, page.rect.height
        latex_content.append(f"\\newgeometry{{papersize={{{w_pt}pt,{h_pt}pt}},margin=0pt}}")
        if page_num > 0: latex_content.append("\\clearpage")
        latex_content.append("~") 

        blocks = page.get_text("dict")["blocks"]
        page_data = []
        used_coords = set()

        for b in blocks:
            if b["type"] == 1:
                x0, y0, x1, y1 = b["bbox"]
                latex_content.append(
                    f"\\begin{{textblock*}}{{{x1-x0}pt}}({x0}pt,{y0}pt)"
                    f"\\fcolorbox{{gray!30}}{{gray!10}}{{\\vbox to {y1-y0}pt{{\\vfill\\hbox to {x1-x0}pt{{\\hfill OBJ\\hfill}}\\vfill}}}}"
                    f"\\end{{textblock*}}"
                )
                continue

            if "lines" in b:
                for l in b["lines"]:
                    coord_key = (round(l["bbox"][0], 0), round(l["bbox"][1], 0))
                    if coord_key in used_coords: continue
                    
                    line_text = " ".join([s["text"] for s in l["spans"] if s["text"].strip()])
                    if not line_text: continue
                    
                    page_data.append({
                        'text': line_text, 'font_size': l["spans"][0]["size"],
                        'is_bold': 1 if "bold" in l["spans"][0]["font"].lower() else 0,
                        'x0': l["bbox"][0], 'y0': l["bbox"][1],
                        'width': l["bbox"][2] - l["bbox"][0], 'page_number': page_num
                    })
                    used_coords.add(coord_key)
        
        if page_data:
            df = pd.DataFrame(page_data)
            df['dist_prev_y'] = df['y0'].diff().fillna(0)
            df['center_dev'] = abs((w_pt/2) - df['x0'])
            df['is_first_page'] = (df['page_number'] == 0).astype(int)
            df['rel_font_size'] = (df['font_size'] - df['font_size'].mean()) / (df['font_size'].std() + 0.001)
            
            features = ['font_size', 'rel_font_size', 'is_bold', 'x0', 'y0', 'dist_prev_y', 'center_dev', 'is_first_page']
            df['prediction'] = model.predict(df[features])

            for _, row in df.iterrows():
                fake_text = anonymize_text(row['text'])
                style = ""
                if row['prediction'] == 'title': style = "\\huge\\textbf"
                elif row['prediction'] == 'header': style = "\\large\\textbf"
                elif row['is_bold']: style = "\\textbf"

                latex_content.append(
                    f"\\begin{{textblock*}}{{{row['width']+20}pt}}({row['x0']}pt,{row['y0']}pt)"
                    f"\\fontsize{{{row['font_size']}}}{{{row['font_size']}}}\\selectfont\\noindent "
                    f"\\smash{{{style}{{{fake_text}}}}}"
                    f"\\end{{textblock*}}"
                )
        
        print(f"[{page_num + 1}/{total_pages}] Page processed")

    latex_content.append("\\end{document}")
    output_file = get_output_path("reconstructed_layout.tex")
    with open(output_file, "w") as f:
        f.write("\n".join(latex_content))
    print(f"Reconstruction completed. Output saved at: {output_file}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    model_url = os.getenv("MODEL_URL")
    if not model_url:
        print("Error: MODEL_URL environment variable not set.")
        sys.exit(1)

    if len(sys.argv) > 1:
        generate_professional_latex(sys.argv[1], model_url)
    else:
        print("Usage: python inference.py <pdf_path>")