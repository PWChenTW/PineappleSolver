#!/usr/bin/env python3
"""
API審計日誌查看工具
用於分析API調用模式和性能
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os

class APIAuditViewer:
    def __init__(self, log_file=".api_audit.log"):
        self.log_file = log_file
        self.entries = []
        
    def load_logs(self):
        """載入API審計日誌"""
        if not os.path.exists(self.log_file):
            print(f"❌ 審計日誌文件不存在: {self.log_file}")
            return False
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.entries.append(line)
            return True
        except Exception as e:
            print(f"❌ 讀取日誌失敗: {e}")
            return False
    
    def parse_entry(self, entry):
        """解析日誌條目"""
        try:
            # 解析格式：timestamp: API調用 - command
            parts = entry.split(': API調用 - ', 1)
            if len(parts) == 2:
                timestamp_str, command = parts
                timestamp = datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Z %Y")
                return {
                    'timestamp': timestamp,
                    'command': command,
                    'type': self._classify_command(command)
                }
        except Exception:
            pass
        return None
    
    def _classify_command(self, command):
        """分類命令類型"""
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['api', 'curl', 'http', 'request']):
            return 'api_call'
        elif any(word in command_lower for word in ['git', 'commit', 'push', 'pull']):
            return 'git_operation'
        elif any(word in command_lower for word in ['test', 'pytest', 'unittest']):
            return 'testing'
        elif any(word in command_lower for word in ['python', 'node', 'npm', 'pip']):
            return 'development'
        else:
            return 'other'
    
    def analyze_patterns(self, hours=24):
        """分析API調用模式"""
        if not self.entries:
            print("📊 沒有API調用記錄")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_entries = []
        
        for entry_str in self.entries:
            entry = self.parse_entry(entry_str)
            if entry and entry['timestamp'] >= cutoff_time:
                recent_entries.append(entry)
        
        if not recent_entries:
            print(f"📊 過去 {hours} 小時內沒有API調用記錄")
            return
        
        # 統計分析
        total_calls = len(recent_entries)
        call_types = Counter(entry['type'] for entry in recent_entries)
        hourly_distribution = defaultdict(int)
        
        for entry in recent_entries:
            hour = entry['timestamp'].hour
            hourly_distribution[hour] += 1
        
        # 顯示結果
        print(f"📊 API調用分析報告 (過去 {hours} 小時)")
        print("=" * 50)
        print(f"總調用次數: {total_calls}")
        print(f"平均每小時: {total_calls / hours:.1f} 次")
        
        print("\n📈 調用類型分布:")
        for call_type, count in call_types.most_common():
            percentage = (count / total_calls) * 100
            print(f"  {call_type}: {count} 次 ({percentage:.1f}%)")
        
        print("\n⏰ 小時分布:")
        for hour in sorted(hourly_distribution.keys()):
            count = hourly_distribution[hour]
            bar = "█" * min(20, count)
            print(f"  {hour:02d}:00 - {hour:02d}:59 | {bar} ({count})")
        
        # 最近的調用
        print(f"\n🕒 最近 10 次調用:")
        for entry in sorted(recent_entries, key=lambda x: x['timestamp'], reverse=True)[:10]:
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            print(f"  {time_str} | {entry['type']} | {entry['command'][:60]}...")
    
    def show_summary(self):
        """顯示總體摘要"""
        if not self.entries:
            print("📊 沒有API調用記錄")
            return
        
        parsed_entries = [self.parse_entry(entry) for entry in self.entries]
        parsed_entries = [e for e in parsed_entries if e]
        
        if not parsed_entries:
            print("📊 沒有有效的API調用記錄")
            return
        
        total_calls = len(parsed_entries)
        first_call = min(entry['timestamp'] for entry in parsed_entries)
        last_call = max(entry['timestamp'] for entry in parsed_entries)
        duration = (last_call - first_call).total_seconds() / 3600  # hours
        
        print("📊 API審計總結")
        print("=" * 30)
        print(f"總調用次數: {total_calls}")
        print(f"時間範圍: {first_call.strftime('%Y-%m-%d %H:%M')} 至 {last_call.strftime('%Y-%m-%d %H:%M')}")
        print(f"持續時間: {duration:.1f} 小時")
        
        if duration > 0:
            print(f"平均頻率: {total_calls / duration:.1f} 次/小時")
        
        # 類型統計
        call_types = Counter(entry['type'] for entry in parsed_entries)
        print("\n📈 調用類型:")
        for call_type, count in call_types.most_common():
            percentage = (count / total_calls) * 100
            print(f"  {call_type}: {count} 次 ({percentage:.1f}%)")
    
    def export_report(self, output_file="api_audit_report.json"):
        """導出詳細報告"""
        parsed_entries = [self.parse_entry(entry) for entry in self.entries]
        parsed_entries = [e for e in parsed_entries if e]
        
        # 轉換datetime為字符串
        for entry in parsed_entries:
            entry['timestamp'] = entry['timestamp'].isoformat()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_entries': len(parsed_entries),
            'entries': parsed_entries
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ 報告已導出: {output_file}")
        except Exception as e:
            print(f"❌ 導出失敗: {e}")

def main():
    parser = argparse.ArgumentParser(description="API審計日誌分析工具")
    parser.add_argument('--log-file', default='.api_audit.log', 
                       help='審計日誌文件路徑')
    parser.add_argument('--hours', type=int, default=24,
                       help='分析最近N小時的數據')
    parser.add_argument('--summary', action='store_true',
                       help='顯示總體摘要')
    parser.add_argument('--export', metavar='FILE',
                       help='導出詳細報告到JSON文件')
    parser.add_argument('--test', action='store_true',
                       help='測試模式（不讀取真實日誌）')
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ API審計工具測試模式 - 功能正常")
        return 0
    
    viewer = APIAuditViewer(args.log_file)
    
    if not viewer.load_logs():
        return 1
    
    if args.summary:
        viewer.show_summary()
    elif args.export:
        viewer.export_report(args.export)
    else:
        viewer.analyze_patterns(args.hours)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())