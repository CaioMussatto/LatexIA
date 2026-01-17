import joblib
import argparse
import os
from datetime import datetime
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_SRC = os.path.dirname(CURRENT_DIR) # Pasta 'src'
OUTPUT_PATH = os.path.join(BASE_SRC, "output")

os.makedirs(OUTPUT_PATH, exist_ok=True)

DEFAULT_MODEL = os.path.join(CURRENT_DIR, "export", "layout_model.joblib")

class AcademicEngine:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.getenv("MODEL_PATH", DEFAULT_MODEL)
        
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            print(f"✅ Modelo carregado com sucesso de: {model_path}")
        else:
            print(f"⚠️ Aviso: Modelo não encontrado em {model_path}. Lógica padrão ativa.")

    def _get_header(self):
        return r"""\documentclass[10pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[paper=a4paper, top=2cm, bottom=2.5cm, left=2cm, right=2cm]{geometry}
\usepackage{multicol}
\usepackage{wrapfig}
\usepackage{caption}
\usepackage{booktabs}
\usepackage{tcolorbox}
\usepackage{lipsum}
\usepackage{microtype}

\captionsetup{font=small, labelfont=bf, skip=6pt, justification=centering}
\setlength{\columnsep}{20pt}
\setlength{\intextsep}{10pt}

\pagestyle{empty}
\raggedbottom

\begin{document}
\enlargethispage{2cm} % Margem de manobra para evitar quebra por milímetros
"""

    def _get_footer(self):
        return r"\end{document}"

    def _generate_component(self, c_type, title, label="Scientific Data"):
        if c_type == "image":
            return r"""\begin{tcolorbox}[colback=gray!2, colframe=black!80, arc=0mm, center, boxrule=0.5pt]
\centering \vspace{1.2cm} \Large \textbf{IMAGE AREA} \vspace{1.2cm}
\end{tcolorbox}
\vspace{-5pt}
\captionof{figure}{""" + label + " - " + title + "}"
        else:
            return r"""\begin{center}
\small
\begin{tabular}{@{}lll@{}} \toprule
\textbf{Parameter} & \textbf{Value} & \textbf{Status} \\ \midrule
Metric A & 0.95 & Verified \\
Limit & 1 Page & Active \\ \bottomrule
\end{tabular}
\vspace{2pt}
\captionof{table}{""" + label + " - " + title + "}" + r"\end{center}"


    def layout_full(self, _):
        return r"\section*{Complete Report}\begin{multicols}{2}\lipsum[1-8]\end{multicols}"

    def layout_top(self, c_type):
        comp = self._generate_component(c_type, "Top View")
        return f"{comp}\n\\vspace{{10pt}}\n\\begin{{multicols}}{{2}}\\lipsum[1-7]\\end{{multicols}}"

    def layout_bottom(self, c_type):
        comp = self._generate_component(c_type, "Bottom View")
        return f"\\begin{{multicols}}{{2}}\\lipsum[1-7]\\end{{multicols}}\n\\vspace{{\\fill}}\n{comp}"

    def layout_middle(self, c_type):
        comp = self._generate_component(c_type, "Central View")
        return f"\\begin{{multicols}}{{2}}\\lipsum[1-2]\\end{{multicols}}\n{comp}\n\\begin{{multicols}}{{2}}\\lipsum[3-6]\\end{{multicols}}"

    def layout_side(self, side, pos, c_type):
        comp = self._generate_component(c_type, f"Lateral {pos.capitalize()}")
        lines = 16
        
        if pos == "top":
            return f"\\begin{{wrapfigure}}[{lines}]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[1-7]"
        elif pos == "middle":
            return f"\\lipsum[1-2]\n\\begin{{wrapfigure}}[{lines}]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[3-7]"
        else: 
            return f"\\lipsum[1-5]\n\\begin{{wrapfigure}}[{lines}]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[11-12]"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("layout", choices=["full", "top", "bottom", "middle", "left", "right"])
    parser.add_argument("type", choices=["image", "table"], nargs="?", default="image")
    parser.add_argument("--pos", choices=["top", "middle", "bottom"], default="top")
    
    args = parser.parse_args()
    engine = AcademicEngine()
    
    if args.layout in ["left", "right"]:
        side = "l" if args.layout == "left" else "r"
        content = engine.layout_side(side, args.pos, args.type)
    else:
        mapping = {
            "full": engine.layout_full, "top": engine.layout_top,
            "bottom": engine.layout_bottom, "middle": engine.layout_middle
        }
        content = mapping[args.layout](args.type)

    final_tex = engine._get_header() + content + engine._get_footer()
    
    ts = datetime.now().strftime("%H%M%S")
    filename = os.path.join(OUTPUT_PATH, f"FINAL_{args.layout}_{args.pos}_{ts}.tex")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_tex)
    
    print(f"✅ Gerado (Página Única Real): {filename}")

if __name__ == "__main__":
    main()