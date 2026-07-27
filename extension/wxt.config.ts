import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'Job Market Collector',
    description: '采集 BOSS 岗位，同步本地 SQLite，并提供首次使用与个人档案冷启动引导。',
    version: '0.9.0',
    permissions: [
      'activeTab',
      'storage',
    ],
    host_permissions: [
      '*://zhipin.com/*',
      '*://*.zhipin.com/*',
      'http://127.0.0.1/*',
      'http://localhost/*',
    ],
    action: {
      default_title: '采集岗位并管理求职状态',
    },
  },
});
