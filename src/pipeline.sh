set -e
mkdir -p docs notebooks outputs/charts outputs/tables powerbi data/raw
python src/run_pipeline.py
python src/build_report.py
