import os
import urllib.request

url = "https://github.com/numpy/numpy/releases/download/v2.2.6/numpy-2.2.6-cp313-cp313-manylinux_2_17_x86_64.whl"
out = os.path.join("deps", "numpy-2.2.6-cp313-cp313-manylinux_2_17_x86_64.whl")

os.makedirs("deps", exist_ok=True)
print(f"Downloading: {url}\n  to: {out}")
urllib.request.urlretrieve(url, out)
print("다운로드 완료:", out)
