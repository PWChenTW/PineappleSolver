# 技術設計階段

執行DDD(領域驅動設計)技術設計，將需求轉換為具體的技術架構和實現方案。

## 用法
`/spec-design [功能名稱]`

## 功能說明

這個命令會：

1. **讀取需求文檔**
   - 分析BDD場景和驗收標準
   - 理解業務邏輯和約束條件
   - 識別技術挑戰點

2. **執行DDD設計**
   - 建立領域模型
   - 設計實體和值對象
   - 定義聚合邊界
   - 規劃領域服務

3. **生成設計文檔**
   - 保存到 `.kiro/specs/[feature-name]/design.md`
   - 更新規格狀態為 `tasks`

## DDD設計流程

### 1. 領域分析
- 識別核心領域概念
- 建立通用語言
- 劃分限界上下文

### 2. 模型設計
- 定義實體(Entity)
- 設計值對象(Value Object)
- 確定聚合根(Aggregate Root)
- 規劃倉儲(Repository)

### 3. 架構設計
- 分層架構設計
- 依賴注入規劃
- 接口定義
- 數據流設計

### 4. 技術選型
- 框架和庫選擇
- 數據存儲方案
- API設計
- 集成方案

## 輸出格式

生成的 `design.md` 包含：

```markdown
# [功能名稱] 技術設計

## 領域模型

### 實體設計
```python
class TradingStrategy(Entity):
    """交易策略聚合根"""
    def __init__(self, strategy_id: StrategyId, name: str):
        self.id = strategy_id
        self.name = name
        self.parameters = {}
        self.signals = []
    
    def generate_signal(self, market_data: MarketData) -> Signal:
        """生成交易信號"""
        pass
```

### 值對象設計
```python
@dataclass(frozen=True)
class Signal(ValueObject):
    """交易信號值對象"""
    symbol: str
    timestamp: datetime
    action: SignalAction
    confidence: Decimal
    metadata: Dict[str, Any]
```

### 領域服務
```python
class SignalGenerationService:
    """信號生成領域服務"""
    def generate_signals(self, strategy: TradingStrategy, 
                        market_data: MarketData) -> List[Signal]:
        pass
```

## 架構設計

### 分層架構
```
Application Layer    # 應用服務、命令處理
     ↓
Domain Layer        # 實體、值對象、領域服務
     ↓
Infrastructure Layer # 倉儲實現、外部API
```

### 組件圖
```
[Strategy Service] → [Risk Manager] → [Order Service]
        ↓                ↓               ↓
[Market Data API] → [Position Manager] → [Broker API]
```

## 技術規格

### API設計
- 策略管理API：`/api/strategies`
- 信號查詢API：`/api/signals`
- 風控檢查API：`/api/risk-check`

### 數據模型
- 策略配置表
- 信號歷史表
- 風控記錄表

### 性能要求
- 信號生成延遲：< 100ms
- 並發處理能力：1000 req/sec
- 數據處理量：10MB/min

## 實施計劃

### 開發優先級
1. 核心領域模型
2. 信號生成邏輯
3. 風控集成
4. API接口
5. 測試覆蓋

### 技術風險
- [風險項目] → [緩解方案]
- [性能瓶頸] → [優化策略]

## 測試策略

### 單元測試
- 實體行為測試
- 值對象驗證
- 領域服務邏輯

### 集成測試
- API接口測試
- 數據庫集成測試
- 外部服務集成

### 端到端測試
- 完整業務流程測試
- 性能基準測試
```

## 設計原則

### DDD最佳實踐
1. **明確的領域邊界**：清晰的聚合邊界
2. **豐富的領域模型**：業務邏輯在領域層
3. **通用語言**：一致的術語使用
4. **依賴倒置**：領域層不依賴基礎設施

### 量化交易特殊考量
1. **實時性要求**：低延遲設計
2. **數據一致性**：事務邊界清晰
3. **風險控制**：每層都有風控檢查
4. **審計追蹤**：完整的操作記錄

## 示例

```bash
> /spec-design rsi-strategy
```

會基於RSI策略的需求分析，設計包含：
- RSIStrategy實體
- SignalGeneration領域服務
- RiskValidation值對象
- MarketDataRepository接口

## 質量檢查

設計完成後會自動檢查：
- [ ] 領域模型完整
- [ ] 架構分層清晰
- [ ] 接口定義明確
- [ ] 性能需求可達成
- [ ] 風控機制完善

## 人工審核點

在進入任務分解前，需要確認：
1. 架構設計合理
2. 技術選型適當
3. 性能指標可達成
4. 風險控制充分

通過審核後使用 `/spec-tasks [功能名稱]` 進入下一階段。