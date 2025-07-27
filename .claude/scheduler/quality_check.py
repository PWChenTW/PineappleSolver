#!/usr/bin/env python3
"""
代碼品質自動檢查腳本
在Claude Code完成響應後自動檢查代碼品質問題
"""

import os
import sys
import re
import glob
from datetime import datetime
import json

class QualityChecker:
    def __init__(self):
        self.warnings = []
        self.errors = []
        
    def check_recent_files(self, minutes=10):
        """檢查最近修改的文件"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (minutes * 60)
        
        # 檢查各種類型的文件
        file_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.go', '**/*.java', 'src/**/*', 'lib/**/*']
        
        for pattern in file_patterns:
            for filepath in glob.glob(pattern, recursive=True):
                if os.path.isfile(filepath) and os.path.getmtime(filepath) > cutoff_time:
                    self._check_file_content(filepath)
    
    def _check_file_content(self, filepath):
        """檢查文件內容的品質問題"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 通用檢查
            self._check_sensitive_data(filepath, content)
            self._check_error_handling(filepath, content)
            self._check_code_quality(filepath, content)
            self._check_documentation(filepath, content)
            
        except Exception as e:
            self.warnings.append(f"無法檢查文件 {filepath}: {e}")
    
    def _check_sensitive_data(self, filepath, content):
        """檢查敏感數據"""
        sensitive_patterns = [
            (r'api.?key\s*=\s*["\'](?!.*\{)[^"\']{10,}', 'API密鑰可能被硬編碼'),
            (r'password\s*=\s*["\'][^"\']{3,}', '密碼可能被硬編碼'),
            (r'secret\s*=\s*["\'][^"\']{10,}', '秘密可能被硬編碼'),
            (r'token\s*=\s*["\'][^"\']{10,}', 'Token可能被硬編碼'),
            (r'private.?key\s*=\s*["\'][^"\']{10,}', '私鑰可能被硬編碼'),
        ]
        
        for pattern, description in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.warnings.append(
                    f"🔒 安全警告: {filepath} {description}"
                )
    
    def _check_error_handling(self, filepath, content):
        """檢查錯誤處理"""
        # 查找可能的外部調用或高風險操作
        risky_patterns = [
            r'requests\.',
            r'urllib\.',
            r'http\.',
            r'api\.',
            r'client\.',
            r'fetch\(',
            r'axios\.',
            r'connect\(',
            r'open\(',
            r'file\.',
        ]
        
        has_risky_operations = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in risky_patterns
        )
        
        if has_risky_operations:
            # 檢查是否有錯誤處理
            error_handling_patterns = [
                r'try:',
                r'except',
                r'catch',
                r'error',
                r'exception',
                r'\.catch\(',
                r'throw',
                r'if\s+err',
            ]
            
            has_error_handling = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in error_handling_patterns
            )
            
            if not has_error_handling:
                self.warnings.append(
                    f"🔧 品質提醒: {filepath} 有外部調用但缺少錯誤處理"
                )
    
    def _check_code_quality(self, filepath, content):
        """檢查代碼品質"""
        # 檢查過長的函數
        if filepath.endswith('.py'):
            self._check_python_quality(filepath, content)
        elif filepath.endswith(('.js', '.ts')):
            self._check_javascript_quality(filepath, content)
        elif filepath.endswith('.go'):
            self._check_go_quality(filepath, content)
    
    def _check_python_quality(self, filepath, content):
        """檢查Python代碼品質"""
        lines = content.split('\n')
        
        # 檢查函數長度
        function_pattern = r'^\s*def\s+\w+'
        current_function = None
        function_start = 0
        
        for i, line in enumerate(lines):
            if re.match(function_pattern, line):
                if current_function and (i - function_start) > 50:
                    self.warnings.append(
                        f"📏 品質提醒: {filepath} 函數 {current_function} 過長 ({i - function_start} 行)"
                    )
                current_function = re.search(r'def\s+(\w+)', line).group(1)
                function_start = i
        
        # 檢查是否有TODO註釋
        if re.search(r'#\s*TODO', content, re.IGNORECASE):
            self.warnings.append(
                f"📝 提醒: {filepath} 包含TODO註釋，記得處理"
            )
    
    def _check_javascript_quality(self, filepath, content):
        """檢查JavaScript/TypeScript代碼品質"""
        # 檢查console.log（可能是調試代碼）
        if re.search(r'console\.log\(', content):
            self.warnings.append(
                f"🐛 提醒: {filepath} 包含console.log，可能是調試代碼"
            )
        
        # 檢查是否有var（建議使用let/const）
        if re.search(r'\bvar\s+\w+', content):
            self.warnings.append(
                f"💡 建議: {filepath} 使用var聲明變量，建議使用let/const"
            )
    
    def _check_go_quality(self, filepath, content):
        """檢查Go代碼品質"""
        # 檢查是否有fmt.Println（可能是調試代碼）
        if re.search(r'fmt\.Println\(', content):
            self.warnings.append(
                f"🐛 提醒: {filepath} 包含fmt.Println，可能是調試代碼"
            )
    
    def _check_documentation(self, filepath, content):
        """檢查文檔和註釋"""
        lines = content.split('\n')
        
        if filepath.endswith('.py'):
            # 檢查Python函數是否有docstring
            function_lines = [i for i, line in enumerate(lines) 
                            if re.match(r'^\s*def\s+\w+', line)]
            
            for func_line in function_lines:
                # 檢查函數後面是否有docstring
                if func_line + 1 < len(lines):
                    next_line = lines[func_line + 1].strip()
                    has_docstring = (
                        next_line.startswith('"""') or 
                        next_line.startswith("'''") or
                        next_line.startswith('"')
                    )
                    
                    if not has_docstring:
                        func_name = re.search(r'def\s+(\w+)', lines[func_line]).group(1)
                        self.warnings.append(
                            f"📚 建議: {filepath} 函數 {func_name} 缺少文檔字符串"
                        )
    
    def check_git_changes(self):
        """檢查Git變更中的品質問題"""
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
                    if filepath and os.path.exists(filepath):
                        # 只檢查代碼文件
                        if any(filepath.endswith(ext) for ext in ['.py', '.js', '.ts', '.go', '.java', '.cpp', '.c']):
                            self._check_file_content(filepath)
        except Exception:
            # Git檢查失敗不影響主要功能
            pass
    
    def generate_report(self):
        """生成品質檢查報告"""
        if not self.warnings and not self.errors:
            return None
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'quality_level': 'POOR' if self.errors else 'NEEDS_IMPROVEMENT' if self.warnings else 'GOOD'
            }
        }
        
        return report
    
    def save_report(self, report, filename='.quality_check_report.json'):
        """保存品質報告"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # 靜默失敗，不影響主流程

def main():
    """主函數"""
    checker = QualityChecker()
    
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
            print("🚨 發現代碼品質問題:")
            for error in checker.errors:
                print(f"  {error}")
        
        if checker.warnings and len(checker.warnings) <= 3:
            print("💡 品質建議:")
            for warning in checker.warnings:
                print(f"  {warning}")
        elif checker.warnings:
            print(f"💡 發現 {len(checker.warnings)} 個品質建議，詳情請查看報告")
    
    # 返回0表示成功（即使有警告）
    return 0

if __name__ == '__main__':
    sys.exit(main())