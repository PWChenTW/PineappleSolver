# OFC Solver 立即行動計劃

**生效日期**: 2025-01-27  
**計劃週期**: 2 週達到 MVP

## 第一階段：基礎修復（Day 1-3）

### Task 1: 修復 MCTS 返回值問題
**負責人**: data-specialist  
**預計時間**: 4 小時

#### BDD 場景
```gherkin
Feature: MCTS 搜索結果完整性
  作為 OFC Solver 使用者
  我希望獲得完整的搜索結果
  以便做出最佳決策

  Scenario: 獲取期望分數
    Given MCTS 搜索已完成
    When 請求搜索結果
    Then 應返回根節點的期望分數
    And 分數應基於所有模擬的平均值

  Scenario: 獲取最佳動作列表
    Given MCTS 搜索已完成
    And 根節點有多個子節點
    When 請求前 N 個最佳動作
    Then 應返回按訪問次數排序的動作列表
    And 每個動作應包含訪問次數和平均獎勵
```

#### 具體任務
1. 修改 `MCTSEngine.search()` 返回根節點引用
2. 在 `OFCSolver.solve()` 中提取 expected_score
3. 實現 get_top_actions() 方法
4. 添加相應的單元測試

### Task 2: 實現結構化錯誤處理
**負責人**: test-engineer  
**預計時間**: 6 小時

#### BDD 場景
```gherkin
Feature: 錯誤處理機制
  作為 API 使用者
  我希望收到清晰的錯誤信息
  以便快速定位和解決問題

  Scenario: 無效手牌輸入
    Given 用戶提供了無效的手牌
    When 調用求解器
    Then 應拋出 InvalidInputError
    And 錯誤信息應說明具體問題

  Scenario: 超時處理
    Given 求解時間限制為 10 秒
    When 求解超過時間限制
    Then 應返回部分結果
    And 標記結果為 "incomplete"

  Scenario: 內存不足
    Given 系統內存接近上限
    When 嘗試擴展搜索樹
    Then 應優雅降級到單線程模式
    And 記錄警告日誌
```

#### 具體任務
1. 創建 `exceptions.py` 定義自定義異常
2. 為所有公開方法添加 try-catch
3. 實現輸入驗證裝飾器
4. 添加錯誤恢復機制

### Task 3: 建立日誌系統
**負責人**: integration-specialist  
**預計時間**: 4 小時

#### 結構化日誌格式
```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "level": "INFO",
  "component": "mcts_engine",
  "message": "Search completed",
  "context": {
    "simulations": 65000,
    "time_taken": 10.5,
    "threads": 4,
    "request_id": "uuid-here"
  }
}
```

## 第二階段：API 開發（Day 4-7）

### Task 4: API 框架搭建
**負責人**: architect  
**預計時間**: 8 小時

#### API 設計規範
```yaml
openapi: 3.0.0
info:
  title: OFC Solver API
  version: 1.0.0

paths:
  /api/v1/solve:
    post:
      summary: 求解 OFC 局面
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                game_state:
                  $ref: '#/components/schemas/GameState'
                options:
                  type: object
                  properties:
                    time_limit: 
                      type: number
                      default: 30
                    threads:
                      type: number
                      default: 4
      responses:
        200:
          description: 求解成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SolveResult'
```

#### BDD 場景
```gherkin
Feature: OFC Solver REST API
  作為 API 用戶
  我希望通過 HTTP 請求求解 OFC 局面
  以便集成到我的應用中

  Scenario: 成功求解請求
    Given API 服務正在運行
    And 我有一個有效的遊戲狀態
    When 我發送 POST 請求到 /api/v1/solve
    Then 應返回 200 狀態碼
    And 響應應包含最佳動作
    And 響應時間應小於配置的時限

  Scenario: 請求驗證失敗
    Given API 服務正在運行
    When 我發送缺少必要字段的請求
    Then 應返回 400 狀態碼
    And 錯誤信息應指出缺失的字段

  Scenario: 併發請求處理
    Given API 服務正在運行
    When 同時發送 10 個求解請求
    Then 所有請求都應得到處理
    And 不應相互干擾
```

### Task 5: 核心 API 端點實現
**負責人**: integration-specialist  
**預計時間**: 12 小時

#### 端點清單
1. **POST /api/v1/solve**
   - 輸入：GameState + Options
   - 輸出：SolveResult
   - 特性：異步處理、請求 ID

2. **POST /api/v1/analyze**
   - 輸入：GameState
   - 輸出：PositionAnalysis
   - 特性：快速評估、無搜索

3. **GET /api/v1/health**
   - 輸出：服務狀態
   - 特性：版本信息、資源使用

4. **POST /api/v1/batch**
   - 輸入：GameState 數組
   - 輸出：批量結果
   - 特性：並行處理、進度回調

## 第三階段：測試和文檔（Day 8-10）

### Task 6: 測試套件開發
**負責人**: test-engineer  
**預計時間**: 16 小時

#### 測試策略
```python
# 測試結構
tests/
├── unit/
│   ├── test_card.py
│   ├── test_hand.py
│   ├── test_mcts.py
│   └── test_evaluator.py
├── integration/
│   ├── test_solver.py
│   ├── test_api.py
│   └── test_workflow.py
├── performance/
│   ├── test_benchmark.py
│   └── test_stress.py
└── e2e/
    └── test_scenarios.py
```

#### 關鍵測試場景
1. **單元測試**（目標覆蓋率 80%）
   - 所有公開方法
   - 邊界條件
   - 錯誤情況

2. **整合測試**
   - 完整遊戲流程
   - API 請求響應
   - 並發處理

3. **性能測試**
   - 基準測試（baseline）
   - 壓力測試（1000 QPS）
   - 內存洩漏檢測

### Task 7: API 文檔和示例
**負責人**: business-analyst  
**預計時間**: 8 小時

#### 文檔結構
```markdown
docs/
├── api/
│   ├── README.md
│   ├── quickstart.md
│   ├── reference.md
│   └── examples/
│       ├── python_client.py
│       ├── curl_examples.sh
│       └── postman_collection.json
├── deployment/
│   ├── docker.md
│   ├── kubernetes.md
│   └── monitoring.md
└── development/
    ├── architecture.md
    ├── contributing.md
    └── testing.md
```

## 第四階段：部署準備（Day 11-14）

### Task 8: Docker 化
**負責人**: integration-specialist  
**預計時間**: 6 小時

#### Dockerfile 示例
```dockerfile
# 多階段構建
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 9: CI/CD 配置
**負責人**: architect  
**預計時間**: 4 小時

#### GitHub Actions 工作流
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements-dev.txt
          pytest --cov=src --cov-report=xml
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t ofc-solver:${{ github.sha }} .
      
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: echo "Deploy to staging"
```

## 每日站會計劃

### Day 1-3: 基礎修復
- 上午：TODO 修復 + 錯誤處理
- 下午：日誌系統 + 測試

### Day 4-7: API 開發  
- Day 4: FastAPI 框架搭建
- Day 5: 核心端點實現
- Day 6: 請求驗證和錯誤處理
- Day 7: API 測試和優化

### Day 8-10: 測試和文檔
- Day 8: 單元測試補充
- Day 9: 整合測試和性能測試
- Day 10: 文檔編寫和示例

### Day 11-14: 部署和發布
- Day 11: Docker 化
- Day 12: CI/CD 設置
- Day 13: 部署測試
- Day 14: MVP 發布

## 成功標準

### MVP 完成標準（Day 14）
- [ ] 所有 P0 任務完成
- [ ] API 可正常訪問
- [ ] 測試覆蓋率 >60%
- [ ] 文檔齊全
- [ ] Docker 鏡像可用
- [ ] CI/CD 運行正常

### 質量標準
- [ ] 無嚴重 bug
- [ ] API 響應時間 <30s
- [ ] 錯誤率 <1%
- [ ] 文檔清晰完整
- [ ] 代碼符合規範

## 風險和緩解

1. **時間風險**: 14天可能過於緊張
   - 緩解：優先完成核心功能，次要功能可延後

2. **技術風險**: FastAPI 整合可能有問題
   - 緩解：準備 Flask 作為備選方案

3. **資源風險**: 多線程可能導致資源競爭
   - 緩解：實現資源池和限流機制

## 每日檢查清單

- [ ] 代碼已提交
- [ ] 測試已通過
- [ ] 文檔已更新
- [ ] 任務已更新
- [ ] 明日計劃已確定

---

**執行開始**: 2025-01-28  
**MVP 目標**: 2025-02-10  
**負責人**: 全體 Sub Agents