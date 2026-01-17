import joblib
import argparse
import os
from datetime import datetime

class AcademicEngine:
    def __init__(self, model_path):
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)

    def _get_header(self):
        return r"""\documentclass[10pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1.5cm, top=1cm, bottom=1.5cm]{geometry}
\usepackage{multicol}
\usepackage{wrapfig}
\usepackage{caption}
\usepackage{booktabs}
\usepackage{tcolorbox}
\usepackage{lipsum}
\usepackage{microtype}

% Configuração de legenda e espaçamento
\captionsetup{font=small, labelfont=bf, skip=5pt}
\setlength{\intextsep}{5pt} % Espaço acima/abaixo do componente
\setlength{\columnsep}{15pt}

\pagestyle{empty}
\raggedbottom

\begin{document}
\enlargethispage{2cm} % Força o conteúdo a caber na página 1
"""

    def _get_footer(self):
        return r"\end{document}"

    def _generate_component(self, c_type, title, label="Legenda padrão do componente"):
        if c_type == "image":
            return r"""\begin{tcolorbox}[colback=gray!5, colframe=black, arc=0mm, center]
\centering \vspace{1.2cm} \Large \textbf{IMAGEM} \vspace{1.2cm}
\end{tcolorbox}
\captionof{figure}{""" + label + " - " + title + "}"
        else:
            return r"""\begin{center}
\small
\begin{tabular}{@{}lll@{}} \toprule
\textbf{Parâmetro} & \textbf{Valor} & \textbf{Status} \\ \midrule
Layout & Acadêmico & Final \\
Estabilidade & Blindada & OK \\ \bottomrule
\end{tabular}
\captionof{table}{""" + label + " - " + title + "}" + r"\end{center}"

    def layout_full(self, _):
        return r"\section*{Relatório Full}\begin{multicols}{2}\lipsum[1-10]\end{multicols}"

    def layout_top(self, c_type):
        comp = self._generate_component(c_type, "Topo")
        return f"{comp}\n\\vspace{{5pt}}\n\\begin{{multicols}}{{2}}\\lipsum[1-8]\\end{{multicols}}"

    def layout_bottom(self, c_type):
        comp = self._generate_component(c_type, "Bottom")
        return f"\\begin{{multicols}}{{2}}\\lipsum[1-8]\\end{{multicols}}\n\\vfill\n{comp}"

    def layout_middle(self, c_type):
        comp = self._generate_component(c_type, "Middle")
        return f"\\begin{{multicols}}{{2}}\\lipsum[1-3]\\end{{multicols}}\n{comp}\n\\begin{{multicols}}{{2}}\\lipsum[4-7]\\end{{multicols}}"

    def layout_side(self, side, pos, c_type):
        # Ajustamos o número de linhas (15) para garantir o espaçamento da legenda
        comp = self._generate_component(c_type, f"Lateral {pos.capitalize()}")
        
        if pos == "top":
            return f"\\begin{{wrapfigure}}[15]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[1-10]"
        elif pos == "middle":
            return f"\\lipsum[1-3]\n\\begin{{wrapfigure}}[15]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[4-10]"
        else: # bottom
            return f"\\lipsum[1-6]\n\\begin{{wrapfigure}}[15]{{{side}}}{{0.48\\textwidth}}\n{comp}\n\\end{{wrapfigure}}\n\\lipsum[7-10]"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("layout", choices=["full", "top", "bottom", "middle", "left", "right"])
    parser.add_argument("type", choices=["image", "table"], nargs="?", default="image")
    parser.add_argument("--pos", choices=["top", "middle", "bottom"], default="top")
    
    args = parser.parse_args()
    model_path = '/home/caio/Latex_ia/src/models/export/layout_model.joblib'
    engine = AcademicEngine(model_path)
    
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
    filename = f"FINAL_PAGE_{args.layout}_{args.pos}_{ts}.tex"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_tex)
    
    print(f"✅ Versão Final Única Página Gerada: {filename}")

if __name__ == "__main__":
    main()