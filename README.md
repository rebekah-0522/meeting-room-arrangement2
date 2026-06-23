# Foxconn 会议室预约系统

C01 / C02 · 4F 会议室统一预约与管理平台，供 Meeting EPM 及各部门同事使用。

## 功能概览

- **21 间会议室**：C01-4F（11 间）、C02-4F（10 间），Webex / 投影仪 / 容量信息一目了然
- **30 分钟分段预约**：08:00 – 20:30 全天时段
- **权限规则**：
  - ≤ 3 天：自行预约
  - \> 3 天：需 Meeting EPM 审批
  - \> 7 天：仅 EPM 可安排
  - 40 人以上大会议室：仅限项目负责人
  - 每月取消 \> 3 次：标记「信用不良」，后续需 EPM 审批
- **日 / 周 / 月视图**查看排期
- **CSV 导出**：周排期、月视图、Build 阶段总表、操作日志
- **CSV 批量导入**：自动检测冲突，支持覆盖确认
- **操作日志**：记录所有关键操作，便于追溯
- **EPM 管理后台**：Build 管理、会议室属性编辑、审批待办

## 使用方法

1. 用浏览器打开 `index.html`
2. 输入姓名、邮箱并选择身份登录
3. Meeting EPM 请选择「Meeting EPM」身份，或使用邮箱 `rebekah.xy.he@mail.foxconn.com`

## 联系人

如有特殊情况请联系 Meeting EPM **Rebekah**：rebekah.xy.he@mail.foxconn.com

## 说明

- 数据保存在浏览器 **localStorage** 中，同一台电脑同一浏览器可持久化
- 邮件通知为**模拟**（记录在 EPM 管理 → 邮件记录），生产环境需对接企业邮件 API
- 建议部署到内网 Web 服务器供团队共用；多人协作需后续接入后端数据库

## 文件结构

```
Meeting Room Arrangement/
├── index.html
├── css/style.css
├── js/
│   ├── data.js      # 会议室数据与常量
│   ├── storage.js   # 本地存储
│   ├── booking.js   # 预约逻辑
│   ├── export.js    # 导入导出
│   └── app.js       # 界面交互
└── README.md
```
