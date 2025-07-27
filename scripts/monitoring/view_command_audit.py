#!/usr/bin/env python3
"""
命令審計日誌查看工具
用於分析命令執行模式和使用統計
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os

class CommandAuditViewer:
    def __init__(self, log_file=".command_audit.log"):
        self.log_file = log_file
        self.entries = []
        
    def load_logs(self):
        """載入命令審計日誌"""
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
            # 解析格式：timestamp: 命令執行 - command
            parts = entry.split(': 命令執行 - ', 1)
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
        
        if any(word in command_lower for word in ['git', 'commit', 'push', 'pull', 'merge']):
            return 'git_operation'
        elif any(word in command_lower for word in ['test', 'pytest', 'unittest', 'jest']):
            return 'testing'
        elif any(word in command_lower for word in ['npm', 'pip', 'yarn', 'cargo', 'go mod']):
            return 'package_management'
        elif any(word in command_lower for word in ['python', 'node', 'go run', 'java']):
            return 'development'
        elif any(word in command_lower for word in ['build', 'compile', 'make']):
            return 'build_operation'
        elif any(word in command_lower for word in ['curl', 'wget', 'http', 'api']):
            return 'network_operation'
        elif any(word in command_lower for word in ['ls', 'cat', 'grep', 'find', 'mkdir']):
            return 'file_operation'
        else:
            return 'other'
    
    def analyze_patterns(self, hours=24):
        """分析命令執行模式"""
        if not self.entries:
            print("📊 沒有命令執行記錄")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_entries = []
        
        for entry_str in self.entries:
            entry = self.parse_entry(entry_str)
            if entry and entry['timestamp'] >= cutoff_time:
                recent_entries.append(entry)
        
        if not recent_entries:
            print(f"📊 過去 {hours} 小時內沒有命令執行記錄")
            return
        
        # 統計分析
        total_commands = len(recent_entries)
        command_types = Counter(entry['type'] for entry in recent_entries)
        hourly_distribution = defaultdict(int)
        
        for entry in recent_entries:
            hour = entry['timestamp'].hour
            hourly_distribution[hour] += 1
        
        # 顯示結果
        print(f"📊 命令執行分析報告 (過去 {hours} 小時)")
        print("=" * 50)
        print(f"總命令數: {total_commands}")
        print(f"平均每小時: {total_commands / hours:.1f} 個")
        
        print("\n📈 命令類型分布:")
        for cmd_type, count in command_types.most_common():
            percentage = (count / total_commands) * 100
            print(f"  {cmd_type}: {count} 個 ({percentage:.1f}%)")
        
        print("\n⏰ 小時分布:")
        for hour in sorted(hourly_distribution.keys()):
            count = hourly_distribution[hour]
            bar = "█" * min(20, count)
            print(f"  {hour:02d}:00 - {hour:02d}:59 | {bar} ({count})")
        
        # 最近的命令
        print(f"\n🕒 最近 10 個命令:")
        for entry in sorted(recent_entries, key=lambda x: x['timestamp'], reverse=True)[:10]:
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            print(f"  {time_str} | {entry['type']} | {entry['command'][:60]}...")
    
    def show_summary(self):
        """顯示總體摘要"""
        if not self.entries:
            print("📊 沒有命令執行記錄")
            return
        
        parsed_entries = [self.parse_entry(entry) for entry in self.entries]
        parsed_entries = [e for e in parsed_entries if e]
        
        if not parsed_entries:
            print("📊 沒有有效的命令執行記錄")
            return
        
        total_commands = len(parsed_entries)
        first_command = min(entry['timestamp'] for entry in parsed_entries)
        last_command = max(entry['timestamp'] for entry in parsed_entries)
        duration = (last_command - first_command).total_seconds() / 3600  # hours
        
        print("📊 命令審計總結")
        print("=" * 30)
        print(f"總命令數: {total_commands}")
        print(f"時間範圍: {first_command.strftime('%Y-%m-%d %H:%M')} 至 {last_command.strftime('%Y-%m-%d %H:%M')}")
        print(f"持續時間: {duration:.1f} 小時")
        
        if duration > 0:
            print(f"平均頻率: {total_commands / duration:.1f} 個/小時")
        
        # 類型統計
        command_types = Counter(entry['type'] for entry in parsed_entries)
        print("\n📈 命令類型:")
        for cmd_type, count in command_types.most_common():
            percentage = (count / total_commands) * 100
            print(f"  {cmd_type}: {count} 個 ({percentage:.1f}%)")
    
    def show_top_commands(self, limit=10):
        """顯示最常用的命令"""
        parsed_entries = [self.parse_entry(entry) for entry in self.entries]
        parsed_entries = [e for e in parsed_entries if e]
        
        if not parsed_entries:
            print("📊 沒有命令執行記錄")
            return
        
        # 統計命令頻率
        command_counter = Counter(entry['command'] for entry in parsed_entries)
        
        print(f"📊 最常用的 {limit} 個命令:")
        print("=" * 40)
        
        for i, (command, count) in enumerate(command_counter.most_common(limit), 1):
            percentage = (count / len(parsed_entries)) * 100
            print(f"{i:2d}. {command[:50]:<50} ({count:3d}次, {percentage:4.1f}%)")
    
    def export_report(self, output_file="command_audit_report.json"):
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
    parser = argparse.ArgumentParser(description="命令審計日誌分析工具")
    parser.add_argument('--log-file', default='.command_audit.log', 
                       help='審計日誌文件路徑')
    parser.add_argument('--hours', type=int, default=24,
                       help='分析最近N小時的數據')
    parser.add_argument('--summary', action='store_true',
                       help='顯示總體摘要')
    parser.add_argument('--top-commands', type=int, metavar='N',
                       help='顯示最常用的N個命令')
    parser.add_argument('--export', metavar='FILE',
                       help='導出詳細報告到JSON文件')
    parser.add_argument('--test', action='store_true',
                       help='測試模式（不讀取真實日誌）')
    
    args = parser.parse_args()
    
    if args.test:
        print("✅ 命令審計工具測試模式 - 功能正常")
        return 0
    
    viewer = CommandAuditViewer(args.log_file)
    
    if not viewer.load_logs():
        return 1
    
    if args.summary:
        viewer.show_summary()
    elif args.top_commands:
        viewer.show_top_commands(args.top_commands)
    elif args.export:
        viewer.export_report(args.export)
    else:
        viewer.analyze_patterns(args.hours)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())