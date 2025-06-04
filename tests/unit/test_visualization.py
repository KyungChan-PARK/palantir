import pandas as pd

from palantir.core.visualization import generate_plotly_html


def test_generate_plotly_html_table():
    df = pd.DataFrame({"a": [1,2]})
    html = generate_plotly_html({"type": "table", "data": df.to_dict()})
    assert html.startswith("<div")

def test_generate_plotly_html_json():
    html = generate_plotly_html({"type": "json", "data": {"a": 1}})
    assert html.startswith("<pre>")

def test_generate_plotly_html_pdf():
    html = generate_plotly_html({"type": "pdf", "text": "abc"*1000})
    assert html.startswith("<pre>")

def test_generate_plotly_html_image():
    html = generate_plotly_html({"type": "image", "vector": [0]*512})
    assert html.startswith("<pre>")

def test_generate_plotly_html_else():
    html = generate_plotly_html({"type": "unknown", "data": "test"})
    assert html.startswith("<pre>") 