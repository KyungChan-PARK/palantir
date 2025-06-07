# Grafana Linux 설치 및 설정 가이드

## 1. 시스템 요구사항
- Linux (Ubuntu 22.04 LTS 이상 권장)
- systemd 지원
- 최소 2GB RAM
- 최소 1GB 디스크 공간

## 2. APT를 통한 설치
```bash
# APT 저장소 추가
sudo apt-get install -y apt-transport-https software-properties-common
sudo wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key

echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# 패키지 설치
sudo apt-get update
sudo apt-get install -y grafana
```

## 3. 서비스 설정 및 시작
```bash
# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# 상태 확인
sudo systemctl status grafana-server
```

## 4. 방화벽 설정
```bash
# UFW가 활성화된 경우
sudo ufw allow 3000/tcp
```

## 5. Prometheus 데이터소스 자동 등록
```bash
# 설정 디렉토리 생성
sudo mkdir -p /etc/grafana/provisioning/datasources/

# 데이터소스 설정 파일 생성
sudo tee /etc/grafana/provisioning/datasources/prometheus.yaml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
EOF
```

## 6. 권한 설정
```bash
# Grafana 사용자에게 필요한 권한 부여
sudo chown -R grafana:grafana /var/lib/grafana
sudo chown -R grafana:grafana /etc/grafana
```

## 7. 대시보드 설정
```bash
# 대시보드 디렉토리 생성
sudo mkdir -p /var/lib/grafana/dashboards
sudo chown -R grafana:grafana /var/lib/grafana/dashboards

# 대시보드 프로비저닝 설정
sudo tee /etc/grafana/provisioning/dashboards/default.yaml << EOF
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
```

## 8. 보안 설정
```bash
# admin 비밀번호 변경
sudo grafana-cli admin reset-admin-password <새_비밀번호>

# 설정 파일 권한 제한
sudo chmod 640 /etc/grafana/grafana.ini
```

## 9. 로깅 설정
```bash
# 로그 디렉토리 권한 설정
sudo chown -R grafana:grafana /var/log/grafana
```

## 10. 상태 확인
- 웹 인터페이스: http://localhost:3000
- 기본 로그인: admin / admin
- 상태 API: http://localhost:3000/api/health

## 11. 문제 해결
### 로그 확인
```bash
sudo journalctl -u grafana-server -f
```

### 일반적인 문제
1. 권한 문제
```bash
sudo chown -R grafana:grafana /var/lib/grafana
sudo chmod -R 755 /var/lib/grafana
```

2. 포트 충돌
```bash
sudo netstat -tulpn | grep 3000
```

3. 메모리 부족
```bash
# grafana.ini 메모리 설정 조정
sudo vi /etc/grafana/grafana.ini
``` 