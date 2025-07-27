# 通用AI協作開發項目模板

**基於Claude-Claude Code多實例協作開發經驗**

這是一個完整的通用AI協作開發項目模板，整合了多實例協作、規格驅動開發(SDD)、行為驅動開發(BDD)、領域驅動設計(DDD)、測試驅動開發(TDD)，以及最新的Sub Agents和Hooks功能。

## 📋 目錄結構

```
general-ai-project/
├── README.md                          # 項目說明
├── CLAUDE.md                          # Claude Code 主配置
├── setup.sh                           # 一鍵設置腳本
├── .claude/
│   ├── commands/                      # 自定義命令
│   │   ├── spec-init.md              # 初始化規格
│   │   ├── spec-requirements.md       # 需求分析
│   │   ├── spec-design.md            # 技術設計
│   │   └── spec-tasks.md             # 任務分解
│   ├── agents/                       # Sub Agents 配置
│   │   ├── business-analyst.md       # 業務分析師
│   │   ├── architect.md              # 系統架構師
│   │   ├── data-specialist.md        # 數據專家
│   │   ├── integration-specialist.md # 集成專家
│   │   └── test-engineer.md          # 測試工程師
│   ├── scheduler/                    # 任務調度器
│   │   ├── spec_scheduler.py         # 主調度器
│   │   ├── quality_check.py          # 品質檢查
│   │   └── logs/                     # 日誌目錄
│   └── settings.json                 # Hooks配置
├── .kiro/
│   ├── steering/                     # 項目知識庫
│   │   ├── product.md                # 產品概述
│   │   ├── tech.md                   # 技術架構
│   │   ├── structure.md              # 項目結構
│   │   ├── methodology.md            # 開發方法論
│   │   ├── business_rules.md         # 業務規則
│   │   └── collaboration.md          # 協作規範
│   └── specs/                        # 功能規格
│       └── [feature-name]/
│           ├── spec.json             # 規格狀態
│           ├── requirements.md       # 需求文檔
│           ├── design.md             # 設計文檔
│           └── tasks.md              # 任務清單
├── docs/
│   ├── quick_reference/              # 快速參考
│   │   ├── api_design.md             # API設計
│   │   ├── data_structures.md        # 數據結構
│   │   ├── design_patterns.md        # 設計模式
│   │   ├── performance.md            # 性能優化
│   │   └── error_handling.md         # 錯誤處理
│   ├── checklists/                   # 檢查清單
│   │   ├── code_review.md            # 代碼審查
│   │   ├── security.md               # 安全檢查
│   │   ├── performance.md            # 性能檢查
│   │   └── deployment.md             # 部署檢查
│   ├── collaboration/                # 協作指南
│   │   ├── multi_instance.md         # 多實例協作
│   │   ├── role_assignment.md        # 角色分配
│   │   └── workflow.md               # 工作流程
│   └── examples/                     # 使用範例
│       ├── bdd_scenarios.md          # BDD場景
│       ├── ddd_modeling.md           # DDD建模
│       └── agent_usage.md            # Agent使用
├── src/
│   ├── domain/                       # DDD領域層
│   │   ├── entities/                 # 實體
│   │   ├── value_objects/            # 值對象
│   │   ├── aggregates/               # 聚合根
│   │   └── services/                 # 領域服務
│   ├── application/                  # 應用層
│   │   ├── services/                 # 應用服務
│   │   ├── commands/                 # 命令處理
│   │   └── queries/                  # 查詢處理
│   ├── infrastructure/               # 基礎設施層
│   │   ├── persistence/              # 持久化
│   │   ├── external/                 # 外部服務
│   │   └── web/                      # Web接口
│   └── utils/                        # 工具函數
├── tests/
│   ├── behavior/                     # BDD測試
│   │   └── features/                 # Gherkin場景
│   ├── unit/                         # TDD單元測試
│   ├── integration/                  # 整合測試
│   └── fixtures/                     # 測試數據
└── scripts/
    ├── setup/                        # 設置腳本
    ├── deployment/                   # 部署腳本
    ├── monitoring/                   # 監控工具
    │   ├── view_command_audit.py     # 命令審計查看器
    │   └── performance_monitor.py    # 性能監控
    └── maintenance/                  # 維護腳本
```

## 🤖 Sub Agents 配置

### 核心Agent功能

#### business-analyst (業務分析師)
- **專長**: 需求分析、BDD場景生成、用戶體驗設計
- **觸發詞**: 需求、分析、業務邏輯、BDD、場景、用戶故事
- **輸出**: 詳細的業務需求文檔和BDD測試場景

#### architect (系統架構師)
- **專長**: 系統架構設計、DDD領域建模、技術選型
- **觸發詞**: 架構、設計、系統、模組、組件、DDD、模式
- **輸出**: 完整的技術架構設計和實施計劃

#### data-specialist (數據專家)
- **專長**: 數據結構設計、算法實現、性能優化
- **觸發詞**: 數據、算法、計算、處理、演算法、優化
- **輸出**: 高效的數據處理方案和算法實現

#### integration-specialist (集成專家)
- **專長**: API設計、外部系統集成、服務間通信
- **觸發詞**: API、接口、集成、外部、服務、網路
- **輸出**: 完整的集成方案和API文檔

#### test-engineer (測試工程師)
- **專長**: 測試策略、自動化測試、品質保證
- **觸發詞**: 測試、單元測試、整合測試、品質、覆蓋率
- **輸出**: 全面的測試計劃和自動化測試套件

## 🔄 開發方法論整合

### 1. SDD (規格驅動開發) - 主框架
```
階段流程: requirements → design → tasks → implementation
```

### 2. BDD (行為驅動開發) - 需求階段
- 使用Gherkin語言描述業務行為
- Given-When-Then場景結構
- 可執行的驗收標準

### 3. DDD (領域驅動設計) - 設計階段
- 領域模型建立
- 實體、值對象、聚合設計
- 限界上下文劃分

### 4. TDD (測試驅動開發) - 實施階段
- 紅-綠-重構循環
- 單元測試優先
- 持續重構改善

## ⚡ 自動化功能

### Hooks 自動化
- **敏感文件保護**: 自動阻止修改機密文件
- **代碼格式化**: Python(Black)、JS/TS(Prettier)、Go(gofmt)
- **命令審計**: 記錄所有命令執行
- **品質檢查**: 自動代碼品質和安全檢查

### 任務調度
- **規格狀態追蹤**: 自動記錄開發階段進度
- **進度報告**: 生成項目進度摘要
- **任務分配**: Sub Agent智能任務分工

## 🎯 適用項目類型

### Web應用開發
- 前端框架集成 (React, Vue, Angular)
- 後端API開發 (REST, GraphQL)
- 全棧應用架構

### 桌面應用
- 跨平台桌面應用 (Electron, Tauri)
- 原生桌面應用 (Qt, .NET)

### 遊戲開發
- 遊戲邏輯設計
- 遊戲引擎集成
- 多人遊戲架構

### 工具和庫
- 開發工具創建
- 庫和框架設計
- 命令行工具

### API服務
- 微服務架構
- RESTful API設計
- GraphQL服務

### 數據處理
- 數據分析工具
- ETL管道
- 機器學習項目

## 🚀 快速開始

### 1. 環境設置
```bash
# 複製模板
cp -r General_Project_Template my-new-project
cd my-new-project

# 運行設置腳本
./setup.sh

# 驗證環境
./test_setup.sh
```

### 2. 項目初始化
```bash
# 啟動Claude Code
claude-code

# 初始化第一個功能
> /spec-init "user-auth" "用戶註冊和登錄系統"

# 開始需求分析
> /spec-requirements user-auth
```

### 3. 開發流程
```bash
# 完成需求後進行設計
> /spec-design user-auth

# 設計完成後分解任務
> /spec-tasks user-auth

# 開始實施
> 現在開始實施 user-auth
```

## 📊 監控和工具

### 進度追蹤
```bash
# 查看項目進度
python .claude/scheduler/spec_scheduler.py report

# 查看特定功能狀態
python .claude/scheduler/spec_scheduler.py status user-auth
```

### 品質監控
```bash
# 查看命令執行統計
python scripts/monitoring/view_command_audit.py

# 查看品質檢查報告
cat .quality_check_report.json
```

## 🛠️ 自定義和擴展

### 添加新的Sub Agent
1. 在 `.claude/agents/` 創建新的markdown文件
2. 定義Agent的專長和觸發詞
3. 更新 `CLAUDE.md` 中的觸發規則

### 添加自定義Hooks
1. 編輯 `.claude/settings.json`
2. 添加新的matcher和hooks規則
3. 測試Hook功能

### 擴展快速參考
1. 在 `docs/quick_reference/` 添加新文檔
2. 更新 `CLAUDE.md` 中的查閱機制
3. 添加觸發詞映射

## 📚 最佳實踐

### 代碼組織
- 遵循DDD分層架構
- 保持高內聚、低耦合
- 使用清晰的命名約定

### 測試策略
- 單元測試覆蓋率 > 80%
- BDD場景覆蓋主要業務流程
- 集成測試驗證系統協作

### 文檔維護
- 保持文檔與代碼同步
- 使用Markdown格式
- 包含實用的代碼示例

### 協作規範
- 明確的角色分工
- 定期進度同步
- 標準化的Git工作流

---

這個模板為各種類型的軟件項目提供了一個solid foundation，結合AI協作和現代開發最佳實踐，讓開發過程更高效、更有組織。