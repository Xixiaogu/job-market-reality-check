import './style.css';

type BadgeType =
  | 'loading'
  | 'boss'
  | 'normal'
  | 'error';

type ApiBadgeType =
  | 'checking'
  | 'online'
  | 'unpaired'
  | 'offline'
  | 'error';

interface JobCoreData {
  schemaVersion: string;
  jobId: string | null;
  jobTitle: string | null;
  salary: string | null;
  city: string | null;
  experience: string | null;
  internshipDays: string | null;
  internshipDuration: string | null;
  education: string | null;
  companyShortName: string | null;
  companyFullName: string | null;
  financingStage: string | null;
  companySize: string | null;
  industry: string | null;
  jobTags: string[];
  jobDescription: string | null;
  sourceUrl: string;
  collectedAt: string;
  extraction: Record<string, string>;
}

interface StoredJob extends JobCoreData {
  savedAt: string;
}

interface DomDiagnostic {
  schemaVersion: string;
  collectedAt: string;
  page: {
    title: string;
    origin: string;
    pathname: string;
    viewportWidth: number;
    viewportHeight: number;
  };
  extractedCore: JobCoreData;
  candidateElements: unknown[];
  anchorElements: unknown[];
  notes: string[];
}

interface PipelineRun {
  run_id?: number;
  status?: string;
  completed_steps?: number;
  current_step?: string;
  error_message?: string;
}

interface ApiHealthResponse {
  ok: boolean;
  job_count: number;
  dashboard_exists: boolean;
  latest_pipeline: PipelineRun | null;
}

interface ApiRuntimeResponse {
  database_path: string;
  token_path: string;
  dashboard_path: string;
}

interface PipelineSchedule {
  started: boolean;
  run: PipelineRun | null;
}

interface ApiUpsertResponse {
  ok: boolean;
  action: 'inserted' | 'updated' | 'unchanged';
  job_id: string;
  revision: number;
  job_count: number;
  pipeline?: PipelineSchedule;
}

interface ApiBulkUpsertResponse {
  ok: boolean;
  results: {
    input: number;
    inserted: number;
    updated: number;
    unchanged: number;
    failed: number;
    errors: unknown[];
  };
  job_count: number;
  pipeline?: PipelineSchedule;
}

interface ApiPipelineRunResponse extends PipelineSchedule {
  ok: boolean;
}

interface ApiPipelineStatusResponse {
  run: PipelineRun | null;
  dashboard_exists: boolean;
  dashboard_path: string;
}

type UserStatus =
  | 'to_review'
  | 'interested'
  | 'preparing'
  | 'applied'
  | 'written_test'
  | 'interview'
  | 'offer'
  | 'rejected'
  | 'abandoned';

interface JobManagementState {
  job_id: string;
  user_status: UserStatus;
  listing_status: string;
  quality_override: string;
  category_manual: string;
  notes: string;
  archived_at: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

interface ApiManagedJobResponse {
  job_id: string;
  management: JobManagementState;
}

interface ApiManagementPatchResponse {
  ok: boolean;
  job_id: string;
  changed: boolean;
  changed_fields: string[];
  analysis_required: boolean;
  management: JobManagementState;
}

interface ProfileOnboardingStatus {
  profile_initialized: boolean;
  completion_percent: number;
  job_count: number;
  next_action: string;
  action_label: string;
  recommendation_basis: string;
  project_is_optional: boolean;
  maturity: {
    stage: string;
    label: string;
    confidence: string;
    progress: number;
    message: string;
  };
}

const STORAGE_KEY = 'collectedJobsV1';
const API_TOKEN_KEY = 'localApiTokenV1';
const AUTO_ANALYZE_KEY = 'autoAnalyzeAfterSyncV1';
const API_BASE = 'http://127.0.0.1:8765';
const API_TIMEOUT_MS = 4000;
const PIPELINE_POLL_INTERVAL_MS = 1100;
const PIPELINE_POLL_LIMIT = 120;

function requireElement<T extends Element>(
  selector: string,
): T {
  const element =
    document.querySelector<T>(selector);

  if (!element) {
    throw new Error(
      `未找到页面元素：${selector}`,
    );
  }

  return element;
}

const app = requireElement<HTMLElement>('#app');

app.innerHTML = `
  <section class="page">
    <header class="header">
      <div>
        <p class="eyebrow">
          JOB MARKET COLLECTOR
        </p>
        <h1>岗位采集器</h1>
      </div>

      <span
        id="site-badge"
        class="badge badge-loading"
      >
        检查中
      </span>
    </header>

    <section class="summary-strip">
      <div>
        <span class="summary-label">
          浏览器本地
        </span>
        <strong id="saved-count" class="summary-value">
          0
        </strong>
      </div>

      <span id="storage-status" class="storage-status">
        正在读取
      </span>
    </section>

    <section class="api-panel">
      <div class="api-heading">
        <div>
          <span class="panel-kicker">LOCAL API</span>
          <h2>SQLite 自动同步</h2>
        </div>

        <span
          id="api-status-badge"
          class="api-badge api-badge-checking"
        >
          检查中
        </span>
      </div>

      <p id="api-summary" class="api-summary">
        正在检查 127.0.0.1:8765。
      </p>

      <div class="token-row">
        <input
          id="api-token-input"
          class="token-input"
          type="password"
          autocomplete="off"
          spellcheck="false"
          placeholder="粘贴 api_token.txt 内容"
        >

        <button
          id="save-token-button"
          class="mini-button"
          type="button"
        >
          保存并测试
        </button>
      </div>

      <div class="api-options-row">
        <label class="checkbox-label">
          <input
            id="auto-analyze-checkbox"
            type="checkbox"
            checked
          >
          同步后自动更新分析看板
        </label>

        <button
          id="clear-token-button"
          class="link-button"
          type="button"
        >
          清除令牌
        </button>
      </div>

      <p id="pipeline-status" class="pipeline-status">
        分析状态：等待连接
      </p>

      <div class="api-actions">
        <button
          id="sync-all-button"
          class="secondary-button"
          type="button"
          disabled
        >
          同步本地全部
        </button>

        <button
          id="open-dashboard-button"
          class="secondary-button"
          type="button"
        >
          打开看板
        </button>
      </div>
    </section>

    <section id="cold-start-panel" class="cold-start-panel is-hidden">
      <div class="cold-start-heading">
        <div>
          <span class="panel-kicker">FIRST RUN</span>
          <h2 id="cold-start-title">首次使用引导</h2>
        </div>
        <span id="cold-start-badge" class="cold-start-badge">待检查</span>
      </div>
      <p id="cold-start-message" class="cold-start-message">
        连接本地 API 后显示档案与岗位样本状态。
      </p>
      <div class="cold-start-progress"><i id="cold-start-progress" style="width:0%"></i></div>
      <div class="cold-start-actions">
        <button id="open-profile-button" class="secondary-button" type="button">打开个人档案</button>
      </div>
    </section>

    <section class="info-card">
      <div class="field job-field">
        <span class="field-label">
          岗位名称
        </span>
        <p
          id="job-title"
          class="field-value job-title"
        >
          正在读取……
        </p>
      </div>

      <div class="field company-field">
        <span class="field-label">公司</span>
        <p id="company-name" class="field-value">—</p>
        <p id="company-meta" class="field-subvalue">—</p>
      </div>

      <div class="field-grid">
        <div class="field compact-field">
          <span class="field-label">薪资</span>
          <p id="salary" class="field-value">—</p>
        </div>

        <div class="field compact-field">
          <span class="field-label">城市</span>
          <p id="city" class="field-value">—</p>
        </div>

        <div class="field compact-field">
          <span class="field-label">经验</span>
          <p id="experience" class="field-value">—</p>
        </div>

        <div class="field compact-field">
          <span class="field-label">学历</span>
          <p id="education" class="field-value">—</p>
        </div>

        <div class="field compact-field">
          <span class="field-label">出勤</span>
          <p id="internship-days" class="field-value">—</p>
        </div>

        <div class="field compact-field">
          <span class="field-label">周期</span>
          <p id="internship-duration" class="field-value">—</p>
        </div>
      </div>

      <div class="field">
        <span class="field-label">岗位标签</span>
        <div id="job-tags" class="tag-list">
          <span class="empty-inline">—</span>
        </div>
      </div>

      <div class="field">
        <span class="field-label">职位描述</span>
        <p id="description-status" class="field-value">
          正在读取……
        </p>
        <p id="description-preview" class="description-preview"></p>
      </div>
    </section>

    <section class="quick-management-panel">
      <div class="quick-management-heading">
        <div>
          <span class="panel-kicker">JOB STATUS</span>
          <h2>快捷求职管理</h2>
        </div>

        <span
          id="quick-management-badge"
          class="quick-management-badge"
        >
          等待岗位
        </span>
      </div>

      <div class="quick-management-grid">
        <label class="quick-field">
          <span>个人求职进度</span>
          <select
            id="quick-user-status"
            class="quick-select"
            disabled
          >
            <option value="to_review">待判断</option>
            <option value="interested">感兴趣</option>
            <option value="preparing">准备投递</option>
            <option value="applied">已投递</option>
            <option value="written_test">笔试</option>
            <option value="interview">面试</option>
            <option value="offer">Offer</option>
            <option value="rejected">被拒</option>
            <option value="abandoned">放弃</option>
          </select>
        </label>

        <label class="quick-field quick-notes-field">
          <span>个人备注</span>
          <textarea
            id="quick-notes"
            class="quick-notes"
            rows="2"
            maxlength="600"
            disabled
            placeholder="例如：适合Agent项目经历；需要补SQL案例"
          ></textarea>
        </label>
      </div>

      <p
        id="quick-management-status"
        class="quick-management-status"
      >
        读取岗位后显示当前求职状态。
      </p>

      <div class="quick-management-actions">
        <button
          id="save-quick-status-button"
          class="secondary-button"
          type="button"
          disabled
        >
          保存求职状态
        </button>

        <button
          id="open-management-button"
          class="secondary-button"
          type="button"
          disabled
        >
          打开管理中心
        </button>
      </div>
    </section>

    <p id="message" class="message">
      正在读取当前岗位。
    </p>

    <div class="actions">
      <button
        id="collect-button"
        class="primary-button"
        type="button"
        disabled
      >
        采集当前岗位
      </button>

      <button
        id="refresh-button"
        class="secondary-button"
        type="button"
      >
        重新读取
      </button>
    </div>

    <section class="collection-panel">
      <div class="section-header">
        <h2>最近采集</h2>
        <button
          id="clear-button"
          class="danger-link"
          type="button"
        >
          清空
        </button>
      </div>

      <div id="recent-jobs" class="recent-jobs">
        <p class="empty-state">暂无采集记录</p>
      </div>
    </section>

    <div class="export-grid">
      <button
        id="export-jsonl-button"
        class="secondary-button"
        type="button"
      >
        备份 JSONL
      </button>

      <button
        id="export-csv-button"
        class="secondary-button"
        type="button"
      >
        备份 CSV
      </button>
    </div>

    <button
      id="diagnostic-button"
      class="text-button"
      type="button"
    >
      导出 DOM 诊断
    </button>

    <p class="footer-note">
      Phase 8.1C：首次采集可直接建立岗位样本，档案建议会标明真实岗位或冷启动来源。
    </p>
  </section>
`;

const badgeElement =
  requireElement<HTMLElement>('#site-badge');
const savedCountElement =
  requireElement<HTMLElement>('#saved-count');
const storageStatusElement =
  requireElement<HTMLElement>('#storage-status');
const apiStatusBadgeElement =
  requireElement<HTMLElement>('#api-status-badge');
const apiSummaryElement =
  requireElement<HTMLElement>('#api-summary');
const apiTokenInput =
  requireElement<HTMLInputElement>('#api-token-input');
const saveTokenButton =
  requireElement<HTMLButtonElement>('#save-token-button');
const clearTokenButton =
  requireElement<HTMLButtonElement>('#clear-token-button');
const autoAnalyzeCheckbox =
  requireElement<HTMLInputElement>('#auto-analyze-checkbox');
const pipelineStatusElement =
  requireElement<HTMLElement>('#pipeline-status');
const syncAllButton =
  requireElement<HTMLButtonElement>('#sync-all-button');
const openDashboardButton =
  requireElement<HTMLButtonElement>('#open-dashboard-button');
const coldStartPanel =
  requireElement<HTMLElement>('#cold-start-panel');
const coldStartTitleElement =
  requireElement<HTMLElement>('#cold-start-title');
const coldStartBadgeElement =
  requireElement<HTMLElement>('#cold-start-badge');
const coldStartMessageElement =
  requireElement<HTMLElement>('#cold-start-message');
const coldStartProgressElement =
  requireElement<HTMLElement>('#cold-start-progress');
const openProfileButton =
  requireElement<HTMLButtonElement>('#open-profile-button');
const jobTitleElement =
  requireElement<HTMLElement>('#job-title');
const companyNameElement =
  requireElement<HTMLElement>('#company-name');
const companyMetaElement =
  requireElement<HTMLElement>('#company-meta');
const salaryElement =
  requireElement<HTMLElement>('#salary');
const cityElement =
  requireElement<HTMLElement>('#city');
const experienceElement =
  requireElement<HTMLElement>('#experience');
const daysElement =
  requireElement<HTMLElement>('#internship-days');
const durationElement =
  requireElement<HTMLElement>('#internship-duration');
const educationElement =
  requireElement<HTMLElement>('#education');
const tagsElement =
  requireElement<HTMLElement>('#job-tags');
const descriptionStatusElement =
  requireElement<HTMLElement>('#description-status');
const descriptionPreviewElement =
  requireElement<HTMLElement>('#description-preview');
const quickManagementBadgeElement =
  requireElement<HTMLElement>('#quick-management-badge');
const quickUserStatusElement =
  requireElement<HTMLSelectElement>('#quick-user-status');
const quickNotesElement =
  requireElement<HTMLTextAreaElement>('#quick-notes');
const quickManagementStatusElement =
  requireElement<HTMLElement>('#quick-management-status');
const saveQuickStatusButton =
  requireElement<HTMLButtonElement>('#save-quick-status-button');
const openManagementButton =
  requireElement<HTMLButtonElement>('#open-management-button');
const messageElement =
  requireElement<HTMLElement>('#message');
const recentJobsElement =
  requireElement<HTMLElement>('#recent-jobs');
const collectButton =
  requireElement<HTMLButtonElement>('#collect-button');
const refreshButton =
  requireElement<HTMLButtonElement>('#refresh-button');
const clearButton =
  requireElement<HTMLButtonElement>('#clear-button');
const exportJsonlButton =
  requireElement<HTMLButtonElement>('#export-jsonl-button');
const exportCsvButton =
  requireElement<HTMLButtonElement>('#export-csv-button');
const diagnosticButton =
  requireElement<HTMLButtonElement>('#diagnostic-button');

let currentJob: JobCoreData | null = null;
let storedJobs: StoredJob[] = [];
let apiToken = '';
let apiConnected = false;
let apiServiceOnline = false;
let apiJobCount: number | null = null;
let pipelinePollGeneration = 0;
let currentManagementJobId: string | null = null;
let currentManagementExists = false;
let profileOnboarding: ProfileOnboardingStatus | null = null;

function setBadge(
  type: BadgeType,
  text: string,
): void {
  badgeElement.className =
    `badge badge-${type}`;
  badgeElement.textContent = text;
}

function setApiBadge(
  type: ApiBadgeType,
  text: string,
): void {
  apiStatusBadgeElement.className =
    `api-badge api-badge-${type}`;
  apiStatusBadgeElement.textContent = text;
}

function setText(
  element: HTMLElement,
  value: string | null,
): void {
  element.textContent = value || '—';
}

function isBossPage(rawUrl: string): boolean {
  try {
    const hostname =
      new URL(rawUrl).hostname.toLowerCase();

    return (
      hostname === 'zhipin.com' ||
      hostname.endsWith('.zhipin.com')
    );
  } catch {
    return false;
  }
}

function isStringOrNull(
  value: unknown,
): value is string | null {
  return (
    typeof value === 'string' ||
    value === null
  );
}

function isJobCoreData(
  value: unknown,
): value is JobCoreData {
  if (
    typeof value !== 'object' ||
    value === null
  ) {
    return false;
  }

  const record =
    value as Record<string, unknown>;

  return (
    typeof record.schemaVersion === 'string' &&
    isStringOrNull(record.jobTitle) &&
    isStringOrNull(record.salary) &&
    typeof record.sourceUrl === 'string' &&
    (
      record.jobTags === undefined ||
      Array.isArray(record.jobTags)
    ) &&
    typeof record.extraction === 'object' &&
    record.extraction !== null
  );
}

function isStoredJob(
  value: unknown,
): value is StoredJob {
  if (!isJobCoreData(value)) {
    return false;
  }

  return (
    'savedAt' in value &&
    typeof value.savedAt === 'string'
  );
}

function isDomDiagnostic(
  value: unknown,
): value is DomDiagnostic {
  if (
    typeof value !== 'object' ||
    value === null
  ) {
    return false;
  }

  return (
    'schemaVersion' in value &&
    typeof value.schemaVersion === 'string' &&
    'candidateElements' in value &&
    Array.isArray(value.candidateElements) &&
    'anchorElements' in value &&
    Array.isArray(value.anchorElements) &&
    'notes' in value &&
    Array.isArray(value.notes)
  );
}

async function getCurrentTab() {
  const tabs = await browser.tabs.query({
    active: true,
    currentWindow: true,
  });

  const currentTab = tabs[0];

  if (!currentTab) {
    throw new Error(
      '没有找到当前活动标签页',
    );
  }

  return currentTab;
}

async function requestJobCore(
  tabId: number,
): Promise<JobCoreData> {
  const response: unknown =
    await browser.tabs.sendMessage(
      tabId,
      {
        type: 'GET_CURRENT_JOB_CORE',
      },
    );

  if (!isJobCoreData(response)) {
    throw new Error(
      '岗位字段数据格式不正确',
    );
  }

  response.jobTags =
    Array.isArray(response.jobTags)
      ? response.jobTags
      : [];

  return response;
}

async function requestDomDiagnostic(
  tabId: number,
): Promise<DomDiagnostic> {
  const response: unknown =
    await browser.tabs.sendMessage(
      tabId,
      {
        type: 'GET_DOM_DIAGNOSTIC',
      },
    );

  if (!isDomDiagnostic(response)) {
    throw new Error(
      'DOM 诊断数据格式不正确',
    );
  }

  return response;
}

async function loadStoredJobs(): Promise<StoredJob[]> {
  const result =
    await browser.storage.local.get(STORAGE_KEY);

  const rawJobs = result[STORAGE_KEY];

  if (!Array.isArray(rawJobs)) {
    return [];
  }

  return rawJobs.filter((value: unknown) => {
    if (!isStoredJob(value)) {
      return false;
    }

    value.jobTags =
      Array.isArray(value.jobTags)
        ? value.jobTags
        : [];

    return true;
  });
}

async function saveStoredJobs(
  jobs: StoredJob[],
): Promise<void> {
  await browser.storage.local.set({
    [STORAGE_KEY]: jobs,
  });
}

async function loadApiSettings(): Promise<void> {
  const result =
    await browser.storage.local.get([
      API_TOKEN_KEY,
      AUTO_ANALYZE_KEY,
    ]);

  const savedToken = result[API_TOKEN_KEY];
  apiToken =
    typeof savedToken === 'string'
      ? savedToken.trim()
      : '';

  const savedAutoAnalyze =
    result[AUTO_ANALYZE_KEY];

  autoAnalyzeCheckbox.checked =
    typeof savedAutoAnalyze === 'boolean'
      ? savedAutoAnalyze
      : true;

  apiTokenInput.value = apiToken;
}

async function saveApiToken(
  token: string,
): Promise<void> {
  apiToken = token.trim();

  if (apiToken) {
    await browser.storage.local.set({
      [API_TOKEN_KEY]: apiToken,
    });
  } else {
    await browser.storage.local.remove(
      API_TOKEN_KEY,
    );
  }
}

async function saveAutoAnalyzeSetting(): Promise<void> {
  await browser.storage.local.set({
    [AUTO_ANALYZE_KEY]:
      autoAnalyzeCheckbox.checked,
  });
}

function getJobIdentity(
  job: JobCoreData,
): string {
  if (job.jobId) {
    return `id:${job.jobId}`;
  }

  return `url:${job.sourceUrl}`;
}

function formatLocalTime(
  isoString: string,
): string {
  const date = new Date(isoString);

  if (Number.isNaN(date.getTime())) {
    return isoString;
  }

  return new Intl.DateTimeFormat(
    'zh-CN',
    {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(date);
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderStoredJobs(): void {
  savedCountElement.textContent =
    String(storedJobs.length);

  storageStatusElement.textContent =
    storedJobs.length > 0
      ? '浏览器备份正常'
      : '等待采集';

  exportJsonlButton.disabled =
    storedJobs.length === 0;
  exportCsvButton.disabled =
    storedJobs.length === 0;
  clearButton.disabled =
    storedJobs.length === 0;
  syncAllButton.disabled =
    storedJobs.length === 0 ||
    !apiConnected;

  const recentJobs = storedJobs
    .slice()
    .sort(
      (left, right) =>
        new Date(right.savedAt).getTime() -
        new Date(left.savedAt).getTime(),
    )
    .slice(0, 5);

  if (recentJobs.length === 0) {
    recentJobsElement.innerHTML =
      '<p class="empty-state">暂无采集记录</p>';
    return;
  }

  recentJobsElement.innerHTML =
    recentJobs
      .map((job) => {
        const title =
          escapeHtml(
            job.jobTitle || '未命名岗位',
          );

        const company =
          job.companyFullName ||
          job.companyShortName;

        const meta =
          [
            company,
            job.city,
            job.salary,
          ]
            .filter(Boolean)
            .map((value) =>
              escapeHtml(String(value)),
            )
            .join(' · ');

        return `
          <article class="recent-job">
            <div>
              <h3>${title}</h3>
              <p>${meta || '字段待补充'}</p>
            </div>
            <time>
              ${escapeHtml(formatLocalTime(job.savedAt))}
            </time>
          </article>
        `;
      })
      .join('');
}

function renderTags(tags: string[]): void {
  if (tags.length === 0) {
    tagsElement.innerHTML =
      '<span class="empty-inline">—</span>';
    return;
  }

  tagsElement.innerHTML = tags
    .slice(0, 12)
    .map(
      (tag) =>
        `<span class="tag">${escapeHtml(tag)}</span>`,
    )
    .join('');
}

function currentJobAlreadySaved(): boolean {
  if (!currentJob) {
    return false;
  }

  const identity = getJobIdentity(currentJob);
  return storedJobs.some(
    (storedJob) =>
      getJobIdentity(storedJob) === identity,
  );
}

function renderCollectButtonText(): void {
  if (!currentJob) {
    collectButton.textContent =
      '采集当前岗位';
    return;
  }

  const alreadySaved =
    currentJobAlreadySaved();

  if (apiConnected) {
    collectButton.textContent =
      alreadySaved
        ? '更新并同步岗位'
        : apiJobCount === 0
          ? '采集为第一个样本'
          : '采集并同步岗位';
    return;
  }

  collectButton.textContent =
    alreadySaved
      ? '更新本地岗位'
      : '仅保存到浏览器';
}

const USER_STATUS_LABELS: Record<UserStatus, string> = {
  to_review: '待判断',
  interested: '感兴趣',
  preparing: '准备投递',
  applied: '已投递',
  written_test: '笔试',
  interview: '面试',
  offer: 'Offer',
  rejected: '被拒',
  abandoned: '放弃',
};

function setQuickManagementBadge(
  text: string,
  tone:
    | 'idle'
    | 'ready'
    | 'saved'
    | 'warning'
    | 'error' = 'idle',
): void {
  quickManagementBadgeElement.className =
    `quick-management-badge quick-management-${tone}`;
  quickManagementBadgeElement.textContent = text;
}

function resetQuickManagement(
  message = '读取岗位后显示当前求职状态。',
): void {
  currentManagementJobId = null;
  currentManagementExists = false;
  quickUserStatusElement.value = 'to_review';
  quickNotesElement.value = '';
  quickUserStatusElement.disabled = true;
  quickNotesElement.disabled = true;
  saveQuickStatusButton.disabled = true;
  openManagementButton.disabled =
    !apiServiceOnline;
  quickManagementStatusElement.textContent =
    message;
  setQuickManagementBadge('等待岗位');
}

function prepareQuickManagementForJob(): void {
  currentManagementJobId = null;
  currentManagementExists = false;
  quickUserStatusElement.value = 'to_review';
  quickNotesElement.value = '';
  quickUserStatusElement.disabled = false;
  quickNotesElement.disabled = false;
  saveQuickStatusButton.disabled = true;
  openManagementButton.disabled =
    !apiServiceOnline;
  quickManagementStatusElement.textContent =
    apiConnected
      ? '正在读取 SQLite 中的求职状态。'
      : '可以先选择状态；连接本地 API 后，采集时会同步。';
  setQuickManagementBadge(
    apiConnected ? '读取中' : '待同步',
    apiConnected ? 'idle' : 'warning',
  );
}

function quickManagementPatch(): {
  user_status: UserStatus;
  notes: string;
} {
  return {
    user_status:
      quickUserStatusElement.value as UserStatus,
    notes: quickNotesElement.value.trim(),
  };
}

function isMissingManagedJobError(
  message: string,
): boolean {
  return (
    message.includes('岗位不存在') ||
    message.includes('404')
  );
}

async function loadCurrentManagement(): Promise<void> {
  if (!currentJob) {
    resetQuickManagement();
    return;
  }

  quickUserStatusElement.disabled = false;
  quickNotesElement.disabled = false;
  openManagementButton.disabled =
    !apiServiceOnline;

  if (!apiConnected) {
    currentManagementJobId = null;
    currentManagementExists = false;
    saveQuickStatusButton.disabled = true;
    quickManagementStatusElement.textContent =
      apiServiceOnline
        ? 'API 尚未完成令牌配对；采集前请先配对。'
        : '本地 API 未启动；当前状态会在服务恢复后随采集同步。';
    setQuickManagementBadge(
      apiServiceOnline ? '待配对' : '服务离线',
      'warning',
    );
    return;
  }

  if (!currentJob.jobId) {
    currentManagementJobId = null;
    currentManagementExists = false;
    saveQuickStatusButton.disabled = true;
    quickManagementStatusElement.textContent =
      '当前页面缺少稳定岗位 ID；采集成功后再保存状态。';
    setQuickManagementBadge('待采集', 'warning');
    return;
  }

  quickManagementStatusElement.textContent =
    '正在读取当前岗位的求职状态。';
  setQuickManagementBadge('读取中');

  try {
    const record =
      await apiRequest<ApiManagedJobResponse>(
        `/api/v1/jobs/${encodeURIComponent(currentJob.jobId)}`,
      );

    const management = record.management;

    currentManagementJobId = record.job_id;
    currentManagementExists = true;
    quickUserStatusElement.value =
      management.user_status;
    quickNotesElement.value =
      management.notes || '';
    saveQuickStatusButton.disabled = false;
    quickManagementStatusElement.textContent =
      `已载入：${USER_STATUS_LABELS[management.user_status]} · 最近更新 ${formatLocalTime(management.updated_at)}`;
    setQuickManagementBadge('已同步', 'saved');
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    currentManagementJobId = null;
    currentManagementExists = false;
    saveQuickStatusButton.disabled = true;

    if (isMissingManagedJobError(errorMessage)) {
      quickManagementStatusElement.textContent =
        '该岗位尚未进入 SQLite；点击采集时会连同状态和备注一起保存。';
      setQuickManagementBadge('待采集', 'ready');
      return;
    }

    quickManagementStatusElement.textContent =
      `求职状态读取失败：${errorMessage}`;
    setQuickManagementBadge('读取失败', 'error');
  }
}

async function saveQuickManagementForJob(
  jobId: string,
  silent = false,
): Promise<ApiManagementPatchResponse> {
  const response =
    await apiRequest<ApiManagementPatchResponse>(
      `/api/v1/jobs/${encodeURIComponent(jobId)}/management`,
      {
        method: 'PATCH',
        body: JSON.stringify(
          quickManagementPatch(),
        ),
      },
    );

  currentManagementJobId = response.job_id;
  currentManagementExists = true;
  quickUserStatusElement.value =
    response.management.user_status;
  quickNotesElement.value =
    response.management.notes || '';
  saveQuickStatusButton.disabled = false;
  quickManagementStatusElement.textContent =
    response.changed
      ? `已保存：${USER_STATUS_LABELS[response.management.user_status]} · ${formatLocalTime(response.management.updated_at)}`
      : `状态未变化：${USER_STATUS_LABELS[response.management.user_status]}`;
  setQuickManagementBadge('已同步', 'saved');

  if (!silent) {
    messageElement.textContent =
      response.changed
        ? `求职状态已保存：${USER_STATUS_LABELS[response.management.user_status]}。`
        : '求职状态和备注没有变化。';
  }

  return response;
}

async function saveQuickManagementOnly(): Promise<void> {
  if (!currentJob) {
    messageElement.textContent =
      '当前没有可管理的岗位。';
    return;
  }

  if (!apiConnected) {
    messageElement.textContent =
      '请先启动并配对本地 API。';
    return;
  }

  const jobId =
    currentManagementJobId ||
    currentJob.jobId;

  if (!jobId || !currentManagementExists) {
    messageElement.textContent =
      '该岗位尚未写入 SQLite，请先点击“采集并同步岗位”。';
    return;
  }

  saveQuickStatusButton.disabled = true;
  saveQuickStatusButton.textContent =
    '保存中……';

  try {
    await saveQuickManagementForJob(jobId);
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `求职状态保存失败：${errorMessage}`;
    quickManagementStatusElement.textContent =
      `保存失败：${errorMessage}`;
    setQuickManagementBadge('保存失败', 'error');
  } finally {
    saveQuickStatusButton.disabled =
      !currentManagementExists;
    saveQuickStatusButton.textContent =
      '保存求职状态';
  }
}

async function openManagementCenter(): Promise<void> {
  try {
    await browser.tabs.create({
      url: `${API_BASE}/manage`,
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `无法打开岗位管理中心：${errorMessage}`;
  }
}

function renderJob(
  job: JobCoreData,
): void {
  currentJob = job;
  prepareQuickManagementForJob();

  setText(jobTitleElement, job.jobTitle);
  setText(
    companyNameElement,
    job.companyFullName ||
      job.companyShortName,
  );

  companyMetaElement.textContent =
    [
      job.companyShortName &&
      job.companyShortName !==
        job.companyFullName
        ? job.companyShortName
        : null,
      job.financingStage,
      job.companySize,
      job.industry,
    ]
      .filter(Boolean)
      .join(' · ') || '—';

  setText(salaryElement, job.salary);
  setText(cityElement, job.city);
  setText(
    experienceElement,
    job.experience,
  );
  setText(daysElement, job.internshipDays);
  setText(
    durationElement,
    job.internshipDuration,
  );
  setText(
    educationElement,
    job.education,
  );
  renderTags(job.jobTags);

  if (job.jobDescription) {
    descriptionStatusElement.textContent =
      `已读取 ${job.jobDescription.length} 个字符`;

    const preview =
      job.jobDescription.length > 160
        ? `${job.jobDescription.slice(0, 160)}…`
        : job.jobDescription;

    descriptionPreviewElement.textContent =
      preview;
  } else {
    descriptionStatusElement.textContent =
      '未读取到职位描述';
    descriptionPreviewElement.textContent =
      '';
  }

  collectButton.disabled = false;
  renderCollectButtonText();

  const missingFields = [
    ['岗位名称', job.jobTitle],
    ['薪资', job.salary],
    ['城市', job.city],
    ['学历', job.education],
    [
      '公司名称',
      job.companyFullName ||
        job.companyShortName,
    ],
    ['职位描述', job.jobDescription],
  ]
    .filter(([, value]) => !value)
    .map(([label]) => label);

  if (missingFields.length === 0) {
    messageElement.textContent =
      apiConnected
        ? '字段完整；点击后将保存并同步到 SQLite。'
        : '字段完整；本地 API 未连接，将只保存浏览器备份。';
  } else {
    messageElement.textContent =
      `可以采集；待核对字段：${missingFields.join('、')}。`;
  }
}

function resetJobView(): void {
  currentJob = null;
  resetQuickManagement();
  collectButton.disabled = true;
  collectButton.textContent =
    '采集当前岗位';

  jobTitleElement.textContent =
    '正在读取……';

  for (const element of [
    companyNameElement,
    companyMetaElement,
    salaryElement,
    cityElement,
    experienceElement,
    daysElement,
    durationElement,
    educationElement,
  ]) {
    element.textContent = '—';
  }

  renderTags([]);
  descriptionStatusElement.textContent =
    '正在读取……';
  descriptionPreviewElement.textContent =
    '';
}

function pipelineStatusLabel(
  run: PipelineRun | null,
): string {
  if (!run || !run.status) {
    return '分析状态：尚无任务';
  }

  const completed =
    typeof run.completed_steps === 'number'
      ? run.completed_steps
      : 0;
  const step = run.current_step || '';

  if (
    run.status === 'queued' ||
    run.status === 'running'
  ) {
    return `分析状态：运行中 ${completed}/4${step ? ` · ${step}` : ''}`;
  }

  if (run.status === 'success') {
    return '分析状态：最近一次任务已完成';
  }

  if (run.status === 'failed') {
    return `分析状态：失败${run.error_message ? ` · ${run.error_message}` : ''}`;
  }

  if (run.status === 'interrupted') {
    return '分析状态：上次任务被中断';
  }

  return `分析状态：${run.status}`;
}

function renderApiHealth(
  health: ApiHealthResponse,
  authenticated: boolean,
): void {
  apiServiceOnline = true;
  apiConnected = authenticated;
  apiJobCount = health.job_count;

  if (authenticated) {
    setApiBadge('online', '已连接');
    apiSummaryElement.textContent =
      `服务在线 · SQLite ${health.job_count} 条岗位`;
  } else {
    setApiBadge('unpaired', '待配对');
    apiSummaryElement.textContent =
      `服务在线 · SQLite ${health.job_count} 条岗位 · 请粘贴令牌`;
  }

  pipelineStatusElement.textContent =
    pipelineStatusLabel(
      health.latest_pipeline,
    );

  syncAllButton.disabled =
    storedJobs.length === 0 ||
    !apiConnected;
  openDashboardButton.disabled =
    !health.dashboard_exists;
  renderCollectButtonText();
  if (!authenticated) {
    profileOnboarding = null;
    renderProfileOnboarding();
  }
}

function renderApiOffline(message: string): void {
  apiServiceOnline = false;
  apiConnected = false;
  apiJobCount = null;
  setApiBadge('offline', '服务离线');
  apiSummaryElement.textContent = message;
  pipelineStatusElement.textContent =
    '分析状态：请先启动 run_local_api.ps1';
  syncAllButton.disabled = true;
  openDashboardButton.disabled = true;
  profileOnboarding = null;
  renderProfileOnboarding();
  renderCollectButtonText();
}

function renderApiAuthError(message: string): void {
  apiServiceOnline = true;
  apiConnected = false;
  setApiBadge('error', '令牌错误');
  apiSummaryElement.textContent = message;
  syncAllButton.disabled = true;
  profileOnboarding = null;
  renderProfileOnboarding();
  renderCollectButtonText();
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = API_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(
    () => controller.abort(),
    timeoutMs,
  );

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timer);
  }
}

async function readErrorDetail(
  response: Response,
): Promise<string> {
  try {
    const body =
      await response.json() as unknown;

    if (
      typeof body === 'object' &&
      body !== null &&
      'detail' in body
    ) {
      const detail =
        (body as { detail: unknown }).detail;

      return typeof detail === 'string'
        ? detail
        : JSON.stringify(detail);
    }
  } catch {
    // Ignore invalid JSON error responses.
  }

  return `${response.status} ${response.statusText}`;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  requireToken = true,
): Promise<T> {
  if (requireToken && !apiToken) {
    throw new Error(
      '尚未保存本地 API 令牌。',
    );
  }

  const headers = new Headers(options.headers);

  if (options.body && !headers.has('Content-Type')) {
    headers.set(
      'Content-Type',
      'application/json',
    );
  }

  if (requireToken) {
    headers.set(
      'X-Job-Market-Token',
      apiToken,
    );
  }

  const response = await fetchWithTimeout(
    `${API_BASE}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail);
  }

  return await response.json() as T;
}

function renderProfileOnboarding(): void {
  if (!profileOnboarding || !apiConnected) {
    coldStartPanel.classList.add('is-hidden');
    return;
  }

  coldStartPanel.classList.remove('is-hidden');
  coldStartPanel.classList.toggle(
    'is-warning',
    profileOnboarding.job_count < 3,
  );
  coldStartTitleElement.textContent =
    profileOnboarding.job_count === 0
      ? '用当前岗位启动你的第一个样本'
      : profileOnboarding.maturity.label;
  coldStartBadgeElement.textContent =
    profileOnboarding.maturity.confidence;
  coldStartMessageElement.textContent =
    profileOnboarding.job_count === 0 && currentJob
      ? '当前岗位可以直接采集为第一个样本；随后打开个人档案，只需确认五项核心信息。'
      : profileOnboarding.maturity.message;
  coldStartProgressElement.style.width =
    `${profileOnboarding.maturity.progress}%`;
  openProfileButton.textContent =
    profileOnboarding.profile_initialized
      ? '查看个人档案'
      : '完成60秒设置';
  renderCollectButtonText();
}

async function refreshProfileOnboarding(): Promise<void> {
  if (!apiConnected) {
    profileOnboarding = null;
    renderProfileOnboarding();
    return;
  }

  try {
    profileOnboarding =
      await apiRequest<ProfileOnboardingStatus>(
        '/api/v1/profile/onboarding',
      );
  } catch {
    profileOnboarding = null;
  }

  renderProfileOnboarding();
}

async function checkApiConnection(): Promise<void> {
  setApiBadge('checking', '检查中');
  apiSummaryElement.textContent =
    '正在检查本地 FastAPI。';

  try {
    const health =
      await apiRequest<ApiHealthResponse>(
        '/api/v1/health',
        {},
        false,
      );

    if (!apiToken) {
      renderApiHealth(health, false);
      return;
    }

    try {
      await apiRequest<ApiRuntimeResponse>(
        '/api/v1/runtime',
      );
      renderApiHealth(health, true);
      await refreshProfileOnboarding();
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : String(error);
      renderApiAuthError(
        `服务在线，但鉴权失败：${errorMessage}`,
      );
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    renderApiOffline(
      `无法连接 ${API_BASE}：${errorMessage}`,
    );
  }
}

async function refreshPipelineStatus(): Promise<PipelineRun | null> {
  const response =
    await apiRequest<ApiPipelineStatusResponse>(
      '/api/v1/pipeline/status',
    );

  pipelineStatusElement.textContent =
    pipelineStatusLabel(response.run);
  openDashboardButton.disabled =
    !response.dashboard_exists;

  return response.run;
}

async function pollPipelineUntilSettled(): Promise<void> {
  const generation = ++pipelinePollGeneration;

  for (
    let attempt = 0;
    attempt < PIPELINE_POLL_LIMIT;
    attempt += 1
  ) {
    if (generation !== pipelinePollGeneration) {
      return;
    }

    try {
      const run = await refreshPipelineStatus();
      const status = run?.status;

      if (
        status === 'success' ||
        status === 'failed' ||
        status === 'interrupted'
      ) {
        await checkApiConnection();
        return;
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : String(error);

      pipelineStatusElement.textContent =
        `分析状态读取失败：${errorMessage}`;
      return;
    }

    await new Promise<void>((resolve) => {
      window.setTimeout(
        resolve,
        PIPELINE_POLL_INTERVAL_MS,
      );
    });
  }

  pipelineStatusElement.textContent =
    '分析仍在后台运行，可稍后重新打开插件查看。';
}

function describeUpsertAction(
  action: ApiUpsertResponse['action'],
): string {
  if (action === 'inserted') {
    return '新增';
  }

  if (action === 'updated') {
    return '更新';
  }

  return '未变化';
}

function handlePipelineSchedule(
  pipeline: PipelineSchedule | undefined,
): void {
  if (!pipeline) {
    return;
  }

  pipelineStatusElement.textContent =
    pipeline.started
      ? '分析状态：已启动，正在后台运行'
      : pipelineStatusLabel(pipeline.run);

  void pollPipelineUntilSettled();
}

async function triggerPipelineIfChanged(
  changedCount: number,
): Promise<void> {
  if (!autoAnalyzeCheckbox.checked) {
    return;
  }

  if (changedCount <= 0) {
    pipelineStatusElement.textContent =
      '分析状态：岗位未变化，无需重复运行';
    return;
  }

  const response =
    await apiRequest<ApiPipelineRunResponse>(
      '/api/v1/pipeline/run',
      {
        method: 'POST',
      },
    );

  handlePipelineSchedule(response);
}

async function readCurrentJob(): Promise<void> {
  refreshButton.disabled = true;
  diagnosticButton.disabled = true;
  refreshButton.textContent = '读取中……';

  resetJobView();
  setBadge('loading', '检查中');
  messageElement.textContent =
    '正在读取当前岗位。';

  try {
    storedJobs = await loadStoredJobs();
    renderStoredJobs();

    const currentTab =
      await getCurrentTab();

    const pageUrl =
      currentTab.url?.trim() || '';

    if (!isBossPage(pageUrl)) {
      jobTitleElement.textContent =
        '仅支持 BOSS 页面';
      setBadge('normal', '普通页面');
      messageElement.textContent =
        '请打开 BOSS 岗位详情页。';
      return;
    }

    if (
      typeof currentTab.id !== 'number'
    ) {
      throw new Error(
        '当前标签页缺少有效 ID',
      );
    }

    const job = await requestJobCore(
      currentTab.id,
    );

    setBadge('boss', 'BOSS 页面');
    renderJob(job);
    diagnosticButton.disabled = false;
    await loadCurrentManagement();
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    jobTitleElement.textContent =
      '读取失败';
    setBadge('error', '读取失败');
    messageElement.textContent =
      `错误：${errorMessage}`;
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent =
      '重新读取';
  }
}

async function collectCurrentJob(): Promise<void> {
  if (!currentJob) {
    messageElement.textContent =
      '当前没有可采集的岗位。';
    return;
  }

  collectButton.disabled = true;
  collectButton.textContent =
    apiConnected
      ? '正在保存并同步……'
      : '正在保存……';

  let localAction: 'inserted' | 'updated';

  try {
    storedJobs = await loadStoredJobs();

    const identity =
      getJobIdentity(currentJob);
    const existingIndex =
      storedJobs.findIndex(
        (storedJob) =>
          getJobIdentity(storedJob) ===
          identity,
      );

    const storedJob: StoredJob = {
      ...currentJob,
      savedAt: new Date().toISOString(),
    };

    if (existingIndex >= 0) {
      storedJobs[existingIndex] =
        storedJob;
      localAction = 'updated';
    } else {
      storedJobs.push(storedJob);
      localAction = 'inserted';
    }

    await saveStoredJobs(storedJobs);
    renderStoredJobs();

    if (!apiConnected) {
      const reason = apiServiceOnline
        ? '尚未通过令牌配对'
        : '本地 API 未启动';

      messageElement.textContent =
        `岗位已${localAction === 'inserted' ? '保存' : '更新'}浏览器备份；${reason}，暂未写入 SQLite。`;
      return;
    }

    try {
      const response =
        await apiRequest<ApiUpsertResponse>(
          '/api/v1/jobs/upsert',
          {
            method: 'POST',
            body: JSON.stringify(storedJob),
          },
        );

      apiJobCount = response.job_count;
      apiSummaryElement.textContent =
        `服务在线 · SQLite ${response.job_count} 条岗位`;

      let managementSuffix = '';

      try {
        const managementResponse =
          await saveQuickManagementForJob(
            response.job_id,
            true,
          );

        managementSuffix =
          `；求职状态${managementResponse.changed ? '已保存' : '未变化'}：${USER_STATUS_LABELS[managementResponse.management.user_status]}`;
      } catch (managementError) {
        const managementErrorMessage =
          managementError instanceof Error
            ? managementError.message
            : String(managementError);

        managementSuffix =
          `；但求职状态保存失败：${managementErrorMessage}`;
        quickManagementStatusElement.textContent =
          `保存失败：${managementErrorMessage}`;
        setQuickManagementBadge(
          '状态失败',
          'error',
        );
      }

      messageElement.textContent =
        `浏览器备份完成；SQLite ${describeUpsertAction(response.action)}成功，总计 ${response.job_count} 条${managementSuffix}。`;
      await refreshProfileOnboarding();
      await triggerPipelineIfChanged(
        response.action === 'unchanged' ? 0 : 1,
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : String(error);

      messageElement.textContent =
        `浏览器备份已完成，但 SQLite 同步失败：${errorMessage}`;
      await checkApiConnection();
    }

  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `保存失败：${errorMessage}`;
  } finally {
    collectButton.disabled =
      currentJob === null;
    renderCollectButtonText();
  }
}

async function syncAllStoredJobs(): Promise<void> {
  syncAllButton.disabled = true;
  syncAllButton.textContent =
    '同步中……';

  try {
    storedJobs = await loadStoredJobs();
    renderStoredJobs();

    if (storedJobs.length === 0) {
      messageElement.textContent =
        '浏览器本地没有可同步岗位。';
      return;
    }

    if (!apiConnected) {
      throw new Error(
        '本地 API 尚未完成令牌配对。',
      );
    }

    const response =
      await apiRequest<ApiBulkUpsertResponse>(
        '/api/v1/jobs/bulk-upsert',
        {
          method: 'POST',
          body: JSON.stringify({
            jobs: storedJobs,
          }),
        },
      );

    const results = response.results;
    apiJobCount = response.job_count;
    apiSummaryElement.textContent =
      `服务在线 · SQLite ${response.job_count} 条岗位`;
    messageElement.textContent =
      `批量同步完成：新增 ${results.inserted}、更新 ${results.updated}、未变化 ${results.unchanged}、失败 ${results.failed}。`;
    await triggerPipelineIfChanged(
      results.inserted + results.updated,
    );
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `批量同步失败：${errorMessage}`;
    await checkApiConnection();
  } finally {
    syncAllButton.textContent =
      '同步本地全部';
    syncAllButton.disabled =
      storedJobs.length === 0 ||
      !apiConnected;
  }
}

async function saveTokenAndTest(): Promise<void> {
  saveTokenButton.disabled = true;
  saveTokenButton.textContent =
    '测试中……';

  try {
    const token =
      apiTokenInput.value.trim();

    if (!token) {
      throw new Error(
        '请先粘贴 api_token.txt 的完整内容。',
      );
    }

    await saveApiToken(token);
    await checkApiConnection();

    if (apiConnected) {
      await loadCurrentManagement();
      messageElement.textContent =
        `本地 API 配对成功，SQLite 当前 ${apiJobCount ?? 0} 条岗位。`;
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `配对失败：${errorMessage}`;
  } finally {
    saveTokenButton.disabled = false;
    saveTokenButton.textContent =
      '保存并测试';
  }
}

async function clearApiToken(): Promise<void> {
  await saveApiToken('');
  apiTokenInput.value = '';
  apiConnected = false;
  await checkApiConnection();
  await loadCurrentManagement();
  messageElement.textContent =
    '本地 API 令牌已从浏览器存储中清除。';
}

async function openProfile(): Promise<void> {
  await browser.tabs.create({
    url: `${API_BASE}/profile`,
  });
}

async function openDashboard(): Promise<void> {
  try {
    const health =
      await apiRequest<ApiHealthResponse>(
        '/api/v1/health',
        {},
        false,
      );

    if (!health.dashboard_exists) {
      throw new Error(
        '看板尚未生成。',
      );
    }

    await browser.tabs.create({
      url: `${API_BASE}/dashboard`,
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `无法打开看板：${errorMessage}`;
    await checkApiConnection();
  }
}

function formatTimestampForFile(
  date: Date,
): string {
  const pad = (value: number): string =>
    String(value).padStart(2, '0');

  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    '-',
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join('');
}

function downloadText(
  content: string,
  fileName: string,
  mimeType: string,
): void {
  const blob = new Blob(
    [content],
    {
      type: `${mimeType};charset=utf-8`,
    },
  );

  const objectUrl =
    URL.createObjectURL(blob);
  const anchor =
    document.createElement('a');

  anchor.href = objectUrl;
  anchor.download = fileName;
  anchor.style.display = 'none';

  document.body.append(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => {
    URL.revokeObjectURL(objectUrl);
  }, 1000);
}

function downloadJson(
  value: unknown,
  fileName: string,
): void {
  downloadText(
    JSON.stringify(value, null, 2),
    fileName,
    'application/json',
  );
}

function escapeCsv(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  const text =
    typeof value === 'string'
      ? value
      : JSON.stringify(value);

  return `"${text.replaceAll('"', '""')}"`;
}

async function exportJsonl(): Promise<void> {
  storedJobs = await loadStoredJobs();

  if (storedJobs.length === 0) {
    messageElement.textContent =
      '当前没有可导出的岗位。';
    return;
  }

  const content =
    `${storedJobs.map((job) => JSON.stringify(job)).join('\n')}\n`;

  downloadText(
    content,
    `boss-jobs-${formatTimestampForFile(new Date())}.jsonl`,
    'application/x-ndjson',
  );

  messageElement.textContent =
    `已导出 ${storedJobs.length} 条 JSONL 备份。`;
}

async function exportCsv(): Promise<void> {
  storedJobs = await loadStoredJobs();

  if (storedJobs.length === 0) {
    messageElement.textContent =
      '当前没有可导出的岗位。';
    return;
  }

  const headers = [
    'jobId',
    'jobTitle',
    'salary',
    'city',
    'experience',
    'internshipDays',
    'internshipDuration',
    'education',
    'companyShortName',
    'companyFullName',
    'financingStage',
    'companySize',
    'industry',
    'jobTags',
    'jobDescription',
    'sourceUrl',
    'collectedAt',
    'savedAt',
  ] as const;

  const lines = [
    headers.map(escapeCsv).join(','),
    ...storedJobs.map(
      (job) =>
        headers
          .map((header) =>
            escapeCsv(job[header]),
          )
          .join(','),
    ),
  ];

  downloadText(
    `\uFEFF${lines.join('\r\n')}`,
    `boss-jobs-${formatTimestampForFile(new Date())}.csv`,
    'text/csv',
  );

  messageElement.textContent =
    `已导出 ${storedJobs.length} 条 CSV 备份。`;
}

async function clearStoredJobs(): Promise<void> {
  const confirmed =
    window.confirm(
      `确定清空浏览器保存的 ${storedJobs.length} 条岗位吗？SQLite 数据不会被删除。`,
    );

  if (!confirmed) {
    return;
  }

  await browser.storage.local.remove(
    STORAGE_KEY,
  );

  storedJobs = [];
  renderStoredJobs();

  if (currentJob) {
    renderJob(currentJob);
  }

  messageElement.textContent =
    '浏览器岗位备份已清空；SQLite 数据未受影响。';
}

async function exportDomDiagnostic(): Promise<void> {
  diagnosticButton.disabled = true;
  diagnosticButton.textContent =
    '正在生成……';

  try {
    const currentTab =
      await getCurrentTab();

    if (
      typeof currentTab.id !== 'number'
    ) {
      throw new Error(
        '当前标签页缺少有效 ID',
      );
    }

    const diagnostic =
      await requestDomDiagnostic(
        currentTab.id,
      );

    downloadJson(
      diagnostic,
      `boss-dom-diagnostic-${formatTimestampForFile(new Date())}.json`,
    );

    messageElement.textContent =
      'DOM 诊断文件已导出。';
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : String(error);

    messageElement.textContent =
      `诊断导出失败：${errorMessage}`;
  } finally {
    diagnosticButton.disabled = false;
    diagnosticButton.textContent =
      '导出 DOM 诊断';
  }
}

saveQuickStatusButton.addEventListener(
  'click',
  () => {
    void saveQuickManagementOnly();
  },
);

openManagementButton.addEventListener(
  'click',
  () => {
    void openManagementCenter();
  },
);

collectButton.addEventListener(
  'click',
  () => {
    void collectCurrentJob();
  },
);

refreshButton.addEventListener(
  'click',
  () => {
    void readCurrentJob();
  },
);

clearButton.addEventListener(
  'click',
  () => {
    void clearStoredJobs();
  },
);

exportJsonlButton.addEventListener(
  'click',
  () => {
    void exportJsonl();
  },
);

exportCsvButton.addEventListener(
  'click',
  () => {
    void exportCsv();
  },
);

diagnosticButton.addEventListener(
  'click',
  () => {
    void exportDomDiagnostic();
  },
);

saveTokenButton.addEventListener(
  'click',
  () => {
    void saveTokenAndTest();
  },
);

clearTokenButton.addEventListener(
  'click',
  () => {
    void clearApiToken();
  },
);

syncAllButton.addEventListener(
  'click',
  () => {
    void syncAllStoredJobs();
  },
);

openDashboardButton.addEventListener(
  'click',
  () => {
    void openDashboard();
  },
);

openProfileButton.addEventListener(
  'click',
  () => {
    void openProfile();
  },
);

autoAnalyzeCheckbox.addEventListener(
  'change',
  () => {
    void saveAutoAnalyzeSetting();
  },
);

async function initializePopup(): Promise<void> {
  await loadApiSettings();
  await Promise.all([
    readCurrentJob(),
    checkApiConnection(),
  ]);
  await loadCurrentManagement();
}

void initializePopup();

// PHASE_7B3_EXTENSION_QUICK_MANAGEMENT


// PHASE_81C_EXTENSION_COLD_START
