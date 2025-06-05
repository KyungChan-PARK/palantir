# mypy: ignore-errors
import os

import yaml


def sync_ontology_to_neo4j(
    url: str, user: str, password: str, ontology_dir: str = "ontology"
):
    for fname in os.listdir(ontology_dir):
        if not fname.endswith(".yaml"):
            continue
        with open(os.path.join(ontology_dir, fname), "r", encoding="utf-8") as f:
            yaml.safe_load(f)
