# Grafana 9 Windows ZIP 설치 및 Prometheus 연동

## 1. 다운로드 및 압축 해제
- https://grafana.com/grafana/download/9.5.15?platform=windows
- ZIP 파일을 C:\palantir\grafana\ 에 압축 해제

## 2. Grafana 실행
```powershell
cd C:\palantir\grafana\bin
start grafana-server.exe
```
- 기본 포트: 3000 (http://localhost:3000)

## 3. Prometheus 데이터소스 자동 등록
- C:\palantir\grafana\conf\provisioning\datasources\prometheus.yaml 생성
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