#!/usr/bin/env python3
"""
規格驅動開發(SDD)任務調度器
管理SDD流程的自動化執行
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class SpecScheduler:
    """SDD規格調度器"""
    
    def __init__(self, base_path=".kiro/specs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 設置日誌
        self.setup_logging()
        
        # SDD階段定義
        self.stages = [
            'init',
            'requirements',  # BDD階段
            'design',       # DDD階段
            'tasks',        # 任務分解
            'implementation', # 實施階段
            'completed'
        ]
    
    def setup_logging(self):
        """設置日誌"""
        log_dir = Path('.claude/scheduler/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SpecScheduler')
    
    def create_spec(self, feature_name: str, description: str) -> Dict[str, Any]:
        """創建新的功能規格"""
        spec_dir = self.base_path / feature_name
        spec_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建規格狀態文件
        spec_data = {
            'feature_name': feature_name,
            'description': description,
            'status': 'init',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'stages': {
                'init': {
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat()
                },
                'requirements': {'status': 'pending'},
                'design': {'status': 'pending'},
                'tasks': {'status': 'pending'},
                'implementation': {'status': 'pending'},
                'completed': {'status': 'pending'}
            },
            'metadata': {
                'estimated_hours': 0,
                'priority': 'medium',
                'assigned_agents': [],
                'dependencies': []
            }
        }
        
        # 保存規格文件
        spec_file = spec_dir / 'spec.json'
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec_data, f, indent=2, ensure_ascii=False)
        
        # 創建佔位文件
        placeholder_files = [
            'requirements.md',
            'design.md', 
            'tasks.md'
        ]
        
        for filename in placeholder_files:
            filepath = spec_dir / filename
            if not filepath.exists():
                filepath.write_text(f"# {feature_name} - {filename.replace('.md', '').title()}\n\n待生成...\n")
        
        self.logger.info(f"創建規格: {feature_name}")
        return spec_data
    
    def update_stage_status(self, feature_name: str, stage: str, status: str, 
                           metadata: Optional[Dict] = None) -> bool:
        """更新階段狀態"""
        spec_file = self.base_path / feature_name / 'spec.json'
        
        if not spec_file.exists():
            self.logger.error(f"規格文件不存在: {feature_name}")
            return False
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec_data = json.load(f)
            
            # 更新階段狀態
            if stage in spec_data['stages']:
                spec_data['stages'][stage]['status'] = status
                spec_data['stages'][stage]['updated_at'] = datetime.now().isoformat()
                
                if status == 'completed':
                    spec_data['stages'][stage]['completed_at'] = datetime.now().isoformat()
                
                if metadata:
                    spec_data['stages'][stage].update(metadata)
            
            # 更新總體狀態
            spec_data['status'] = self._calculate_overall_status(spec_data['stages'])
            spec_data['updated_at'] = datetime.now().isoformat()
            
            # 保存更新
            with open(spec_file, 'w', encoding='utf-8') as f:
                json.dump(spec_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"更新規格 {feature_name} 階段 {stage} 為 {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新階段狀態失敗: {e}")
            return False
    
    def _calculate_overall_status(self, stages: Dict) -> str:
        """計算總體狀態"""
        for stage in reversed(self.stages):
            if stage in stages and stages[stage]['status'] == 'completed':
                return stage
        return 'init'
    
    def get_spec_status(self, feature_name: str) -> Optional[Dict]:
        """獲取規格狀態"""
        spec_file = self.base_path / feature_name / 'spec.json'
        
        if not spec_file.exists():
            return None
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"讀取規格狀態失敗: {e}")
            return None
    
    def list_specs(self, status_filter: Optional[str] = None) -> List[Dict]:
        """列出所有規格"""
        specs = []
        
        for spec_dir in self.base_path.iterdir():
            if spec_dir.is_dir():
                spec_data = self.get_spec_status(spec_dir.name)
                if spec_data:
                    if not status_filter or spec_data['status'] == status_filter:
                        specs.append(spec_data)
        
        return sorted(specs, key=lambda x: x['created_at'], reverse=True)
    
    def get_next_action(self, feature_name: str) -> Optional[str]:
        """獲取下一個建議動作"""
        spec_data = self.get_spec_status(feature_name)
        if not spec_data:
            return None
        
        current_status = spec_data['status']
        
        action_map = {
            'init': f'/spec-requirements {feature_name}',
            'requirements': f'/spec-design {feature_name}',
            'design': f'/spec-tasks {feature_name}',
            'tasks': f'開始實施 {feature_name}',
            'implementation': f'完成並測試 {feature_name}',
            'completed': None
        }
        
        return action_map.get(current_status)
    
    def generate_progress_report(self) -> str:
        """生成進度報告"""
        all_specs = self.list_specs()
        
        if not all_specs:
            return "📊 目前沒有進行中的規格"
        
        # 統計各階段數量
        stage_counts = {stage: 0 for stage in self.stages}
        for spec in all_specs:
            stage_counts[spec['status']] += 1
        
        report = ["📊 SDD規格進度報告", "=" * 30]
        report.append(f"總規格數量: {len(all_specs)}")
        report.append("")
        
        # 階段分布
        report.append("📈 階段分布:")
        for stage, count in stage_counts.items():
            if count > 0:
                percentage = (count / len(all_specs)) * 100
                report.append(f"  {stage}: {count} 個 ({percentage:.1f}%)")
        
        report.append("")
        
        # 進行中的規格
        active_specs = [s for s in all_specs if s['status'] not in ['completed']]
        if active_specs:
            report.append("🚀 進行中的規格:")
            for spec in active_specs[:5]:  # 只顯示前5個
                next_action = self.get_next_action(spec['feature_name'])
                report.append(f"  • {spec['feature_name']} ({spec['status']})")
                if next_action:
                    report.append(f"    下一步: {next_action}")
        
        return "\n".join(report)
    
    def cleanup_old_specs(self, days: int = 30):
        """清理舊的已完成規格"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for spec in self.list_specs('completed'):
            completed_at = datetime.fromisoformat(spec['updated_at'])
            if completed_at < cutoff_date:
                spec_dir = self.base_path / spec['feature_name']
                try:
                    # 移動到歸檔目錄而不是刪除
                    archive_dir = self.base_path.parent / 'archived_specs'
                    archive_dir.mkdir(exist_ok=True)
                    
                    import shutil
                    shutil.move(str(spec_dir), str(archive_dir / spec['feature_name']))
                    cleaned_count += 1
                    
                    self.logger.info(f"歸檔舊規格: {spec['feature_name']}")
                except Exception as e:
                    self.logger.error(f"歸檔規格失敗: {e}")
        
        return cleaned_count

def main():
    """主函數 - 用於命令行操作"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python spec_scheduler.py <command> [args...]")
        print("命令:")
        print("  list - 列出所有規格")
        print("  status <feature> - 查看規格狀態")
        print("  report - 生成進度報告")
        return
    
    scheduler = SpecScheduler()
    command = sys.argv[1]
    
    if command == 'list':
        specs = scheduler.list_specs()
        if specs:
            print("📋 所有規格:")
            for spec in specs:
                print(f"  • {spec['feature_name']} ({spec['status']})")
        else:
            print("📋 沒有找到規格")
    
    elif command == 'status' and len(sys.argv) > 2:
        feature_name = sys.argv[2]
        spec_data = scheduler.get_spec_status(feature_name)
        if spec_data:
            print(f"📊 {feature_name} 狀態:")
            print(f"  當前階段: {spec_data['status']}")
            print(f"  創建時間: {spec_data['created_at']}")
            print(f"  更新時間: {spec_data['updated_at']}")
            
            next_action = scheduler.get_next_action(feature_name)
            if next_action:
                print(f"  下一步: {next_action}")
        else:
            print(f"❌ 規格 {feature_name} 不存在")
    
    elif command == 'report':
        print(scheduler.generate_progress_report())
    
    else:
        print("❌ 無效命令")

if __name__ == '__main__':
    main()