"""데이터 타입별 Plotly/HTML 시각화 유틸리티.

테이블, JSON, PDF, 이미지 등 다양한 타입을 HTML로 변환한다.
"""
import base64
import json
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import plotly.graph_objs as go
from PIL import Image


def generate_plotly_html(data: Dict[str, Any]) -> str:
    """데이터 타입별 Plotly/HTML 변환.

    Args:
        data: 타입 및 데이터 dict
    Returns:
        str: HTML 문자열
    """
    if data.get("type") == "table":
        df = pd.DataFrame(data["data"])
        row_count = len(df)
        html = ""
        if row_count > 1000:
            html += (
                f"<b>표시: 1000행 (전체 {row_count}행) &nbsp; "
                f"<a href='/download/{data['job_id']}'>CSV 전체 다운로드</a></b><br>"
            )
            df = df.head(1000)
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(values=[df[col] for col in df.columns]),
                )
            ]
        )
        html += fig.to_html(full_html=False)
        return html
    elif data.get("type") == "json":
        return f"<pre>{json.dumps(data['data'], indent=2, ensure_ascii=False)}</pre>"
    elif data.get("type") == "pdf":
        text = data['text']
        if not text or len(text.strip()) == 0:
            text = "텍스트 추출 실패 (OCR 불가)"
        return f"<pre>{text[:2000]}</pre>"
    elif data.get("type") == "image":
        # 썸네일 생성
        if 'content' in data:
            img = Image.open(BytesIO(data['content']))
            img.thumbnail((128, 128))
            buf = BytesIO()
            img.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue()).decode()
            thumb_html = f"<img src='data:image/png;base64,{b64}' width='128' height='128'/><br>"
        else:
            thumb_html = ""
        return f"{thumb_html}<pre>CLIP 벡터(512차원): {str(data['vector'][:8])} ...</pre>"
    else:
        return f"<pre>{str(data)[:1000]}</pre>"
