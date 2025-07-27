# 通用AI協作開發模板使用指南

## 📋 概述

這個通用模板整合了我們在對話中討論的所有AI協作最佳實踐：

1. **Claude-Claude Code 多實例協作** - 支援多個實例並行工作
2. **規格驅動開發 (SDD)** - 結構化的開發流程
3. **整合式方法論** - BDD + DDD + TDD 的完美結合
4. **Sub Agents 專業分工** - 5個專業AI助手
5. **Hooks 自動化** - 無需人工提醒的品質保證
6. **通用項目支持** - 適用於各種軟件開發項目

## 🎯 使用場景

### 適合的項目類型
✅ **Web應用開發** (前端、後端、全棧)
✅ **桌面應用程序**
✅ **API服務和微服務**
✅ **工具和庫開發**
✅ **遊戲項目**
✅ **數據處理應用**
✅ **需要高代碼品質的項目**
✅ **團隊協作開發**
✅ **AI輔助開發探索**

### 不適合的項目類型
❌ 簡單的一次性腳本
❌ 純靜態網頁
❌ 學習性質的小練習

## 🚀 快速開始三步驟

### Step 1: 複製模板
```bash
# 方式1: 直接複製目錄
cp -r /path/to/General_Project_Template my-new-project
cd my-new-project

# 方式2: 用於特定項目類型
cp -r General_Project_Template my-web-app
cp -r General_Project_Template my-game-project
cp -r General_Project_Template my-api-service
```

### Step 2: 執行一鍵設置
```bash
# 運行設置腳本
./setup.sh

# 測試環境
./test_setup.sh
```

### Step 3: 初始化項目
```bash
# 啟動Claude Code
claude-code

# 根據你的項目類型調整配置
# Web應用示例
> 使用 architect 幫我設計一個用戶管理系統的架構

# 遊戲項目示例  
> 使用 business-analyst 分析大菠蘿(OFC)遊戲的核心玩法需求

# API服務示例
> 使用 integration-specialist 設計RESTful API的架構
```

## 🔄 開發工作流程

### 標準SDD流程

#### 1. 功能規格創建
```bash
# Web應用示例
> /spec-init "user-auth" "用戶註冊、登錄和權限管理系統"

# 遊戲項目示例
> /spec-init "ofc-hand-eval" "OFC手牌評分和比較系統"

# API服務示例  
> /spec-init "user-api" "用戶管理REST API接口"
```

系統會自動：
- 創建 `.kiro/specs/[功能名稱]/` 目錄
- 生成 `spec.json` 狀態文件
- 準備需求、設計、任務文檔結構

#### 2. 需求分析（BDD階段）
```bash
> /spec-requirements user-auth
```

**business-analyst** Sub Agent會：
- 分析業務需求和用戶故事
- 生成Gherkin BDD場景
- 設計用戶體驗流程
- 識別功能邊界和約束

生成的文件：`.kiro/specs/user-auth/requirements.md`

#### 3. 技術設計（DDD階段）
人工審核需求後：
```bash
> /spec-design user-auth
```

**architect** Sub Agent會：
- 設計系統架構和領域模型
- 定義實體、值對象、聚合
- 選擇技術棧和設計模式
- 規劃數據庫和API設計

生成的文件：`.kiro/specs/user-auth/design.md`

#### 4. 任務分解（TDD準備）
設計審核通過後：
```bash
> /spec-tasks user-auth
```

系統會：
- 將設計分解為具體任務
- 分配給適當的Sub Agents
- 安排TDD測試任務
- 規劃實施優先級

生成的文件：`.kiro/specs/user-auth/tasks.md`

#### 5. 開始實施
```bash
> 現在開始實施 user-auth
```

## 👥 Sub Agents 專業分工

### 1. business-analyst (業務分析師)
**最適合的任務**：
- 需求收集和分析
- 用戶故事編寫
- BDD場景設計
- 業務流程梳理

**觸發示例**：
```bash
> 使用 business-analyst 分析電商網站的購物車功能需求
> 讓 business-analyst 設計用戶註冊流程的BDD場景
```

### 2. architect (系統架構師)
**最適合的任務**：
- 系統架構設計
- 技術選型
- DDD領域建模
- 設計模式應用

**觸發示例**：
```bash
> 使用 architect 設計微服務架構
> 讓 architect 選擇合適的數據庫方案
```

### 3. data-specialist (數據專家)  
**最適合的任務**：
- 算法設計和實現
- 數據結構優化
- 性能分析和改進
- 複雜計算邏輯

**觸發示例**：
```bash
> 使用 data-specialist 優化搜索算法
> 讓 data-specialist 設計緩存策略
```

### 4. integration-specialist (集成專家)
**最適合的任務**：
- API設計和開發
- 第三方服務集成
- 系統間通信
- 數據格式轉換

**觸發示例**：
```bash
> 使用 integration-specialist 設計RESTful API
> 讓 integration-specialist 集成支付網關
```

### 5. test-engineer (測試工程師)
**最適合的任務**：
- 測試策略制定
- 自動化測試實現
- 代碼品質檢查
- 性能測試

**觸發示例**：
```bash
> 使用 test-engineer 設計測試策略
> 讓 test-engineer 實現單元測試
```

## 💡 項目類型特定指南

### Web應用開發

#### 典型開發流程
1. **業務分析**: 分析用戶需求和業務流程
2. **架構設計**: 選擇前後端技術棧，設計API
3. **數據建模**: 設計數據庫schema和領域模型
4. **API開發**: 實現後端API接口
5. **前端實現**: 開發用戶界面
6. **集成測試**: 端到端功能驗證

#### 推薦工具鏈
```bash
# 後端
- Python: FastAPI + SQLAlchemy + PostgreSQL
- Node.js: Express + Prisma + MongoDB
- Java: Spring Boot + JPA + MySQL

# 前端  
- React + TypeScript + Tailwind CSS
- Vue.js + TypeScript + Element Plus
- Angular + TypeScript + Angular Material
```

### 遊戲開發

#### 典型開發流程
1. **遊戲設計**: 定義遊戲規則和玩法機制
2. **架構規劃**: 設計遊戲引擎架構
3. **算法實現**: 實現遊戲邏輯和AI
4. **渲染系統**: 實現圖形和動畫
5. **用戶界面**: 設計遊戲UI/UX
6. **測試平衡**: 遊戲平衡性測試

#### 大菠蘿(OFC)範例
```bash
# 1. 需求分析
> /spec-init "ofc-game" "開放式面朝上中國撲克遊戲"
> /spec-requirements ofc-game

# 2. 核心功能設計
> /spec-init "card-eval" "撲克牌手牌評分系統"
> /spec-init "game-logic" "OFC遊戲規則實現"
> /spec-init "scoring" "OFC計分和獎懲系統"
```

### API服務開發

#### 典型開發流程
1. **API設計**: 定義端點和數據格式
2. **認證授權**: 實現安全機制
3. **業務邏輯**: 實現核心功能
4. **數據持久化**: 數據庫集成
5. **監控日誌**: 可觀測性實現
6. **性能優化**: 緩存和優化

#### 推薦實踐
```bash
# API設計原則
- RESTful風格
- 統一響應格式
- 適當的HTTP狀態碼
- 完整的錯誤處理
- 清晰的文檔

# 性能考量
- 分頁機制
- 數據緩存
- 限流保護
- 異步處理
```

## 🔧 高級功能

### 1. 多實例協作
```bash
# 在不同終端中啟動多個Claude Code實例
# 實例1: 專注前端開發
cd my-project && claude-code
> 我負責前端React組件開發

# 實例2: 專注後端API  
cd my-project && claude-code
> 我負責後端API開發

# 實例3: 專注測試
cd my-project && claude-code  
> 我負責測試和品質保證
```

### 2. 自定義Sub Agent
```bash
# 添加專門的Agent (如：ui-designer)
# 1. 創建 .claude/agents/ui-designer.md
# 2. 定義專長和觸發詞
# 3. 在 CLAUDE.md 中添加觸發規則
```

### 3. 項目模板擴展
```bash
# 為特定項目類型創建子模板
cp -r General_Project_Template React_App_Template
# 在React_App_Template中添加React特定配置
```

## 📊 監控和分析

### 進度追蹤
```bash
# 查看所有功能規格狀態
python .claude/scheduler/spec_scheduler.py list

# 查看項目整體進度  
python .claude/scheduler/spec_scheduler.py report

# 查看特定功能狀態
python .claude/scheduler/spec_scheduler.py status user-auth
```

### 命令審計
```bash
# 查看最近24小時的命令統計
python scripts/monitoring/view_command_audit.py

# 查看最常用的命令
python scripts/monitoring/view_command_audit.py --top-commands 10

# 導出詳細報告
python scripts/monitoring/view_command_audit.py --export report.json
```

### 品質監控
```bash
# 查看代碼品質報告
cat .quality_check_report.json

# 手動觸發品質檢查
python .claude/scheduler/quality_check.py
```

## 🛠️ 故障排除

### 常見問題

#### 1. Claude Code settings.json 錯誤
```bash
# 檢查JSON格式
python3 -m json.tool .claude/settings.json

# 如果有錯誤，參考工作範例格式修復
```

#### 2. Sub Agent 沒有自動觸發
```bash
# 檢查觸發詞是否正確
# 在對話中明確提及觸發詞，如：
> 使用 business-analyst 分析需求
> 讓 architect 設計架構
```

#### 3. Hook 沒有執行
```bash
# 檢查腳本權限
chmod +x .claude/scheduler/quality_check.py

# 檢查路徑是否正確
ls -la .claude/scheduler/
```

### 調試技巧
```bash
# 啟用詳細日誌
export CLAUDE_DEBUG=1
claude-code

# 查看Hook執行日誌
tail -f .command_audit.log

# 手動測試腳本
python3 .claude/scheduler/quality_check.py
```

## 📚 最佳實踐總結

### 開發流程
1. **先規格後編碼** - 總是先完成SDD流程
2. **小步快跑** - 每個功能規格保持適中大小
3. **持續集成** - 頻繁提交和測試
4. **文檔同步** - 保持文檔與代碼同步

### Sub Agent使用
1. **明確指派** - 使用"使用 agent-name"明確指派任務
2. **專業分工** - 讓每個Agent專注其擅長領域
3. **review結果** - 人工審核Agent輸出
4. **迭代改進** - 根據結果調整Agent配置

### 代碼品質
1. **測試優先** - 關鍵邏輯先寫測試
2. **自動格式化** - 依賴Hook自動格式化
3. **安全第一** - 絕不提交敏感信息
4. **性能意識** - 定期性能檢查和優化

---

這個通用模板為各種軟件項目提供了solid foundation，讓您能夠充分利用AI協作的力量，創建高品質的軟件產品。無論是Web應用、桌面軟件、遊戲還是API服務，都能從這個模板中受益。