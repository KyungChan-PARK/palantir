# Grafana 9 Linux 설치 및 Prometheus 연동

## 1. 다운로드 및 압축 해제
- https://grafana.com/grafana/download/9.5.15?platform=linux
- `tar -zxvf grafana-9.5.15.linux-amd64.tar.gz -C ~/palantir/grafana`

## 2. Grafana 실행
```bash
cd ~/palantir/grafana/bin
./grafana-server
```
- 기본 포트: 3000 (http://localhost:3000)

## 3. Prometheus 데이터소스 자동 등록
- ~/palantir/grafana/conf/provisioning/datasources/prometheus.yaml 생성
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
```
- Grafana 재시작 시 자동 인식

## 4. /health API 확인
```bash
curl http://localhost:3000/api/health
```
- 200 OK, {"database":"ok","version":"9.x.x","commit":"..."} 반환
