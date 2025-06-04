import pathlib

ci = pathlib.Path(".github/workflows/ci.yml")
txt = ci.read_text()
block = """
    - name: Quality Gates
      run: |
        pytest -n auto --cov=app --cov-fail-under=92
        mutmut run --paths-to-mutate app
        radon cc -n C app
"""
if "Quality Gates" not in txt:
    txt += block
    ci.write_text(txt)
