import os
import tempfile

import yaml

from palantir.core.ontology_sync import sync_ontology_to_neo4j


def test_sync_ontology_to_neo4j(monkeypatch):
    class DummySession:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    class DummyDriver:
        def session(self):
            return DummySession()

        def close(self):
            pass

    monkeypatch.setattr("neo4j.GraphDatabase.driver", lambda *a, **k: DummyDriver())
    with tempfile.TemporaryDirectory() as d:
        # 파일 없음
        sync_ontology_to_neo4j("bolt://localhost:7687", "neo4j", "test", ontology_dir=d)
        # 파일 있음
        fpath = os.path.join(d, "test.yaml")
        with open(fpath, "w", encoding="utf-8") as f:
            yaml.dump({"a": 1}, f)
        sync_ontology_to_neo4j("bolt://localhost:7687", "neo4j", "test", ontology_dir=d)
