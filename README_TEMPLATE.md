# 通用AI協作開發模板

🎯 **一個完整的AI協作開發環境，適用於各種類型的軟件項目**

## 🚀 快速開始

```bash
# 測試環境
./test_setup.sh

# 開始使用
claude-code
> /spec-init "我的第一個功能" "用戶註冊和登錄系統"
```

## 📋 核心特色

### 🤖 **整合式開發方法論**
- **SDD** (規格驅動) 作為主框架
- **BDD** (行為驅動) 處理需求
- **DDD** (領域驅動) 處理設計
- **TDD** (測試驅動) 確保品質

### 👥 **5個專業Sub Agents**
- `business-analyst` - 業務分析師
- `architect` - 系統架構師
- `data-specialist` - 數據專家
- `integration-specialist` - 集成專家
- `test-engineer` - 測試工程師

### ⚡ **自動化Hooks**
- 代碼格式化
- 敏感文件保護
- 命令執行審計
- 品質自動檢查

### 🔄 **多實例協作**
- 角色分工明確
- 任務自動調度
- Git分支策略
- 進度實時追蹤

## 📖 使用指南

### 標準SDD流程
```bash
# 1. 初始化功能規格
> /spec-init [功能名稱] [描述]

# 2. BDD需求分析
> /spec-requirements [功能名稱]

# 3. DDD技術設計
> /spec-design [功能名稱]

# 4. 任務分解
> /spec-tasks [功能名稱]

# 5. 開始實施
> 現在開始實施 [功能名稱]
```

### Sub Agents使用
```bash
# 顯式調用特定Agent
> 使用 business-analyst 分析這個功能的用戶需求
> 讓 architect 設計系統架構
> 請 data-specialist 優化算法性能
```

## 📊 監控工具

```bash
# 查看命令執行統計
python scripts/monitoring/view_command_audit.py

# 查看項目進度
python .claude/scheduler/spec_scheduler.py report

# 檢查環境狀態
./test_setup.sh
```

## 📁 項目結構

```
├── AI_COLLABORATION_TEMPLATE.md    # 完整模板說明
├── USAGE_GUIDE.md                 # 詳細使用指南
├── CLAUDE.md                      # Claude Code配置
├── setup.sh                       # 一鍵設置腳本
├── test_setup.sh                  # 環境測試腳本
├── .claude/
│   ├── agents/                    # Sub Agents配置
│   ├── commands/                  # Slash Commands
│   ├── scheduler/                 # 任務調度器
│   └── settings.json              # Hooks配置
├── .kiro/
│   ├── steering/                  # 項目知識庫
│   └── specs/                     # 功能規格
├── docs/                          # 文檔目錄
├── src/                           # 源代碼
├── tests/                         # 測試代碼
└── scripts/                       # 工具腳本
```

## 🎯 適用場景

✅ **Web應用開發**
✅ **桌面軟件開發**
✅ **遊戲項目**
✅ **API服務**
✅ **工具和庫**
✅ **算法項目**
✅ **數據處理**

## 📚 深入了解

- **[AI_COLLABORATION_TEMPLATE.md](AI_COLLABORATION_TEMPLATE.md)** - 完整模板框架
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - 詳細使用指南
- **[CLAUDE.md](CLAUDE.md)** - Claude Code配置說明

## 🆘 獲得幫助

1. 查看使用指南：`USAGE_GUIDE.md`
2. 檢查配置文件：`CLAUDE.md`
3. 運行環境測試：`./test_setup.sh`
4. 查看日誌：`.claude/scheduler/logs/`

---

🎉 **開始您的高效AI協作開發之旅！**

這個模板適用於各種類型的軟件項目，從簡單的工具到複雜的企業應用，都能提供專業、高效、安全的AI協作開發環境。