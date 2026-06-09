# Flyway Migration Hygiene — Code/Migration 必须同步

## Core Rule

**任何引用新数据库对象（表/列/索引/存储过程）的代码变更，必须在同一 PR 或同一 commit 内包含对应的 Flyway migration SQL。**

代码和 migration 分开提交 = 生产事故。

## 常见遗漏模式

### 1. Native Query 引用新表，但无 migration
```java
// TxDisplayNoService.java — 引用了 tx_display_no_registry 表
em.createNativeQuery("""
    INSERT IGNORE INTO tx_display_no_registry (biz_date, random_suffix, display_no)
    VALUES (:bizDate, :suffix, :displayNo)
    """)
```
**检查点**: grep `INSERT INTO`, `UPDATE`, `DELETE FROM`, `SELECT ... FROM` 中的表名，确认每个表都有对应 migration。

### 2. JPA Entity 新增 @Table 映射，但无 CREATE TABLE
```java
@Entity
@Table(name = "new_feature_config")  // ← 这个表存在吗？
public class NewFeatureConfig { ... }
```

### 3. ALTER TABLE 在代码中读取新列，但 migration 跑失败被跳过
- Flyway migration 失败（如 `ADD COLUMN` 时列已存在）→ `success=0`
- 后续 migration 被阻塞不执行
- 代码上去了但 schema 没跟上
- **修复**: 补一个 repair migration（参考 V10169 模式：UPDATE flyway_schema_history + 重跑业务逻辑）

### 4. Stored Procedure / Function 在代码中调用，但无 CREATE PROCEDURE migration

## PR Review Checklist

```
[ ] 新增的 Java/Kotlin native query 中的所有表名 → 都有对应 migration
[ ] 新增的 @Entity / @Table 注解 → 表已存在或 migration 中有 CREATE TABLE
[ ] 新增的 @Column 注解 → 列已存在或 migration 中有 ALTER TABLE ADD COLUMN
[ ] migration 文件编号连续，无跳号
[ ] migration 文件在正确的 db/migration 目录下（不是 test/resources）
[ ] ALTER TABLE 用 INFORMATION_SCHEMA 幂等守卫（MySQL 不支持 IF NOT EXISTS）
```

## 快速诊断：线上表不存在

```sql
-- 1. 检查表是否存在
SHOW TABLES LIKE 'table_name';

-- 2. 检查 Flyway 历史
SELECT version, description, success FROM flyway_schema_history
WHERE version LIKE '101%' ORDER BY CAST(version AS UNSIGNED);

-- 3. 找到 success=0 的 migration（阻塞后续所有 migration）
SELECT version, description, installed_on FROM flyway_schema_history
WHERE success = 0 ORDER BY version;
```

## 修复模板（Flyway migration 失败导致后续被阻塞）

```sql
-- Step 1: 修复失败的 migration 记录
UPDATE flyway_schema_history SET success = 1 WHERE version = 'XXXX' AND success = 0;

-- Step 2: 重跑被阻塞的业务逻辑（idempotent）
-- ... 用 stored procedure + cursor 或 UPDATE ... JOIN 实现 ...
```

## UVISA 实际案例

- **V10167 → V10168 阻塞**: `admin_member.password_must_change` 列已存在，ALTER 失败，V10168 未执行
- **dcf083a6 遗漏**: `TxDisplayNoService` 用了 `tx_display_no_registry` 表，commit 只有 Java 没有 SQL migration
