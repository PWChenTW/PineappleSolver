#!/usr/bin/env python3
"""
風控自動檢查腳本
在Claude Code完成響應後自動檢查風險相關問題
"""

import os
import sys
import re
import glob
from datetime import datetime
import json

class RiskChecker:
    def __init__(self):
        self.warnings = []
        self.errors = []
        
    def check_recent_files(self, minutes=10):
        """檢查最近修改的文件"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (minutes * 60)
        
        # 檢查Python文件
        for pattern in ['**/*.py', 'src/**/*.py', 'strategies/**/*.py']:
            for filepath in glob.glob(pattern, recursive=True):
                if os.path.getmtime(filepath) > cutoff_time:
                    self._check_file_content(filepath)
    
    def _check_file_content(self, filepath):
        """檢查文件內容的風險問題"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查交易邏輯是否有止損
            self._check_stop_loss(filepath, content)
            
            # 檢查是否有硬編碼的敏感信息
            self._check_sensitive_data(filepath, content)
            
            # 檢查倉位計算是否合理
            self._check_position_sizing(filepath, content)
            
            # 檢查是否有適當的錯誤處理
            self._check_error_handling(filepath, content)
            
        except Exception as e:
            self.warnings.append(f"無法檢查文件 {filepath}: {e}")
    
    def _check_stop_loss(self, filepath, content):
        """檢查止損機制"""
        # 查找交易相關函數
        trade_patterns = [
            r'def\s+.*(?:buy|sell|trade|order|position)',
            r'class\s+.*(?:Strategy|Trading|Order)',
            r'def\s+.*(?:execute|signal|entry|exit)'
        ]
        
        has_trading_logic = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in trade_patterns
        )
        
        if has_trading_logic:
            # 檢查是否有止損相關代碼
            stop_loss_patterns = [
                r'stop.?loss',
                r'sl\s*=',
                r'stop.?price',
                r'exit.?price',
                r'risk.?management'
            ]
            
            has_stop_loss = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in stop_loss_patterns
            )
            
            if not has_stop_loss:
                self.errors.append(
                    f"⚠️ 風險警告: {filepath} 包含交易邏輯但缺少止損機制"
                )
    
    def _check_sensitive_data(self, filepath, content):
        """檢查敏感數據"""
        sensitive_patterns = [
            (r'api.?key\s*=\s*["\'](?!.*\{)[^"\']{10,}', 'API密鑰可能被硬編碼'),
            (r'password\s*=\s*["\'][^"\']{3,}', '密碼可能被硬編碼'),
            (r'secret\s*=\s*["\'][^"\']{10,}', '秘密可能被硬編碼'),
            (r'token\s*=\s*["\'][^"\']{10,}', 'Token可能被硬編碼'),
        ]
        
        for pattern, description in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.warnings.append(
                    f"🔒 安全警告: {filepath} {description}"
                )
    
    def _check_position_sizing(self, filepath, content):
        """檢查倉位計算"""
        # 查找倉位計算相關代碼
        position_patterns = [
            r'position.?size',
            r'quantity\s*=',
            r'amount\s*=.*\*',
            r'shares\s*='
        ]
        
        has_position_calc = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in position_patterns
        )
        
        if has_position_calc:
            # 檢查是否有風險限制
            risk_limit_patterns = [
                r'max.?risk',
                r'risk.?percent',
                r'max.?position',
                r'risk.?limit',
                r'max.?loss'
            ]
            
            has_risk_limit = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in risk_limit_patterns
            )
            
            if not has_risk_limit:
                self.warnings.append(
                    f"⚠️ 風險提醒: {filepath} 有倉位計算但缺少風險限制"
                )
    
    def _check_error_handling(self, filepath, content):
        """檢查錯誤處理"""
        # 查找API調用或外部依賴
        external_call_patterns = [
            r'requests\.',
            r'api\.',
            r'client\.',
            r'\.get\(',
            r'\.post\(',
            r'connect\('
        ]
        
        has_external_calls = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in external_call_patterns
        )
        
        if has_external_calls:
            # 檢查是否有錯誤處理
            error_handling_patterns = [
                r'try:',
                r'except',
                r'catch',
                r'error',
                r'exception'
            ]
            
            has_error_handling = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in error_handling_patterns
            )
            
            if not has_error_handling:
                self.warnings.append(
                    f"🔧 品質提醒: {filepath} 有外部調用但缺少錯誤處理"
                )
    
    def check_git_changes(self):
        """檢查Git變更中的風險"""
        try:
            import subprocess
            
            # 獲取最近的變更
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                changed_files = result.stdout.strip().split('\n')
                for filepath in changed_files:
                    if filepath.endswith('.py') and os.path.exists(filepath):
                        self._check_file_content(filepath)
        except Exception:
            # Git檢查失敗不影響主要功能
            pass
    
    def generate_report(self):
        """生成風控檢查報告"""
        if not self.warnings and not self.errors:
            return None
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'risk_level': 'HIGH' if self.errors else 'MEDIUM' if self.warnings else 'LOW'
            }
        }
        
        return report
    
    def save_report(self, report, filename='.risk_check_report.json'):
        """保存風控報告"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # 靜默失敗，不影響主流程

def main():
    """主函數"""
    checker = RiskChecker()
    
    # 檢查最近修改的文件
    checker.check_recent_files(minutes=10)
    
    # 檢查Git變更
    checker.check_git_changes()
    
    # 生成報告
    report = checker.generate_report()
    
    if report:
        # 保存報告
        checker.save_report(report)
        
        # 輸出關鍵警告
        if checker.errors:
            print("🚨 發現風險問題:")
            for error in checker.errors:
                print(f"  {error}")
        
        if checker.warnings and len(checker.warnings) <= 3:
            print("⚠️ 風險提醒:")
            for warning in checker.warnings:
                print(f"  {warning}")
        elif checker.warnings:
            print(f"⚠️ 發現 {len(checker.warnings)} 個風險提醒，詳情請查看報告")
    
    # 返回0表示成功（即使有警告）
    return 0

if __name__ == '__main__':
    sys.exit(main())