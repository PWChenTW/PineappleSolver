# OFC Solver 監控指南

## 概述

OFC Solver 集成了 Prometheus 監控系統，提供全面的性能指標和系統健康狀況監控。本指南說明如何設置和使用監控系統。

## 快速開始

### 1. 啟動監控堆棧

```bash
cd monitoring
docker-compose up -d
```

這將啟動：
- **Prometheus**: 指標收集和存儲 (http://localhost:9090)
- **Grafana**: 可視化儀表板 (http://localhost:3000)
- **Redis**: 緩存和任務隊列
- **OFC Solver API**: 主應用程序 (http://localhost:8000)

### 2. 訪問 Grafana

1. 打開瀏覽器訪問 http://localhost:3000
2. 使用默認憑據登錄：
   - 用戶名: `admin`
   - 密碼: `admin`
3. 導航到 "Dashboards" → "OFC Solver Dashboard"

### 3. 驗證指標收集

訪問 http://localhost:8000/metrics 查看原始 Prometheus 指標。

## 監控指標詳解

### API 指標

#### 請求指標
- `ofc_api_requests_total`: API 請求總數
  - 標籤: `method`, `endpoint`, `status`
  - 用途: 追踪 API 使用情況和錯誤率

- `ofc_api_request_duration_seconds`: API 請求延遲
  - 標籤: `method`, `endpoint`
  - 用途: 監控 API 性能

- `ofc_api_active_requests`: 當前活動請求數
  - 標籤: `method`, `endpoint`
  - 用途: 了解系統負載

#### 示例查詢
```promql
# 5分鐘內的請求率
rate(ofc_api_requests_total[5m])

# P95 延遲
histogram_quantile(0.95, sum(rate(ofc_api_request_duration_seconds_bucket[5m])) by (le))

# 錯誤率
sum(rate(ofc_api_requests_total{status=~"5.."}[5m])) / sum(rate(ofc_api_requests_total[5m]))
```

### 求解器指標

#### 性能指標
- `ofc_solver_solve_duration_seconds`: 求解時間
  - 用途: 監控求解器性能

- `ofc_solver_simulations_total`: MCTS 模擬總數
  - 用途: 追踪計算量

- `ofc_solver_simulation_rate`: 當前模擬速率
  - 用途: 實時性能監控

#### 結果指標
- `ofc_solver_expected_score`: 期望分數分布
  - 用途: 分析求解質量

- `ofc_solver_confidence`: 置信度分布
  - 用途: 評估結果可靠性

### MCTS 算法指標

- `ofc_mcts_nodes_evaluated_total`: 評估的節點總數
- `ofc_mcts_rollout_depth`: Rollout 深度分布
- `ofc_mcts_tree_size`: 當前樹大小
- `ofc_mcts_thread_utilization`: 線程利用率

### 系統指標

- `ofc_system_cpu_usage_percent`: CPU 使用率
- `ofc_system_memory_usage_bytes`: 內存使用量
  - 標籤: `type` (rss, vms, available)
- `ofc_system_thread_count`: 線程數

## 儀表板使用

### OFC Solver Dashboard

主儀表板包含以下面板：

1. **API Request Rate**: 顯示各端點的請求率
2. **API P95 Latency**: API 響應時間的 95 百分位數
3. **MCTS Simulation Rate**: 實時模擬速率
4. **Solver Execution Time**: 求解器執行時間趨勢
5. **CPU Usage**: 系統 CPU 使用率
6. **Memory Usage**: 系統內存使用量
7. **Request Status Distribution**: 請求狀態分布餅圖
8. **Error Rate**: 錯誤率趨勢
9. **Expected Score Distribution**: 求解結果分數分布
10. **MCTS Thread Utilization**: 多線程利用率

### 自定義查詢

在 Prometheus UI (http://localhost:9090) 中可以執行自定義查詢：

```promql
# 查找最慢的 API 端點
topk(5, histogram_quantile(0.99, sum(rate(ofc_api_request_duration_seconds_bucket[5m])) by (endpoint, le)))

# 計算求解器成功率
sum(rate(ofc_solver_solve_requests_total{status="success"}[5m])) / sum(rate(ofc_solver_solve_requests_total[5m]))

# 監控內存增長
rate(ofc_system_memory_usage_bytes{type="rss"}[5m])
```

## 集成到應用程序

### 1. 添加 Prometheus 客戶端

```python
from prometheus_client import make_asgi_app
from fastapi import FastAPI
from src.api.prometheus_metrics import *

app = FastAPI()

# 添加 Prometheus 端點
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### 2. 使用增強的中間件

```python
from src.api.middleware_prometheus import PrometheusMiddleware, EnhancedRequestTrackingMiddleware

# 添加 Prometheus 中間件
app.add_middleware(PrometheusMiddleware)
app.add_middleware(EnhancedRequestTrackingMiddleware)
```

### 3. 在代碼中記錄指標

```python
from src.api.prometheus_metrics import record_solver_metrics, record_error

# 記錄求解器指標
record_solver_metrics(
    status="success",
    duration=solve_time,
    simulations=result.simulations,
    expected_score=result.expected_score,
    confidence=result.confidence
)

# 記錄錯誤
record_error(error_type="ValueError", component="solver")
```

## 告警配置

創建告警規則文件 `monitoring/prometheus/alerts/ofc_alerts.yml`:

```yaml
groups:
  - name: ofc_solver_alerts
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, sum(rate(ofc_api_request_duration_seconds_bucket[5m])) by (le)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 延遲過高"
          description: "P95 延遲超過 1 秒"
      
      - alert: HighErrorRate
        expr: sum(rate(ofc_api_requests_total{status=~"5.."}[5m])) / sum(rate(ofc_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "錯誤率過高"
          description: "5xx 錯誤率超過 5%"
      
      - alert: LowSimulationRate
        expr: ofc_solver_simulation_rate < 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "模擬速率過低"
          description: "MCTS 模擬速率低於 1000/秒"
```

## 性能調優

### 1. 減少指標基數

避免在標籤中使用高基數值（如用戶 ID、請求 ID）。

### 2. 調整抓取間隔

在 `prometheus.yml` 中調整：
```yaml
scrape_configs:
  - job_name: 'ofc-solver'
    scrape_interval: 10s  # 增加間隔以減少負載
```

### 3. 優化查詢

使用記錄規則預計算常用查詢：
```yaml
groups:
  - name: ofc_recording_rules
    interval: 30s
    rules:
      - record: ofc:api_request_rate_5m
        expr: rate(ofc_api_requests_total[5m])
```

## 故障排除

### 指標未顯示

1. 檢查應用程序是否正在運行：`curl http://localhost:8000/health`
2. 驗證指標端點：`curl http://localhost:8000/metrics`
3. 檢查 Prometheus targets：http://localhost:9090/targets

### Grafana 無法連接到 Prometheus

1. 檢查數據源配置
2. 驗證網絡連接：`docker network ls`
3. 查看容器日誌：`docker-compose logs prometheus grafana`

### 性能問題

1. 檢查 Prometheus 存儲使用：`du -sh monitoring/prometheus_data`
2. 監控 Prometheus 自身：查看 `prometheus_*` 指標
3. 考慮增加資源限制或使用遠程存儲

## 最佳實踐

1. **定期備份**: 備份 Grafana 儀表板和 Prometheus 數據
2. **設置保留策略**: 配置合適的數據保留期限
3. **使用標籤謹慎**: 避免創建過多時間序列
4. **監控監控系統**: 確保監控系統本身的健康
5. **文檔化**: 記錄自定義指標和儀表板的用途

## 擴展監控

### 添加新指標

1. 在 `prometheus_metrics.py` 中定義指標
2. 在相應代碼位置記錄指標
3. 更新 Grafana 儀表板
4. 添加相關告警規則

### 集成其他工具

- **Loki**: 日誌聚合
- **Jaeger**: 分布式追踪
- **Alertmanager**: 告警管理
- **PagerDuty/Slack**: 告警通知

## 安全考慮

1. **認證**: 為 Prometheus 和 Grafana 配置認證
2. **網絡隔離**: 使用防火牆規則限制訪問
3. **加密**: 使用 TLS 加密指標傳輸
4. **審計**: 記錄對監控系統的訪問