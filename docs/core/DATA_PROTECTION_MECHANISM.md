# Data Protection Mechanism

## Overview

本文档描述项目中关键数据文件的保护机制，特别是项目元数据（`meta.json`）的原子写入实现。

## Problem Background

### 历史问题

在 2026-02-12 发现项目元数据文件损坏问题：
- **症状**：`meta.json` 文件在第188行处截断，导致JSON解析失败
- **影响**：前端无法读取项目列表，API返回500错误
- **原因**：后端在写入过程中被中断（Ctrl+C / 崩溃 / 断电）

### 旧实现的问题

```python
# ❌ 不安全的实现
def _save_meta(self, project_id: str, meta: ProjectMeta):
    meta_path = self._get_meta_path(project_id)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta.to_dict(), f, ensure_ascii=False, indent=2)
```

**风险点：**
1. **直接覆盖** - `'w'` 模式立即清空原文件
2. **无验证** - 不检查序列化是否成功
3. **无原子性** - 中断时文件处于不一致状态
4. **无异常处理** - 失败时留下损坏数据

## Solution: Atomic Write Pattern

### 实现原理

使用**临时文件 + 原子替换**模式确保数据完整性：

```
1. 序列化数据到内存
2. 写入临时文件 (.tmp)
3. 强制刷新到磁盘
4. 验证JSON格式
5. 原子替换原文件
```

### 代码实现

```python
def _save_meta(self, project_id: str, meta: ProjectMeta):
    """保存元数据（原子写入，防止损坏）"""
    meta_path = self._get_meta_path(project_id)
    temp_path = meta_path + '.tmp'
    
    try:
        # 1. 序列化数据（先验证能否成功序列化）
        data_dict = meta.to_dict()
        json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
        
        # 2. 写入临时文件
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
            f.flush()  # 确保写入磁盘
            os.fsync(f.fileno())  # 强制同步到磁盘
        
        # 3. 验证临时文件可读且JSON有效
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # 验证JSON格式
        
        # 4. 原子替换（rename是原子操作）
        os.replace(temp_path, meta_path)
        
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed to save meta for {project_id}: {e}")
        raise
```

### 保护机制特性

| 特性 | 说明 | 实现方式 |
|------|------|----------|
| ✅ **原子性** | 要么完全成功，要么完全失败 | `os.replace()` 原子操作 |
| ✅ **验证** | 写入后立即验证格式 | `json.load()` 检查 |
| ✅ **持久化** | 确保数据写入磁盘 | `fsync()` 强制同步 |
| ✅ **异常安全** | 失败时不破坏原文件 | 写临时文件 + try/except |
| ✅ **清理** | 失败时清理临时文件 | finally 或 except 块 |

## System-wide Protection

### 文件位置

**受保护的文件：**
- `data/projects/{project_id}/meta.json` - 项目元数据（核心）

**实现位置：**
- `src/core/project_manager_v2.py::_save_meta()`

### 备份策略

在修复损坏文件时，系统会自动创建备份：
```
data/projects/PROJ_001/meta.json      # 当前文件
data/projects/PROJ_001/meta.json.bak  # 自动备份
```

## Best Practices

### 对于开发者

1. **使用 ProjectManagerV2 API**
   ```python
   # ✅ 推荐
   project_manager_v2.update_project(project_id, name="New Name")
   
   # ❌ 避免
   meta = project_manager_v2.get_project(project_id)
   meta.name = "New Name"
   # 直接写文件
   with open(meta_path, 'w') as f:
       json.dump(meta.to_dict(), f)
   ```

2. **不要绕过保护机制**
   - 始终使用 `project_manager_v2` 的API
   - 不要直接操作 `meta.json` 文件

3. **异常处理**
   ```python
   try:
       project_manager_v2.update_project(project_id, **updates)
   except Exception as e:
       logger.error(f"Failed to update project: {e}")
       # 处理错误，原文件保持完整
   ```

### 对于运维

1. **备份数据**
   - 定期备份 `data/projects/` 目录
   - 关键操作前手动备份

2. **避免强制中断**
   - 使用正常的停止机制（API或信号）
   - 避免 `kill -9` 或直接断电

3. **监控日志**
   - 关注 `Failed to save meta` 错误
   - 检查磁盘空间和权限

## Troubleshooting

### 场景1：meta.json 损坏

**症状：**
```
{"detail":"Expecting value: line 188 column 21 (char 5347)"}
```

**解决方法：**
1. 检查是否有 `.bak` 备份
2. 使用备份恢复：
   ```bash
   cp data/projects/PROJ_001/meta.json.bak data/projects/PROJ_001/meta.json
   ```
3. 如果没有备份，手动修复JSON格式

### 场景2：临时文件残留

**症状：**
```
data/projects/PROJ_001/meta.json.tmp
```

**解决方法：**
- 临时文件通常在异常时自动清理
- 如果残留，安全删除即可（不影响主文件）

### 场景3：写入失败

**症状：**
```
Failed to save meta for PROJ_001: [Errno 28] No space left on device
```

**检查：**
1. 磁盘空间：`df -h`
2. 文件权限：`ls -l data/projects/PROJ_001/`
3. 目录权限：`ls -ld data/projects/PROJ_001/`

## Related Issues

- Issue #N/A (2026-02-12): meta.json corruption due to non-atomic writes
- Fixed in commit: [hash]

## Future Improvements

### 考虑中的增强

1. **自动备份机制**
   - 写入前自动创建 `.bak`
   - 保留最近N个版本

2. **完整性检查**
   - 启动时验证所有 `meta.json`
   - 自动修复/报告损坏

3. **事务支持**
   - 批量更新的事务包装
   - 失败时回滚所有更改

4. **文件锁**
   - 防止并发写入冲突
   - 使用 `fcntl.flock()` 或类似机制

## References

- Python `os.replace()`: https://docs.python.org/3/library/os.html#os.replace
- Atomic file writes: https://lwn.net/Articles/457667/
- File integrity best practices: https://github.com/pypa/pip/blob/main/src/pip/_internal/utils/filesystem.py
