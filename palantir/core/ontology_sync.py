from neo4j import GraphDatabase
import yaml
import glob

def sync_ontology_to_neo4j(neo4j_url, user, password, ontology_dir="ontology/"):
    driver = GraphDatabase.driver(neo4j_url, auth=(user, password))
    yaml_files = glob.glob(f"{ontology_dir}/*.yaml")
    with driver.session() as session:
        for file in yaml_files:
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # TODO: data 구조에 따라 Cypher 쿼리 작성 및 업서트
                print(f"[SYNC] {file} → Neo4j")
    driver.close() 