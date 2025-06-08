import os
import yaml
from diagrams import Diagram, Cluster
from diagrams.onprem.container import Docker
from diagrams.onprem.queue import Kafka
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.logging import Loki
from diagrams.custom import Custom
from diagrams.generic.blank import Blank

# docker-compose.yml 경로
COMPOSE_FILE = os.path.join(os.path.dirname(__file__), '../docker-compose.yml')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../docs/assets/system_architecture.png')

# 서비스별 아이콘 매핑 (diagrams 기본/커스텀)
ICON_MAP = {
    'api': Docker,
    'kafka': Kafka,
    'zookeeper': Blank,
    'postgres': PostgreSQL,
    'redis': Redis,
    'weaviate': Custom,
    'prometheus': Prometheus,
    'grafana': Grafana,
    'loki': Loki,
}

# Weaviate 아이콘 경로 (없으면 Blank)
WEAVIATE_ICON = os.path.join(os.path.dirname(__file__), '../docs/assets/weaviate.png')

def parse_services():
    with open(COMPOSE_FILE, 'r') as f:
        compose = yaml.safe_load(f)
    return compose.get('services', {})

def main():
    services = parse_services()
    with Diagram("Palantir System Architecture", filename=OUTPUT_FILE, show=False, direction="LR"):
        nodes = {}
        for name, svc in services.items():
            key = name.lower()
            if key == 'weaviate' and os.path.exists(WEAVIATE_ICON):
                nodes[key] = Custom("Weaviate", WEAVIATE_ICON)
            elif key in ICON_MAP:
                nodes[key] = ICON_MAP[key](name)
            else:
                nodes[key] = Docker(name)
        # 주요 연결 예시 (간단화)
        if 'api' in nodes:
            if 'kafka' in nodes:
                nodes['api'] >> nodes['kafka']
            if 'postgres' in nodes:
                nodes['api'] >> nodes['postgres']
            if 'redis' in nodes:
                nodes['api'] >> nodes['redis']
            if 'weaviate' in nodes:
                nodes['api'] >> nodes['weaviate']
        if 'kafka' in nodes and 'zookeeper' in nodes:
            nodes['kafka'] >> nodes['zookeeper']
        if 'prometheus' in nodes and 'api' in nodes:
            nodes['prometheus'] >> nodes['api']
        if 'grafana' in nodes and 'prometheus' in nodes:
            nodes['grafana'] >> nodes['prometheus']
        if 'loki' in nodes and 'api' in nodes:
            nodes['api'] >> nodes['loki']

if __name__ == "__main__":
    main() 