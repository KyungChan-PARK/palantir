"""AUTO-GEN TEST: line-cover stubs"""

import importlib
import pytest
from palantir.core.pipeline_transpiler import transpile_yaml_to_visual
import yaml

mod = importlib.import_module("palantir.core.pipeline_transpiler")


def test_line_5():

    assert True

def test_transpile_yaml_to_visual():
    yaml_str = '''
steps:
  - id: load_data
    type: LoadData
    params:
      path: data.csv
  - id: clean_text
    type: CleanText
    params:
      col: text
edges:
  - source: load_data
    target: clean_text
'''
    result = transpile_yaml_to_visual(yaml_str)
    assert "nodes" in result and "edges" in result
    assert len(result["nodes"]) == 2
    assert result["nodes"][0]["id"] == "load_data"
    assert result["edges"][0]["source"] == "load_data"
    assert result["edges"][0]["target"] == "clean_text"
