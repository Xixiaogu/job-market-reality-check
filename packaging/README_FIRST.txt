招聘市场分析与投递决策系统 V1.0
================================

一、启动软件
------------
双击 JobMarketDecisionSystem.exe。

首次启动后，软件会：
1. 在本机启动 127.0.0.1:8765 服务；
2. 创建独立用户数据目录；
3. 打开浏览器首次设置页；
4. 引导安装随软件附带的浏览器扩展。

软件运行期间请不要结束 JobMarketDecisionSystem.exe 进程。

二、安装浏览器扩展
------------------
扩展目录：

browser-extension\chrome-mv3

安装步骤：
1. 在 Chrome 地址栏打开 chrome://extensions
2. 开启“开发者模式”
3. 点击“加载已解压的扩展程序”
4. 选择本软件目录中的 browser-extension\chrome-mv3
5. 回到首次设置页复制本地 API 令牌，并粘贴到扩展设置中

Edge 可打开 edge://extensions，步骤相同。

三、用户数据位置
----------------
软件数据默认保存在：

%LOCALAPPDATA%\JobMarketDecisionSystem

其中包含：
- data\job_market.db：岗位、档案和投递状态
- runtime\api_token.txt：本地扩展连接令牌
- logs\app.log：运行日志
- exports：导出文件
- backups：本地备份

升级或替换软件目录不会覆盖这里的数据。

四、安全说明
------------
- 服务只监听本机 127.0.0.1
- 数据库和令牌保存在本机
- 发布包不包含开发者的岗位数据、个人档案或 API 令牌
- 不要把 runtime\api_token.txt 内容发给其他人

五、故障排查
------------
无法启动：
1. 检查 8765 端口是否被占用
2. 查看 %LOCALAPPDATA%\JobMarketDecisionSystem\logs\app.log
3. 关闭已有软件进程后重新双击

扩展无法连接：
1. 确认桌面软件仍在运行
2. 确认 API 地址为 http://127.0.0.1:8765
3. 从首次设置页重新复制 API 令牌
4. 在扩展管理页重新加载扩展

版本：1.0.0
