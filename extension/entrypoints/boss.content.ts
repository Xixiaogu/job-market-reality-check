interface JobCoreData {
  schemaVersion: '1.2';
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
  extraction: {
    jobTitle: string;
    salary: string;
    basicInfo: string;
    companyName: string;
    companyInfo: string;
    jobTags: string;
    jobDescription: string;
  };
}

interface ElementDiagnostic {
  path: string;
  parentPath: string | null;
  tagName: string;
  id: string | null;
  classes: string[];
  textPreview: string;
  childElementCount: number;
  rect: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

interface AnchorDiagnostic {
  label: string;
  path: string;
  parentPath: string | null;
  tagName: string;
  classes: string[];
}

interface DomDiagnostic {
  schemaVersion: '1.2';
  collectedAt: string;
  page: {
    title: string;
    origin: string;
    pathname: string;
    viewportWidth: number;
    viewportHeight: number;
  };
  extractedCore: JobCoreData;
  candidateElements: ElementDiagnostic[];
  anchorElements: AnchorDiagnostic[];
  notes: string[];
}

interface GetCurrentJobCoreMessage {
  type: 'GET_CURRENT_JOB_CORE';
}

interface GetDomDiagnosticMessage {
  type: 'GET_DOM_DIAGNOSTIC';
}

type SupportedMessage =
  | GetCurrentJobCoreMessage
  | GetDomDiagnosticMessage;

const exactTitleSelectors = [
  '.job-primary.detail-box .info-primary .name > h1',
  '.job-banner .job-primary .info-primary .name > h1',
  '.rec-position .job-cotent h2 > p',
] as const;

const exactSalarySelectors = [
  '.job-primary.detail-box .info-primary .name > .salary',
  '.job-banner .job-primary .info-primary .name > .salary',
  '.rec-position .job-cotent > div',
] as const;

const primaryBannerSelectors = [
  '.job-primary.detail-box',
  '.job-banner .job-primary',
  '.rec-position .job-cotent',
] as const;

const descriptionSelectors = [
  '.job-detail-section .job-sec-text',
  '.job-detail-section [class*="job-sec-text"]',
  '.job-detail-section [class*="description-content"]',
  '.job-detail-section [class*="job-description"]',
  '.rec-position .rec-detail .detail-text',
] as const;

const companyShortNameSelectors = [
  '.job-sider .sider-company .company-info h3 a',
  '.job-sider .sider-company .company-info h3',
  '.job-sider .sider-company .company-info a',
  '.job-sider .sider-company .company-info',
  '.job-sider .job-company .company-info h3 a',
  '.job-sider .job-company .company-info h3',
  '.job-company .company-info h3 a',
  '.job-company .company-info h3',
  '.job-company .company-name',
  '.company-info .company-name',
  '.rec-position .job-brandComInfo',
] as const;

const companyFullNameSelectors = [
  '.job-sider .sider-company .company-full-name',
  '.job-sider .job-company .company-full-name',
  '.job-company .company-full-name',
  '.brandComBaseInfo > span',
  '.rec-position .brandComBaseInfo > span',
] as const;

const businessInfoSelectors = [
  '.job-detail-company .business-info-box',
  '.job-detail-section.job-detail-company .business-info-box',
  '.job-detail-company [class*="business-info"]',
  '[class*="business-info-box"]',
] as const;

const companyInfoSelectors = [
  '.job-sider .sider-company',
  '.job-sider .job-company',
  '.job-sider .job-company ul',
  '.job-sider .job-company .company-info-list',
  '.job-company .company-info-list',
  '.job-company ul',
  '.brandComBaseInfo > p',
  '.rec-position .brandComBaseInfo > p',
] as const;

const jobTagSelectors = [
  '.job-detail-section .job-tags span',
  '.job-detail-section .tag-list span',
  '.job-detail-section .job-keyword-list span',
  '.job-detail-section [class*="job-tag"] span',
  '.job-detail-section [class*="tag-list"] span',
  '.job-banner .job-tags span',
  '.job-primary .tag-list span',
] as const;

const diagnosticSelectors = [
  '.job-banner',
  '.job-primary.detail-box',
  '.job-primary .info-primary',
  '.job-primary .name',
  '.job-primary .name > h1',
  '.job-primary .name > .salary',
  '.job-detail-section',
  '.detail-content-header',
  '.job-detail-section .job-sec-text',
  '.job-detail-section [class*="tag"]',
  '.job-sider',
  '.job-sider .sider-company',
  '.job-sider .sider-company .company-info',
  '.job-sider .job-company',
  '.job-company',
  '.business-info-box',
  '[class*="business-info"]',
  '.company-info',
  '.company-info-list',
  '.brandComBaseInfo',
  '.rec-position',
  '[class*="job-sec-text"]',
  '[class*="job-description"]',
  'h1',
  'h2',
  'h3',
] as const;

const anchorLabels = [
  '职位描述',
  '职位详情',
  '岗位职责',
  '任职要求',
  '职位要求',
  '工作地点',
  '所在公司',
  '公司介绍',
  '公司信息',
  '公司基本信息',
] as const;

const financingPattern =
  /^(未融资|不需要融资|融资未公开|种子轮|天使轮|Pre-A轮|A轮|A\+轮|Pre-B轮|B轮|B\+轮|C轮|C\+轮|D轮|D\+轮|D轮及以上|E轮|战略融资|股权融资|定向增发|已上市)$/i;

const companySizePattern =
  /^(\d+-\d+人|\d+人以上|\d+人以下|\d+人)$/;

function cleanInlineText(
  value: string | null | undefined,
): string {
  return (value ?? '')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanMultilineText(
  value: string | null | undefined,
): string {
  return (value ?? '')
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((line) => line.replace(/[ \t]+/g, ' ').trim())
    .filter(Boolean)
    .join('\n')
    .trim();
}

function redactText(
  value: string,
  maxLength = 220,
): string {
  const cleaned = cleanInlineText(value)
    .replace(
      /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,
      '[EMAIL]',
    )
    .replace(
      /(^|\D)1[3-9]\d{9}(\D|$)/g,
      '$1[PHONE]$2',
    )
    .replace(
      /https?:\/\/\S+/gi,
      '[URL]',
    );

  if (cleaned.length <= maxLength) {
    return cleaned;
  }

  return `${cleaned.slice(0, maxLength)}…`;
}

function isVisible(
  element: Element | null,
): element is HTMLElement {
  if (!(element instanceof HTMLElement)) {
    return false;
  }

  const style = window.getComputedStyle(element);
  const rect = element.getBoundingClientRect();

  return (
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    Number(style.opacity) !== 0 &&
    rect.width > 0 &&
    rect.height > 0
  );
}

function findVisibleElement(
  selectors: readonly string[],
): HTMLElement | null {
  for (const selector of selectors) {
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>(selector),
    );

    const visibleElement = elements.find(isVisible);

    if (visibleElement) {
      return visibleElement;
    }
  }

  return null;
}

function findVisibleText(
  selectors: readonly string[],
): string | null {
  const element = findVisibleElement(selectors);
  const text = cleanInlineText(element?.innerText);

  return text || null;
}

function findAllVisibleTexts(
  selectors: readonly string[],
): string[] {
  const values: string[] = [];

  for (const selector of selectors) {
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>(selector),
    ).filter(isVisible);

    for (const element of elements) {
      const text = cleanInlineText(element.innerText);

      if (text) {
        values.push(text);
      }
    }
  }

  return values;
}

function uniqueStrings(values: string[]): string[] {
  const result: string[] = [];
  const seen = new Set<string>();

  for (const value of values) {
    const cleaned = cleanInlineText(value);

    if (!cleaned || seen.has(cleaned)) {
      continue;
    }

    seen.add(cleaned);
    result.push(cleaned);
  }

  return result;
}

function splitInfoText(value: string): string[] {
  const multiline = cleanMultilineText(value);

  if (!multiline) {
    return [];
  }

  return uniqueStrings(
    multiline
      .split(/\n|[·•]/)
      .flatMap((part) => part.split(/\s{2,}/))
      .map(cleanInlineText)
      .filter(Boolean),
  );
}

function extractJobId(): string | null {
  const match = window.location.pathname.match(
    /\/job_detail\/([^/.]+)\.html$/i,
  );

  return match?.[1] ?? null;
}

function buildCanonicalUrl(): string {
  return `${window.location.origin}${window.location.pathname}`;
}

function extractFallbackTitle(): string | null {
  const pageTitleMatch = document.title.match(
    /[「【]([^」】]+?)(?:招聘)?[」】]/,
  );

  return cleanInlineText(pageTitleMatch?.[1]) || null;
}

function extractCompanyFromPageTitle(): string | null {
  const match = document.title.match(
    /[_｜|]\s*([^_｜|]+?)招聘(?:-|_)?BOSS直聘/i,
  );

  return cleanInlineText(match?.[1]) || null;
}

function extractSalaryFallback(
  bannerText: string,
): string | null {
  const patterns = [
    /\d+\s*-\s*\d+\s*元\s*\/\s*天/,
    /\d+\s*-\s*\d+\s*[Kk](?:·\d+薪)?/,
    /\d+\s*-\s*\d+\s*元\s*\/\s*时/,
  ];

  for (const pattern of patterns) {
    const match = bannerText.match(pattern);

    if (match) {
      return cleanInlineText(match[0]);
    }
  }

  return null;
}

function normalizeSalary(value: string | null): string | null {
  if (!value) {
    return null;
  }

  return value
    .replace(/\s+/g, '')
    .replace(/／/g, '/')
    .trim();
}

function extractBasicInfo(
  bannerText: string,
  salary: string | null,
): {
  city: string | null;
  experience: string | null;
  internshipDays: string | null;
  internshipDuration: string | null;
  education: string | null;
} {
  let tail = cleanInlineText(bannerText);

  if (salary) {
    const salaryIndex = tail.indexOf(salary);

    if (salaryIndex >= 0) {
      tail = tail.slice(salaryIndex + salary.length).trim();
    }
  }

  tail = tail
    .replace(
      /(感兴趣|立即沟通|完善在线简历|上传附件简历|招聘中)/g,
      ' ',
    )
    .replace(/\s+/g, ' ')
    .trim();

  const internshipDays =
    cleanInlineText(
      tail.match(/(?:每周)?\d+(?:-\d+)?\s*天\s*\/\s*周/)?.[0],
    ) || null;

  const internshipDuration =
    cleanInlineText(
      tail.match(/(?:至少)?\d+(?:-\d+)?\s*个?月(?:以上)?/)?.[0],
    ) || null;

  const education =
    tail.match(
      /(博士及以上|博士|硕士及以上|硕士|本科及以上|本科|大专及以上|大专|高中|中专\/中技|学历不限)/,
    )?.[1] ?? null;

  const experience =
    tail.match(
      /(经验不限|无需经验|在校\/应届|应届生|应届|1年以内|1-3年|3-5年|5-10年|10年以上)/,
    )?.[1] ?? null;

  const boundaries = [
    internshipDays,
    internshipDuration,
    education,
    experience,
  ]
    .filter((value): value is string => Boolean(value))
    .map((value) => tail.indexOf(value))
    .filter((index) => index >= 0);

  const cityArea =
    boundaries.length > 0
      ? tail.slice(0, Math.min(...boundaries))
      : tail;

  const cityToken = cleanInlineText(cityArea)
    .split(' ')
    .find((token) =>
      /^[\u4e00-\u9fa5·]{2,12}$/.test(token),
    );

  return {
    city: cityToken ?? null,
    experience,
    internshipDays,
    internshipDuration,
    education,
  };
}

function isNoiseDescriptionText(text: string): boolean {
  const normalized = cleanInlineText(text);

  if (!normalized) {
    return true;
  }

  const exactNoise = new Set([
    '微信扫码分享',
    '举报',
    '微信扫码分享 举报',
    '职位描述',
    '职位详情',
  ]);

  return exactNoise.has(normalized);
}

function extractDescriptionByExactSelector(): string | null {
  for (const selector of descriptionSelectors) {
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>(selector),
    ).filter(isVisible);

    const candidates = elements
      .map((element) => cleanMultilineText(element.innerText))
      .filter((text) => text.length >= 30)
      .sort((left, right) => right.length - left.length);

    if (candidates[0]) {
      return candidates[0]
        .replace(/(?:\n)?查看全部\s*$/u, '')
        .trim();
    }
  }

  return null;
}

function findDescriptionHeader(): HTMLElement | null {
  const headings = Array.from(
    document.querySelectorAll<HTMLElement>(
      'h2, h3, h4',
    ),
  ).filter(isVisible);

  return (
    headings.find((heading) => {
      const text = cleanInlineText(heading.innerText);

      return text === '职位描述' || text === '职位详情';
    }) ?? null
  );
}

function extractDescriptionByAnchor(): string | null {
  const heading = findDescriptionHeader();

  if (!heading) {
    return null;
  }

  const headerContainer =
    heading.closest<HTMLElement>('.detail-content-header') ??
    heading.closest<HTMLElement>('.text') ??
    heading.parentElement;

  if (!headerContainer) {
    return null;
  }

  const candidates: string[] = [];
  let current = headerContainer.nextElementSibling;

  while (current) {
    if (
      current.matches(
        '.job-boss-info, [class*="job-boss-info"], [class*="boss-info"]',
      )
    ) {
      break;
    }

    if (isVisible(current)) {
      const text = cleanMultilineText(current.innerText);

      if (
        text.length >= 30 &&
        !isNoiseDescriptionText(text)
      ) {
        candidates.push(
          text.replace(/(?:\n)?查看全部\s*$/u, '').trim(),
        );
      }
    }

    current = current.nextElementSibling;
  }

  candidates.sort(
    (left, right) => right.length - left.length,
  );

  return candidates[0] ?? null;
}

function isValidJobTag(value: string): boolean {
  const text = cleanInlineText(value);

  if (!text) {
    return false;
  }

  if (/^[\u4e00-\u9fa5]$/u.test(text)) {
    return false;
  }

  if (text.length > 36) {
    return false;
  }

  if (/\d+\s*-\s*\d+/.test(text)) {
    return false;
  }

  return true;
}

function extractJobTags(): {
  tags: string[];
  source: string;
} {
  const noise = new Set([
    '微信扫码分享',
    '举报',
    '职位描述',
    '职位详情',
    '感兴趣',
    '立即沟通',
    '完善在线简历',
    '上传附件简历',
  ]);

  const exactTags = uniqueStrings(
    findAllVisibleTexts(jobTagSelectors)
      .filter(isValidJobTag)
      .filter((text) => !noise.has(text)),
  );

  if (exactTags.length > 0) {
    return {
      tags: exactTags.slice(0, 20),
      source: 'exact-selector',
    };
  }

  const header = findDescriptionHeader();
  const section = header?.closest<HTMLElement>(
    '.job-detail-section',
  );

  if (!header || !section) {
    return {
      tags: [],
      source: 'missing',
    };
  }

  const headerTop = header.getBoundingClientRect().top;

  const fallbackTags = uniqueStrings(
    Array.from(
      section.querySelectorAll<HTMLElement>(
        'span, li, a, em',
      ),
    )
      .filter(isVisible)
      .filter(
        (element) =>
          element.getBoundingClientRect().top <
          headerTop + 4,
      )
      .map((element) =>
        cleanInlineText(element.innerText),
      )
      .filter(isValidJobTag)
      .filter((text) => !noise.has(text)),
  );

  return {
    tags: fallbackTags.slice(0, 20),
    source:
      fallbackTags.length > 0
        ? 'section-fallback'
        : 'missing',
  };
}

function findCompanyAnchorContainer(): HTMLElement | null {
  const elements = Array.from(
    document.querySelectorAll<HTMLElement>(
      'h2, h3, h4, div, p, span',
    ),
  ).filter(isVisible);

  const anchor = elements.find((element) => {
    const text = cleanInlineText(element.innerText);

    return (
      text === '所在公司' ||
      text === '公司介绍' ||
      text === '公司信息' ||
      text === '公司基本信息'
    );
  });

  if (!anchor) {
    return null;
  }

  return (
    anchor.closest<HTMLElement>('.sider-company') ??
    anchor.closest<HTMLElement>('.content') ??
    anchor.closest<HTMLElement>('.job-company') ??
    anchor.parentElement
  );
}

function findCompanyInfoByPattern(): string | null {
  const elements = Array.from(
    document.querySelectorAll<HTMLElement>(
      'div, ul, p',
    ),
  ).filter(isVisible);

  const candidates = elements
    .map((element) => ({
      text: cleanMultilineText(element.innerText),
      childCount: element.childElementCount,
    }))
    .filter(({ text }) =>
      /(\d+-\d+人|\d+人以上|\d+人以下|已上市|未融资|[A-E]\+?轮|天使轮)/i.test(
        text,
      ),
    )
    .filter(({ text }) => text.length <= 220)
    .sort((left, right) => {
      if (left.text.length !== right.text.length) {
        return right.text.length - left.text.length;
      }

      return right.childCount - left.childCount;
    });

  return candidates[0]?.text ?? null;
}

function getCompanyInfoParts(
  container: HTMLElement | null,
  fallbackText: string | null,
): string[] {
  const values: string[] = [];

  if (container) {
    values.push(...splitInfoText(container.innerText));

    const descendants = Array.from(
      container.querySelectorAll<HTMLElement>(
        'a, p, li, span, em, div',
      ),
    ).filter(isVisible);

    for (const element of descendants) {
      const text = cleanInlineText(element.innerText);

      if (text && text.length <= 80) {
        values.push(text);
      }
    }
  }

  if (fallbackText) {
    values.push(...splitInfoText(fallbackText));
  }

  return uniqueStrings(values);
}

function looksLikeLegalCompanyName(
  value: string,
): boolean {
  const text = cleanInlineText(value);

  if (
    text.length < 4 ||
    text.length > 100
  ) {
    return false;
  }

  if (
    /^(公司名称|企业名称|企业全称|公司基本信息|工商信息)$/u.test(
      text,
    )
  ) {
    return false;
  }

  return /(?:有限责任公司|股份有限公司|有限公司|集团有限公司|合伙企业|事务所|工作室|研究院|研究所|中心)$/u.test(
    text,
  );
}

function extractCompanyFullNameFromBusinessInfo():
  | string
  | null {
  const containers = businessInfoSelectors
    .flatMap((selector) =>
      Array.from(
        document.querySelectorAll<HTMLElement>(selector),
      ),
    )
    .filter(isVisible);

  const labels = new Set([
    '公司名称',
    '企业名称',
    '企业全称',
  ]);

  for (const container of containers) {
    const multiline = cleanMultilineText(
      container.innerText,
    );

    const lines = multiline
      .split('\n')
      .map(cleanInlineText)
      .filter(Boolean);

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];

      if (labels.has(line)) {
        const nextLine = lines[index + 1] ?? '';

        if (looksLikeLegalCompanyName(nextLine)) {
          return nextLine;
        }
      }

      const inlineMatch = line.match(
        /^(?:公司名称|企业名称|企业全称)\s*[:：]?\s*(.+)$/u,
      );

      const inlineCandidate = cleanInlineText(
        inlineMatch?.[1],
      );

      if (
        inlineCandidate &&
        looksLikeLegalCompanyName(inlineCandidate)
      ) {
        return inlineCandidate;
      }
    }

    const descendantTexts = uniqueStrings(
      Array.from(
        container.querySelectorAll<HTMLElement>(
          'span, p, li, div',
        ),
      )
        .filter(isVisible)
        .map((element) =>
          cleanInlineText(element.innerText),
        )
        .filter((text) => text.length <= 100),
    );

    const legalName = descendantTexts.find(
      looksLikeLegalCompanyName,
    );

    if (legalName) {
      return legalName;
    }

    const flattened = cleanInlineText(multiline);
    const flattenedMatch = flattened.match(
      /(?:公司名称|企业名称|企业全称)\s*[:：]?\s*(.+?)(?=\s+(?:法定代表人|注册资本|成立日期|企业类型|经营状态|注册地址|统一社会信用代码|核准日期|营业期限|登记机关|$))/u,
    );

    const flattenedCandidate = cleanInlineText(
      flattenedMatch?.[1],
    );

    if (
      flattenedCandidate &&
      looksLikeLegalCompanyName(flattenedCandidate)
    ) {
      return flattenedCandidate;
    }
  }

  return null;
}

function extractCompanyInfo(): {
  companyShortName: string | null;
  companyFullName: string | null;
  financingStage: string | null;
  companySize: string | null;
  industry: string | null;
  nameSource: string;
  infoSource: string;
} {
  const exactShortName =
    findVisibleText(companyShortNameSelectors);
  const titleShortName =
    exactShortName ? null : extractCompanyFromPageTitle();

  const exactFullName =
    findVisibleText(companyFullNameSelectors);
  const businessFullName =
    exactFullName
      ? null
      : extractCompanyFullNameFromBusinessInfo();

  let companyShortName =
    exactShortName ?? titleShortName;
  const companyFullName =
    exactFullName ?? businessFullName;

  if (!companyShortName && companyFullName) {
    companyShortName = companyFullName;
  }

  const exactInfoContainer =
    findVisibleElement(companyInfoSelectors);
  const exactInfoText = cleanMultilineText(
    exactInfoContainer?.innerText,
  );

  const anchorContainer =
    findCompanyAnchorContainer();
  const anchorText = cleanMultilineText(
    anchorContainer?.innerText,
  );

  const patternInfo =
    exactInfoText
      ? null
      : findCompanyInfoByPattern();

  const fallbackText =
    exactInfoText || patternInfo || anchorText || null;

  const parts = getCompanyInfoParts(
    exactInfoContainer ?? anchorContainer,
    fallbackText,
  )
    .filter(
      (part) =>
        ![
          '所在公司',
          '公司介绍',
          '公司信息',
          '公司基本信息',
          '查看全部职位',
        ].includes(part),
    )
    .filter(
      (part) =>
        part !== companyFullName &&
        part !== companyShortName,
    );

  const financingStage =
    parts.find((part) =>
      financingPattern.test(part),
    ) ??
    (
      cleanInlineText(
        fallbackText?.match(
          /(未融资|不需要融资|融资未公开|种子轮|天使轮|Pre-A轮|A轮|A\+轮|Pre-B轮|B轮|B\+轮|C轮|C\+轮|D轮|D\+轮|D轮及以上|E轮|战略融资|股权融资|定向增发|已上市)/i,
        )?.[1],
      ) ||
      null
    );

  const companySize =
    parts.find((part) =>
      companySizePattern.test(part),
    ) ??
    (
      cleanInlineText(
        fallbackText?.match(
          /(\d+-\d+人|\d+人以上|\d+人以下|\d+人)/,
        )?.[1],
      ) ||
      null
    );

  const sizeIndex = companySize
    ? parts.indexOf(companySize)
    : -1;

  const financingIndex = financingStage
    ? parts.indexOf(financingStage)
    : -1;

  const metadataStart = Math.max(
    sizeIndex,
    financingIndex,
  );

  const industryParts = parts.filter(
    (part, index) =>
      part !== financingStage &&
      part !== companySize &&
      part.length >= 2 &&
      part.length <= 40 &&
      !/查看|职位|招聘|工作地点|地址|立即沟通|公司基本信息|工商信息/.test(
        part,
      ) &&
      (
        metadataStart >= 0
          ? index > metadataStart
          : false
      ),
  );

  const industry =
    industryParts.length > 0
      ? industryParts[0]
      : null;

  return {
    companyShortName,
    companyFullName,
    financingStage,
    companySize,
    industry,
    nameSource: exactFullName
      ? 'exact-full-name'
      : businessFullName
        ? 'business-info'
        : exactShortName
          ? 'short-name-only'
          : titleShortName
            ? 'title-fallback'
            : 'missing',
    infoSource: exactInfoText
      ? 'sider-company'
      : patternInfo
        ? 'pattern-fallback'
        : anchorText
          ? 'anchor-fallback'
          : 'missing',
  };
}

function extractJobCore(): JobCoreData {
  const primaryBanner = findVisibleElement(
    primaryBannerSelectors,
  );

  const bannerText = cleanInlineText(
    primaryBanner?.innerText,
  );

  const exactTitle = findVisibleText(
    exactTitleSelectors,
  );
  const fallbackTitle = exactTitle
    ? null
    : extractFallbackTitle();

  const exactSalary = findVisibleText(
    exactSalarySelectors,
  );
  const fallbackSalary = exactSalary
    ? null
    : extractSalaryFallback(bannerText);

  const salary = normalizeSalary(
    exactSalary ?? fallbackSalary,
  );

  const basicInfo = extractBasicInfo(
    bannerText,
    salary,
  );

  const companyInfo = extractCompanyInfo();
  const jobTags = extractJobTags();

  const exactDescription =
    extractDescriptionByExactSelector();
  const anchorDescription = exactDescription
    ? null
    : extractDescriptionByAnchor();

  return {
    schemaVersion: '1.2',
    jobId: extractJobId(),
    jobTitle: exactTitle ?? fallbackTitle,
    salary,
    city: basicInfo.city,
    experience: basicInfo.experience,
    internshipDays: basicInfo.internshipDays,
    internshipDuration:
      basicInfo.internshipDuration,
    education: basicInfo.education,
    companyShortName:
      companyInfo.companyShortName,
    companyFullName:
      companyInfo.companyFullName,
    financingStage:
      companyInfo.financingStage,
    companySize: companyInfo.companySize,
    industry: companyInfo.industry,
    jobTags: jobTags.tags,
    jobDescription:
      exactDescription ?? anchorDescription,
    sourceUrl: buildCanonicalUrl(),
    collectedAt: new Date().toISOString(),
    extraction: {
      jobTitle: exactTitle
        ? 'exact-selector'
        : fallbackTitle
          ? 'fallback'
          : 'missing',
      salary: exactSalary
        ? 'exact-selector'
        : fallbackSalary
          ? 'fallback'
          : 'missing',
      basicInfo: bannerText
        ? 'banner-text'
        : 'missing',
      companyName: companyInfo.nameSource,
      companyInfo: companyInfo.infoSource,
      jobTags: jobTags.source,
      jobDescription: exactDescription
        ? 'exact-selector'
        : anchorDescription
          ? 'anchor-fallback'
          : 'missing',
    },
  };
}

function cssEscape(value: string): string {
  if (typeof CSS !== 'undefined' && CSS.escape) {
    return CSS.escape(value);
  }

  return value.replace(
    /[^a-zA-Z0-9_-]/g,
    '\\$&',
  );
}

function buildElementSegment(
  element: Element,
): string {
  const tagName = element.tagName.toLowerCase();

  if (element.id) {
    return `${tagName}#${cssEscape(element.id)}`;
  }

  const classNames = Array.from(element.classList)
    .filter(Boolean)
    .slice(0, 3)
    .map(
      (className) =>
        `.${cssEscape(className)}`,
    )
    .join('');

  const parent = element.parentElement;

  if (!parent) {
    return `${tagName}${classNames}`;
  }

  const sameTagSiblings = Array.from(
    parent.children,
  ).filter(
    (sibling) =>
      sibling.tagName === element.tagName,
  );

  if (sameTagSiblings.length <= 1) {
    return `${tagName}${classNames}`;
  }

  const index =
    sameTagSiblings.indexOf(element) + 1;

  return `${tagName}${classNames}:nth-of-type(${index})`;
}

function buildDomPath(
  element: Element | null,
  maxDepth = 8,
): string | null {
  if (!element) {
    return null;
  }

  const segments: string[] = [];
  let current: Element | null = element;

  while (
    current &&
    current !== document.documentElement &&
    segments.length < maxDepth
  ) {
    segments.unshift(
      buildElementSegment(current),
    );
    current = current.parentElement;
  }

  if (current === document.documentElement) {
    segments.unshift('html');
  }

  return segments.join(' > ');
}

function createElementDiagnostic(
  element: HTMLElement,
): ElementDiagnostic {
  const rect = element.getBoundingClientRect();

  return {
    path: buildDomPath(element) ?? '',
    parentPath: buildDomPath(
      element.parentElement,
    ),
    tagName: element.tagName.toLowerCase(),
    id: element.id || null,
    classes: Array.from(
      element.classList,
    ).slice(0, 12),
    textPreview: redactText(
      element.innerText,
      220,
    ),
    childElementCount:
      element.childElementCount,
    rect: {
      left: Math.round(rect.left),
      top: Math.round(rect.top),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
    },
  };
}

function collectCandidateElements(): ElementDiagnostic[] {
  const seen = new Set<HTMLElement>();
  const candidates: HTMLElement[] = [];

  for (const selector of diagnosticSelectors) {
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>(
        selector,
      ),
    );

    for (const element of elements) {
      if (seen.has(element) || !isVisible(element)) {
        continue;
      }

      const text = cleanInlineText(
        element.innerText,
      );
      const rect =
        element.getBoundingClientRect();

      if (
        !text ||
        text.length > 1200 ||
        rect.top < -200 ||
        rect.top > 3000
      ) {
        continue;
      }

      seen.add(element);
      candidates.push(element);
    }
  }

  return candidates
    .sort((left, right) => {
      const leftRect =
        left.getBoundingClientRect();
      const rightRect =
        right.getBoundingClientRect();

      if (leftRect.top !== rightRect.top) {
        return leftRect.top - rightRect.top;
      }

      return leftRect.left - rightRect.left;
    })
    .slice(0, 180)
    .map(createElementDiagnostic);
}

function collectAnchorElements(): AnchorDiagnostic[] {
  const allElements = Array.from(
    document.querySelectorAll<HTMLElement>(
      'h1, h2, h3, h4, div, span, p',
    ),
  );

  const results: AnchorDiagnostic[] = [];
  const seenPaths = new Set<string>();

  for (const label of anchorLabels) {
    for (const element of allElements) {
      if (!isVisible(element)) {
        continue;
      }

      const text = cleanInlineText(
        element.innerText,
      );

      if (text !== label) {
        continue;
      }

      const path = buildDomPath(element);

      if (!path || seenPaths.has(path)) {
        continue;
      }

      seenPaths.add(path);

      results.push({
        label,
        path,
        parentPath: buildDomPath(
          element.parentElement,
        ),
        tagName:
          element.tagName.toLowerCase(),
        classes: Array.from(
          element.classList,
        ).slice(0, 12),
      });
    }
  }

  return results;
}

function buildDomDiagnostic(): DomDiagnostic {
  return {
    schemaVersion: '1.2',
    collectedAt: new Date().toISOString(),
    page: {
      title: redactText(
        document.title,
        180,
      ),
      origin: window.location.origin,
      pathname: window.location.pathname,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
    },
    extractedCore: {
      ...extractJobCore(),
      jobDescription: null,
    },
    candidateElements:
      collectCandidateElements(),
    anchorElements: collectAnchorElements(),
    notes: [
      '未导出 Cookie、localStorage、sessionStorage 或请求头。',
      '页面 URL 已移除查询参数。',
      '节点文本仅保留短预览，并自动遮盖邮箱与手机号。',
      '诊断对象中的 jobDescription 固定为 null。',
    ],
  };
}

function parseMessage(
  message: unknown,
): SupportedMessage | null {
  if (
    typeof message !== 'object' ||
    message === null ||
    !('type' in message)
  ) {
    return null;
  }

  if (message.type === 'GET_CURRENT_JOB_CORE') {
    return {
      type: 'GET_CURRENT_JOB_CORE',
    };
  }

  if (message.type === 'GET_DOM_DIAGNOSTIC') {
    return {
      type: 'GET_DOM_DIAGNOSTIC',
    };
  }

  return null;
}

export default defineContentScript({
  matches: [
    '*://zhipin.com/*',
    '*://*.zhipin.com/*',
  ],

  main() {
    browser.runtime.onMessage.addListener(
      (message: unknown) => {
        const parsedMessage =
          parseMessage(message);

        if (!parsedMessage) {
          return undefined;
        }

        if (
          parsedMessage.type ===
          'GET_CURRENT_JOB_CORE'
        ) {
          return Promise.resolve(
            extractJobCore(),
          );
        }

        return Promise.resolve(
          buildDomDiagnostic(),
        );
      },
    );

    console.log(
      'Job Market Collector content script loaded.',
      {
        url: window.location.href,
      },
    );
  },
});

