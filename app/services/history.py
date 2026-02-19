"""
History service - 管理卡片数据的历史记录

数据存储在 data/history/{source}/ 目录下
文件命名：
- 按天: 2026-02-19.json
- 按小时: 2026-02-19_14.json
- 按时刻: 2026-02-19_14-30-00.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Literal

from app.config import DATA_DIR

HISTORY_DIR = DATA_DIR / "history"


def _ensure_dir(source: str) -> Path:
    """确保数据源目录存在"""
    dir_path = HISTORY_DIR / source
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def write_history(
    source: str,
    data: Any,
    granularity: Literal["day", "hour", "minute"] = "day",
    timestamp: Optional[datetime] = None,
) -> Path:
    """
    写入历史记录
    
    Args:
        source: 数据源名称 (如 "weather", "crypto")
        data: 要存储的数据
        granularity: 时间粒度
        timestamp: 时间戳，默认当前时间
    
    Returns:
        写入的文件路径
    """
    dir_path = _ensure_dir(source)
    ts = timestamp or datetime.now(timezone.utc)
    
    if granularity == "day":
        filename = ts.strftime("%Y-%m-%d.json")
    elif granularity == "hour":
        filename = ts.strftime("%Y-%m-%d_%H.json")
    else:  # minute
        filename = ts.strftime("%Y-%m-%d_%H-%M-%S.json")
    
    file_path = dir_path / filename
    
    record = {
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "data": data,
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    return file_path


def read_latest(source: str) -> Optional[dict]:
    """
    读取最新的历史记录
    
    Args:
        source: 数据源名称
    
    Returns:
        最新记录的 data 字段，或 None
    """
    dir_path = HISTORY_DIR / source
    if not dir_path.exists():
        return None
    
    # 按文件名倒序，取最新的
    files = sorted(dir_path.glob("*.json"), reverse=True)
    if not files:
        return None
    
    with open(files[0], "r", encoding="utf-8") as f:
        record = json.load(f)
    
    return record.get("data")


def read_history(
    source: str,
    range: str = "7d",
) -> list[dict]:
    """
    读取历史记录
    
    Args:
        source: 数据源名称
        range: 时间范围 (如 "7d", "24h", "30d")
    
    Returns:
        历史记录列表 [{"timestamp": ..., "data": ...}, ...]
    """
    dir_path = HISTORY_DIR / source
    if not dir_path.exists():
        return []
    
    # 解析范围
    amount = int(range[:-1])
    unit = range[-1]
    
    now = datetime.now(timezone.utc)
    
    if unit == "d":
        # 按天筛选
        from datetime import timedelta
        cutoff = now - timedelta(days=amount)
    elif unit == "h":
        from datetime import timedelta
        cutoff = now - timedelta(hours=amount)
    else:
        cutoff = now
    
    records = []
    for file_path in sorted(dir_path.glob("*.json")):
        # 从文件名解析时间（粗略判断）
        name = file_path.stem  # 如 "2026-02-19" 或 "2026-02-19_14"
        try:
            if "_" in name:
                if "-" in name.split("_")[1]:
                    # minute: 2026-02-19_14-30-00
                    file_time = datetime.strptime(name, "%Y-%m-%d_%H-%M-%S").replace(tzinfo=timezone.utc)
                else:
                    # hour: 2026-02-19_14
                    file_time = datetime.strptime(name, "%Y-%m-%d_%H").replace(tzinfo=timezone.utc)
            else:
                # day: 2026-02-19
                file_time = datetime.strptime(name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            if file_time >= cutoff:
                with open(file_path, "r", encoding="utf-8") as f:
                    records.append(json.load(f))
        except ValueError:
            continue
    
    return records


def list_sources() -> list[str]:
    """列出所有数据源"""
    if not HISTORY_DIR.exists():
        return []
    return [d.name for d in HISTORY_DIR.iterdir() if d.is_dir()]
