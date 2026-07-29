import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'Job Market Collector',
    description: '由用户触发采集 BOSS 岗位，仅同步到本机 Job Market Reality Check。',
    version: '1.0.7',
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
