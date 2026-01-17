import joblib
import pandas as pd
import argparse
import os

class AcademicEngine:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)

    def _get_header(self):
        # top=1cm sobe o texto ao máximo. inclusion de 'needspace' para evitar quebras ruins.
        return r"""\documentclass[10pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=2cm, top=1cm, bottom=2cm]{geometry}
\usepackage{multicol}
\usepackage{graphicx}
\usepackage{wrapfig}
\usepackage{caption}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{lipsum}
\usepackage{tcolorbox}
\usepackage{needspace}

\setlength{\columnsep}{20pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}

\begin{document}
"""

    def _get_footer(self):
        return r"\end{document}"

    def _generate_content(self, content_type, title="Componente"):
        """Gera o código LaTeX para uma Imagem ou Tabela sem ambiente flutuante."""
        if content_type == "image":
            return r"""
    \begin{tcolorbox}[colback=gray!5, colframe=black, arc=0mm, center, title=""" + title + r"""]
        \centering \vspace{1.5cm} \Large \textbf{ESPAÇO PARA IMAGEM} \vspace{1.5cm}
    \end{tcolorbox}"""
        else:  # Table
            return r"""
    \begin{center}
    \small
    \captionof{table}{Dados Técnicos do Componente}
    \begin{tabular}{@{}lll@{}} \toprule
    \textbf{Parâmetro} & \textbf{Valor} & \textbf{Status} \\ \midrule
    Layout Estilo & Acadêmico & Ativo \\
    Processamento & Random Forest & Validado \\
    Posicionamento & Estático & OK \\ \bottomrule
    \end{tabular}
    \end{center}"""

    # --- GERADORES DE ESTRUTURA ---

    def layout_full(self, _):
        return r"\section*{Relatório Completo}\begin{multicols}{2}\lipsum[1-12]\end{multicols}"

    def layout_top(self, c_type):
        content = self._generate_content(c_type, "Destaque Superior")
        # Texto começa imediatamente após o conteúdo do topo
        return f"{content}\n\\vspace{{-0.2cm}}\n\\section*{{Análise de Topo}}\n\\begin{{multicols}}{{2}}\\lipsum[1-8]\\end{{multicols}}"

    def layout_bottom(self, c_type):
        content = self._generate_content(c_type, "Análise de Rodapé")
        # Multicols preenche a página e o vfill empurra o conteúdo para a última linha da página 1
        return f"\\section*{{Análise de Base}}\n\\begin{{multicols}}{{2}}\\lipsum[1-8]\\end{{multicols}}\n\\vfill\n{content}"

    def layout_left(self, c_type):
        content = self._generate_content(c_type, "Lateral Esquerda")
        # wrapfigure configurado para não flutuar e ocupar espaço exato
        width = "0.45\\textwidth"
        return f"\\section*{{Estudo Lateral Esquerdo}}\n\\begin{{wrapfigure}}{{l}}{{{width}}}\n{content}\n\\end{{wrapfigure}}\n\\lipsum[1-10]"

    def layout_right(self, c_type):
        content = self._generate_content(c_type, "Lateral Direita")
        width = "0.45\\textwidth"
        return f"\\section*{{Estudo Lateral Direito}}\n\\begin{{wrapfigure}}{{r}}{{{width}}}\n{content}\n\\end{{wrapfigure}}\n\\lipsum[1-10]"

def main():
    parser = argparse.ArgumentParser(description="Maestro de Layouts Profissional")
    parser.add_argument("layout", choices=["full", "top", "bottom", "left", "right"], help="Estrutura da página")
    parser.add_argument("type", choices=["image", "table"], nargs='?', default="image", help="Tipo de conteúdo")
    
    args = parser.parse_args()
    
    # Simulação de carregamento do modelo (caminho que você usa)
    model_path = '/home/caio/Latex_ia/src/models/export/layout_model.joblib'
    engine = AcademicEngine(model_path)
    
    mapping = {
        "full": engine.layout_full,
        "top": engine.layout_top,
        "bottom": engine.layout_bottom,
        "left": engine.layout_left,
        "right": engine.layout_right
    }

    content = mapping[args.layout](args.type)
    final_tex = engine._get_header() + content + engine._get_footer()

    filename = f"layout_{args.layout}_{args.type}.tex"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_tex)
    
    print(f"✅ Layout {args.layout.upper()} ({args.type.upper()}) gerado com margens otimizadas em: {filename}")

if __name__ == "__main__":
    main()