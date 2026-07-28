# 外观设置与界面产品化收口

分支：`feature/appearance-settings-and-ui-cleanup`

## 目标

- 在“扩展与设置”中提供“标准浅色”和“Windows Acrylic”两种正式外观。
- 保存设置后自动重启桌面应用并应用新材质。
- 移除用户界面中的 Phase、内部引擎编号和看板版本号。
- 提升市场分析二级导航、服务状态、说明文字和副标题的字号与对比度。
- 保留岗位采集、自动刷新、决策重算和市场分析逻辑不变。

## 设置文件

外观选择保存到：

```text
%LOCALAPPDATA%\JobMarketDecisionSystem\settings.json
```

示例：

```json
{
  "appearance": "acrylic"
}
```

## 重启流程

```text
设置页保存外观
→ 本地 API 原子写入 settings.json
→ 写入 restart-app.request
→ 桌面壳停止服务并释放单实例锁
→ 重新启动当前 EXE
→ 在创建 WebView2 前读取外观设置
```

## 手动验收

1. 设置页中可选择“标准浅色”和“Windows Acrylic”。
2. 点击“保存并重启应用”后窗口自动关闭并重新打开。
3. 重启后仍停留在同一软件版本，外观按选择生效。
4. 两种模式下岗位采集、自动刷新、重新计算和分析看板正常。
5. 用户页面不再显示 Phase 9.1、8.2A、8.1C、7B.2、8.2C、v1.2 等内部标记。
6. 市场分析二级导航和顶部状态文字明显更易读。
7. Acrylic 下长文本和岗位卡片仍有足够对比度。
