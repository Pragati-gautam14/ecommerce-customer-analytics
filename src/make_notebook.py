"""Create + execute a notebook from a list of (kind, source) cells. Usage: make_nb.py cells.py out.ipynb workdir"""
import sys, runpy, nbformat
from nbconvert.preprocessors import ExecutePreprocessor
cells = runpy.run_path(sys.argv[1])["CELLS"]
nb = nbformat.v4.new_notebook()
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.cells = [nbformat.v4.new_markdown_cell(s) if k == "md" else nbformat.v4.new_code_cell(s) for k, s in cells]
ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(nb, {"metadata": {"path": sys.argv[3]}})
nbformat.write(nb, sys.argv[2]); print("wrote", sys.argv[2])
