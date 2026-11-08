"""Download the UCI Online Retail dataset (public mirror, ~45 MB) into data/raw/."""
from pathlib import Path
import urllib.request

URL = ("https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/"
       "master/data/retail-data/all/online-retail-dataset.csv")
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "online_retail.csv"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("downloading ...")
    urllib.request.urlretrieve(URL, OUT)
    print("saved", OUT, f"({OUT.stat().st_size/1e6:.1f} MB)")
