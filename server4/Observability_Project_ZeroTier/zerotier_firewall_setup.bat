@echo off
:: ============================================================
:: ZeroTier Observability Stack — Windows Firewall Setup
:: ZeroTier IP: 10.155.38.64  |  Network: 10.155.38.0/24
:: Run this script as Administrator
:: ============================================================

echo [1/9] Removing old rules if they exist...
netsh advfirewall firewall delete rule name="ZT-Grafana-3000" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-Prometheus-9090" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-Loki-3100" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-HealthAPI-8005" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-RemediationAPI-8808" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-Streamlit-8501" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-ObsAI-8088" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-KafkaAPI-8601" >nul 2>&1
netsh advfirewall firewall delete rule name="ZT-Alloy-12345" >nul 2>&1

echo [2/9] Opening Grafana (3000)...
netsh advfirewall firewall add rule name="ZT-Grafana-3000" dir=in action=allow protocol=TCP localport=3000 remoteip=10.155.38.0/24 description="Grafana dashboard via ZeroTier"

echo [3/9] Opening Prometheus (9090)...
netsh advfirewall firewall add rule name="ZT-Prometheus-9090" dir=in action=allow protocol=TCP localport=9090 remoteip=10.155.38.0/24 description="Prometheus metrics via ZeroTier"

echo [4/9] Opening Loki (3100)...
netsh advfirewall firewall add rule name="ZT-Loki-3100" dir=in action=allow protocol=TCP localport=3100 remoteip=10.155.38.0/24 description="Loki log aggregation via ZeroTier"

echo [5/9] Opening Health API (8005)...
netsh advfirewall firewall add rule name="ZT-HealthAPI-8005" dir=in action=allow protocol=TCP localport=8005 remoteip=10.155.38.0/24 description="Observability Health API via ZeroTier"

echo [6/9] Opening Remediation API (8808)...
netsh advfirewall firewall add rule name="ZT-RemediationAPI-8808" dir=in action=allow protocol=TCP localport=8808 remoteip=10.155.38.0/24 description="Remediation API uvicorn via ZeroTier"

echo [7/9] Opening Streamlit UI (8501)...
netsh advfirewall firewall add rule name="ZT-Streamlit-8501" dir=in action=allow protocol=TCP localport=8501 remoteip=10.155.38.0/24 description="Kafka Control Streamlit UI via ZeroTier"

echo [8/9] Opening OBS AI API (8088) and Kafka Control API (8601)...
netsh advfirewall firewall add rule name="ZT-ObsAI-8088" dir=in action=allow protocol=TCP localport=8088 remoteip=10.155.38.0/24 description="OBS Log AI API via ZeroTier"
netsh advfirewall firewall add rule name="ZT-KafkaAPI-8601" dir=in action=allow protocol=TCP localport=8601 remoteip=10.155.38.0/24 description="Kafka Control FastAPI via ZeroTier"

echo [9/9] Opening Alloy UI (12345)...
netsh advfirewall firewall add rule name="ZT-Alloy-12345" dir=in action=allow protocol=TCP localport=12345 remoteip=10.155.38.0/24 description="Grafana Alloy UI via ZeroTier"

echo.
echo ============================================================
echo  All ZeroTier firewall rules applied successfully.
echo  Ports open to ZeroTier network (10.155.38.0/24):
echo    3000   Grafana
echo    9090   Prometheus
echo    3100   Loki
echo    8005   Health API
echo    8808   Remediation API
echo    8501   Streamlit UI
echo    8088   OBS AI API
echo    8601   Kafka Control API
echo    12345  Alloy
echo  PostgreSQL (5432) is intentionally NOT exposed.
echo ============================================================
pause
