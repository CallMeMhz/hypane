"""
Scheduler decorators for panel handlers.

Usage in handler.py:
```python
from scheduler.decorators import scheduled

@scheduled("*/30 * * * *")
async def collect_weather(data: dict) -> dict:
    '''每30分钟采集天气'''
    return data

@scheduled("0 9 * * *")
def daily_summary(data: dict) -> dict:
    '''每天9点执行'''
    return data
```

Cron 格式: "分 时 日 月 周"
- */5 * * * *    每5分钟
- 0 * * * *      每小时
- 0 9 * * *      每天9:00
- 0 9 * * 1      每周一9:00
- 0 0 1 * *      每月1日
"""


def scheduled(cron: str):
    """
    标记函数为定时任务
    
    Args:
        cron: Cron 表达式
    
    函数签名: (data: dict) -> dict
    - data: 当前 panel 的 data.json 内容
    - 返回: 更新后的 data（会自动保存）
    """
    def decorator(func):
        func._scheduled_cron = cron
        return func
    return decorator
