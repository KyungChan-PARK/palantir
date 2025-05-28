import json

import pandas as pd
import plotly.graph_objs as go


def generate_plotly_html(data):
    if data.get("type") == "table":
        df = pd.DataFrame(data["data"])
        fig = go.Figure(data=[go.Table(header=dict(values=list(df.columns)), cells=dict(values=[df[col] for col in df.columns]))])
        return fig.to_html(full_html=False)
    elif data.get("type") == "json":
        return f"<pre>{json.dumps(data['data'], indent=2, ensure_ascii=False)}</pre>"
    elif data.get("type") == "pdf":
        return f"<pre>{data['text'][:2000]}</pre>"
    elif data.get("type") == "image":
        return f"<pre>CLIP 벡터(512차원): {str(data['vector'][:8])} ...</pre>"
    else:
        return f"<pre>{str(data)[:1000]}</pre>"
