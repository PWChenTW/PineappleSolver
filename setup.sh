#!/bin/bash

# 通用AI協作開發模板 - 一鍵設置腳本
# 設置完整的AI協作開發環境

echo "🚀 通用AI協作開發模板一鍵設置"
echo "==============================="
echo "這將設置完整的AI協作開發環境，包括："
echo "• 規格驅動開發 (SDD) 框架"
echo "• 多實例協作支援"
echo "• Sub Agents 專業分工"
echo "• Hooks 自動化"
echo "• 代碼品質檢查"
echo "==============================="

# 檢查Python環境
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到Python3，請先安裝Python3"
    exit 1
fi

echo "✅ Python3環境檢查通過"

# 創建基本目錄結構
echo "📁 創建目錄結構..."
mkdir -p .claude/agents
mkdir -p .claude/commands  
mkdir -p .claude/scheduler/logs
mkdir -p .kiro/steering
mkdir -p .kiro/specs
mkdir -p docs/quick_reference
mkdir -p docs/examples
mkdir -p docs/collaboration
mkdir -p docs/checklists
mkdir -p src/domain
mkdir -p tests/behavior
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p scripts/monitoring

echo "✅ 目錄結構創建完成"

# 創建知識庫文件
echo "📚 初始化項目知識庫..."

cat > .kiro/steering/product.md << 'EOF'
# 產品概述

## 項目目標
[請描述您的項目目標和願景]

## 核心功能
- [功能1]
- [功能2]
- [功能3]

## 目標用戶
[描述您的目標用戶群體]

## 成功標準
[定義項目成功的衡量標準]
EOF

cat > .kiro/steering/tech.md << 'EOF'
# 技術架構

## 技術棧
- 後端: [請填寫]
- 前端: [請填寫]
- 數據庫: [請填寫]
- 部署: [請填寫]

## 架構決策
[記錄重要的技術決策和原因]

## 性能要求
[定義性能指標和要求]
EOF

cat > .kiro/steering/methodology.md << 'EOF'
# 開發方法論

## SDD (規格驅動開發)
本項目使用SDD作為主要開發流程框架

## 階段說明
1. **需求分析** (BDD) - 理解和定義業務需求
2. **技術設計** (DDD) - 設計系統架構和領域模型
3. **任務分解** - 將設計分解為具體任務
4. **實施開發** (TDD) - 測試驅動的開發實施

## 品質標準
- 代碼覆蓋率 > 80%
- 所有函數必須有文檔
- 核心邏輯必須有單元測試
EOF

cat > .kiro/steering/collaboration.md << 'EOF'
# 協作規範

## Sub Agents分工
- business-analyst: 需求分析和用戶體驗
- architect: 系統架構和技術設計
- data-specialist: 數據結構和算法
- integration-specialist: API和系統集成
- test-engineer: 測試和品質保證

## 多實例協作流程
1. 角色分配和責任劃分
2. 定期進度同步
3. 代碼審查和質量控制
4. 文檔維護和更新
EOF

echo "✅ 知識庫初始化完成"

# 創建快速參考文檔
echo "📖 創建快速參考文檔..."

cat > docs/quick_reference/api_design.md << 'EOF'
# API設計指南

## RESTful設計原則
- 使用HTTP動詞 (GET, POST, PUT, DELETE)
- 資源導向的URL設計
- 統一的響應格式
- 適當的HTTP狀態碼

## 最佳實踐
- API版本管理
- 分頁和排序
- 錯誤處理
- 認證和授權
EOF

cat > docs/quick_reference/design_patterns.md << 'EOF'
# 設計模式參考

## 常用模式
- 單例模式 (Singleton)
- 工廠模式 (Factory)
- 觀察者模式 (Observer)
- 策略模式 (Strategy)

## DDD模式
- 實體 (Entity)
- 值對象 (Value Object)
- 聚合根 (Aggregate Root)
- 領域服務 (Domain Service)
EOF

echo "✅ 快速參考文檔創建完成"

# 創建Git忽略文件
echo "📝 創建配置文件..."

if [ ! -f .gitignore ]; then
cat > .gitignore << 'EOF'
# Logs
*.log
logs/
.claude/scheduler/logs/*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
htmlcov/

# nyc test coverage
.nyc_output

# Dependency directories
node_modules/
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
.command_audit.log
.quality_check_report.json
EOF

echo "✅ .gitignore 文件創建完成"
fi

# 設置腳本權限
chmod +x test_setup.sh
chmod +x .claude/scheduler/spec_scheduler.py
chmod +x .claude/scheduler/quality_check.py
chmod +x scripts/monitoring/view_command_audit.py

echo "✅ 腳本權限設置完成"

# 創建示例項目結構
echo "📦 創建示例代碼結構..."

cat > src/domain/__init__.py << 'EOF'
"""
領域層模組
包含核心業務邏輯和領域模型
"""
EOF

cat > tests/__init__.py << 'EOF'
"""
測試模組
"""
EOF

cat > tests/test_example.py << 'EOF'
"""
示例測試文件
"""
import unittest

class TestExample(unittest.TestCase):
    def test_example(self):
        """示例測試案例"""
        self.assertEqual(1 + 1, 2)

if __name__ == '__main__':
    unittest.main()
EOF

echo "✅ 示例代碼結構創建完成"

# 運行測試檢查
echo "🧪 運行環境測試..."
if [ -f "test_setup.sh" ]; then
    ./test_setup.sh
else
    echo "⚠️  測試腳本不存在，跳過環境測試"
fi

echo ""
echo "🎉 設置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 運行 'claude-code' 啟動開發環境"
echo "2. 使用 '/spec-init [功能名稱] [描述]' 創建第一個功能"
echo "3. 查看 USAGE_GUIDE.md 了解詳細使用方法"
echo ""
echo "🔧 有用的命令："
echo "• ./test_setup.sh - 檢查環境狀態"
echo "• python .claude/scheduler/spec_scheduler.py report - 查看項目進度"
echo "• python scripts/monitoring/view_command_audit.py - 查看命令統計"
echo ""

exit 0