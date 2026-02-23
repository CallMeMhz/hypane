# TODO

## 待讨论/实现

### 多 Panel 共享数据
当多个 panel 需要共享同一个数据源时，task 归属不明确。

可能方案：
1. **主从模式**：一个"主" panel 负责采集，其他 panel 读取它的数据
2. **共享存储**：约定 `data/shared/` 目录
3. **全局任务**：`scheduler/tasks/` 放不属于任何 panel 的全局任务

暂定用方案1，保持 panel 独立性。
