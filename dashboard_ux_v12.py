# DASHBOARD_AUTO_REFRESH_V1
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


START_MARKER = "<!-- JOB_MARKET_DASHBOARD_UX_START -->"
END_MARKER = "<!-- JOB_MARKET_DASHBOARD_UX_END -->"
DEFAULT_DASHBOARD = (
    Path(__file__).resolve().parent
    / "output"
    / "visualization_v1_1"
    / "visual_dashboard_v11.html"
)


CSS = r"""
<style id="job-market-dashboard-ux-styles">
:root {
    --ux-sidebar-width: 244px;
    --ux-livebar-height: 70px;
    --ux-primary: #0f766e;
    --ux-primary-dark: #075e57;
    --ux-primary-soft: #e6f5f2;
    --ux-border: #dce7e8;
    --ux-shadow: 0 10px 32px rgba(23, 52, 64, 0.10);
}

html {
    scroll-behavior: smooth;
    scroll-padding-top: 92px;
}

body.dashboard-ux-enabled {
    overflow-x: hidden;
}

#ux-reading-track {
    position: fixed;
    inset: 0 0 auto 0;
    z-index: 10000;
    height: 4px;
    background: rgba(15, 118, 110, 0.12);
    pointer-events: none;
}

#ux-reading-progress {
    width: 0;
    height: 100%;
    background: linear-gradient(90deg, #0f766e, #20b8aa);
    transition: width 80ms linear;
}

#ux-sidebar {
    position: fixed;
    z-index: 9000;
    left: 18px;
    top: 20px;
    bottom: 20px;
    width: var(--ux-sidebar-width);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--ux-border);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: var(--ux-shadow);
    backdrop-filter: blur(14px);
}

.ux-sidebar-head {
    padding: 20px 18px 15px;
    border-bottom: 1px solid var(--ux-border);
}

.ux-sidebar-kicker {
    margin: 0 0 4px;
    color: var(--ux-primary);
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.13em;
}

.ux-sidebar-title {
    margin: 0;
    color: #17262c;
    font-size: 18px;
    line-height: 1.35;
}

.ux-sidebar-summary {
    margin: 10px 0 0;
    color: #6d7f85;
    font-size: 11px;
    line-height: 1.6;
}

.ux-toc {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
}

.ux-toc-link {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 3px 0;
    padding: 10px 11px;
    border-radius: 10px;
    color: #52666d;
    text-decoration: none;
    font-size: 13px;
    font-weight: 650;
    transition: background 150ms ease, color 150ms ease, transform 150ms ease;
}

.ux-toc-link:hover {
    color: var(--ux-primary-dark);
    background: #f0f8f7;
    transform: translateX(2px);
}

.ux-toc-link.is-active {
    color: var(--ux-primary-dark);
    background: var(--ux-primary-soft);
}

.ux-toc-index {
    width: 24px;
    color: #8ba0a5;
    font-size: 10px;
    font-variant-numeric: tabular-nums;
}

.ux-toc-link.is-active .ux-toc-index {
    color: var(--ux-primary);
}

.ux-sidebar-footer {
    padding: 12px;
    border-top: 1px solid var(--ux-border);
}

.ux-sidebar-button {
    width: 100%;
    border: 1px solid #a8d7d1;
    border-radius: 10px;
    padding: 9px 11px;
    color: var(--ux-primary-dark);
    background: white;
    font: inherit;
    font-size: 12px;
    font-weight: 750;
    cursor: pointer;
}

body.dashboard-ux-enabled > .page {
    width: min(1460px, calc(100% - var(--ux-sidebar-width) - 86px));
    margin: 0 24px 0 calc(var(--ux-sidebar-width) + 54px);
    padding-top: 24px;
}

#ux-livebar {
    position: sticky;
    z-index: 8000;
    top: 12px;
    display: grid;
    grid-template-columns: minmax(0, 1.45fr) minmax(320px, 1fr);
    gap: 14px;
    align-items: center;
    min-height: var(--ux-livebar-height);
    margin: 0 0 22px;
    padding: 13px 16px;
    border: 1px solid rgba(207, 228, 225, 0.95);
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 7px 24px rgba(23, 52, 64, 0.09);
    backdrop-filter: blur(14px);
}

.ux-live-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 16px;
}

.ux-live-item {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    color: #53686f;
    font-size: 12px;
}

.ux-live-item strong {
    color: #17262c;
    font-size: 13px;
}

.ux-status-dot {
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: #a7b4b8;
    box-shadow: 0 0 0 4px rgba(167, 180, 184, 0.16);
}

.ux-status-dot.online,
.ux-status-dot.success {
    background: #15a394;
    box-shadow: 0 0 0 4px rgba(21, 163, 148, 0.14);
}

.ux-status-dot.running {
    background: #e2a400;
    box-shadow: 0 0 0 4px rgba(226, 164, 0, 0.15);
    animation: ux-pulse 1.2s ease-in-out infinite;
}

.ux-status-dot.failed,
.ux-status-dot.offline {
    background: #dc5c5c;
    box-shadow: 0 0 0 4px rgba(220, 92, 92, 0.15);
}

@keyframes ux-pulse {
    50% { opacity: 0.42; }
}

.ux-pipeline {
    min-width: 0;
}

.ux-pipeline-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 7px;
    color: #53686f;
    font-size: 11px;
}

.ux-pipeline-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.ux-pipeline-count {
    flex: none;
    color: #72858a;
    font-variant-numeric: tabular-nums;
}

.ux-pipeline-track {
    height: 8px;
    overflow: hidden;
    border-radius: 999px;
    background: #e8efef;
}

.ux-pipeline-fill {
    width: 0;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #0f766e, #2fb9aa);
    transition: width 320ms ease;
}

#ux-update-banner {
    display: none;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin: -10px 0 20px;
    padding: 12px 15px;
    border: 1px solid #e6cd75;
    border-radius: 12px;
    background: #fff7d9;
    color: #69510d;
    font-size: 12px;
    line-height: 1.55;
}

#ux-update-banner.is-visible {
    display: flex;
}

.ux-update-button {
    flex: none;
    border: 0;
    border-radius: 9px;
    padding: 8px 12px;
    color: white;
    background: #9c7400;
    font: inherit;
    font-size: 11px;
    font-weight: 750;
    cursor: pointer;
}

.analysis-sections {
    display: grid;
    gap: 22px;
    margin-top: 24px;
}

.analysis-section {
    scroll-margin-top: 98px;
    border: 1px solid var(--ux-border);
    border-radius: 17px;
    background: rgba(255, 255, 255, 0.72);
    box-shadow: 0 5px 18px rgba(23, 52, 64, 0.05);
}

.analysis-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    width: 100%;
    border: 0;
    border-radius: 17px 17px 0 0;
    padding: 20px 22px;
    color: inherit;
    background: transparent;
    text-align: left;
    font: inherit;
    cursor: pointer;
}

.analysis-section-header:hover {
    background: #f5faf9;
}

.analysis-section-title-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.analysis-section-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    color: var(--ux-primary-dark);
    background: var(--ux-primary-soft);
    font-size: 11px;
    font-weight: 850;
}

.analysis-section-title {
    margin: 0;
    font-size: 22px;
    line-height: 1.35;
}

.analysis-section-subtitle {
    margin: 4px 0 0;
    color: #6b7e84;
    font-size: 12px;
    line-height: 1.6;
}

.analysis-section-toggle {
    flex: none;
    color: #658087;
    font-size: 13px;
    transition: transform 180ms ease;
}

.analysis-section.is-collapsed .analysis-section-toggle {
    transform: rotate(-90deg);
}

.analysis-section-content {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 22px;
    overflow: hidden;
    padding: 0 22px 22px;
}

.analysis-section.is-collapsed .analysis-section-content {
    display: none;
}

.analysis-section .chart-panel,
.analysis-section .section-card {
    margin-top: 0;
}

.analysis-section .chart-panel.wide,
.analysis-section .section-card {
    grid-column: 1 / -1;
}

.analysis-section .chart-panel img {
    cursor: zoom-in;
    transition: transform 160ms ease, filter 160ms ease;
}

.analysis-section .chart-panel img:hover {
    transform: translateY(-2px);
    filter: drop-shadow(0 8px 14px rgba(23, 52, 64, 0.12));
}

#ux-back-top,
#ux-mobile-toc-button {
    position: fixed;
    z-index: 9100;
    right: 22px;
    width: 46px;
    height: 46px;
    border: 1px solid #b8dcd8;
    border-radius: 14px;
    color: var(--ux-primary-dark);
    background: rgba(255, 255, 255, 0.96);
    box-shadow: var(--ux-shadow);
    font: inherit;
    font-weight: 800;
    cursor: pointer;
    backdrop-filter: blur(12px);
}

#ux-back-top {
    bottom: 22px;
    opacity: 0;
    pointer-events: none;
    transform: translateY(8px);
    transition: opacity 160ms ease, transform 160ms ease;
}

#ux-back-top.is-visible {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
}

#ux-mobile-toc-button {
    display: none;
    bottom: 78px;
}

#ux-lightbox {
    position: fixed;
    z-index: 12000;
    inset: 0;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 38px;
    background: rgba(10, 24, 29, 0.90);
    backdrop-filter: blur(8px);
}

#ux-lightbox.is-open {
    display: flex;
}

.ux-lightbox-dialog {
    position: relative;
    width: min(1380px, 96vw);
    max-height: 92vh;
    overflow: auto;
    border-radius: 16px;
    background: white;
    box-shadow: 0 28px 90px rgba(0, 0, 0, 0.42);
}

.ux-lightbox-image {
    display: block;
    width: 100%;
    height: auto;
}

.ux-lightbox-caption {
    padding: 14px 18px 17px;
    color: #42575e;
    font-size: 13px;
}

.ux-lightbox-close {
    position: sticky;
    z-index: 2;
    top: 12px;
    float: right;
    width: 38px;
    height: 38px;
    margin: 12px 12px -50px 0;
    border: 0;
    border-radius: 999px;
    color: white;
    background: rgba(16, 38, 46, 0.82);
    font: inherit;
    font-size: 20px;
    cursor: pointer;
}

@media (max-width: 1180px) {
    #ux-sidebar {
        transform: translateX(calc(-100% - 30px));
        transition: transform 190ms ease;
    }

    #ux-sidebar.is-open {
        transform: translateX(0);
    }

    body.dashboard-ux-enabled > .page {
        width: min(1460px, calc(100% - 28px));
        margin: 0 auto;
    }

    #ux-mobile-toc-button {
        display: block;
    }
}

@media (max-width: 820px) {
    #ux-livebar {
        position: relative;
        top: auto;
        grid-template-columns: 1fr;
    }

    .analysis-section-content {
        grid-template-columns: 1fr;
        padding: 0 14px 14px;
    }

    .analysis-section .chart-panel,
    .analysis-section .chart-panel.wide,
    .analysis-section .section-card {
        grid-column: auto;
    }

    .analysis-section-header {
        padding: 16px;
    }

    .analysis-section-title {
        font-size: 19px;
    }

    #ux-update-banner {
        align-items: flex-start;
    }
}

@media (max-width: 560px) {
    #ux-sidebar {
        left: 10px;
        top: 10px;
        bottom: 10px;
        width: min(280px, calc(100vw - 20px));
    }

    #ux-livebar {
        padding: 12px;
    }

    .ux-live-meta {
        display: grid;
        grid-template-columns: 1fr 1fr;
    }

    #ux-lightbox {
        padding: 10px;
    }
}
</style>
"""


JS_TEMPLATE = r"""
<script id="job-market-dashboard-ux-script">
(() => {
    'use strict';

    const PAGE_CONFIG = __PAGE_CONFIG__;
    const TOTAL_PIPELINE_STEPS = 4;

    const sectionDefinitions = [
        {
            id: 'skills',
            index: '02',
            title: '技能需求',
            subtitle: '高频技能、要求性质与能力结构。',
            headings: [
                '核心样本最高频技能',
                '技能要求性质',
                '全样本与核心样本比较',
                '五类能力维度',
                '核心样本技能频率',
            ],
        },
        {
            id: 'roles',
            index: '03',
            title: '岗位方向',
            subtitle: '岗位类别、招聘类型和城市结构。',
            headings: [
                '岗位类别',
                '招聘类型',
                '城市分布',
            ],
        },
        {
            id: 'internship',
            index: '04',
            title: '实习约束',
            subtitle: '每周出勤、持续周期与时间要求。',
            headings: [
                '实习出勤要求',
                '实习周期',
            ],
        },
        {
            id: 'market',
            index: '05',
            title: '薪资与公司',
            subtitle: '公司规模、行业和薪资区间。',
            headings: [
                '公司规模',
                '行业分布',
                '实习日薪区间',
                '月薪岗位区间',
            ],
        },
        {
            id: 'details',
            index: '06',
            title: '岗位明细',
            subtitle: '筛选、核对并打开具体岗位。',
            headings: [
                '岗位明细筛选',
            ],
        },
    ];

    const tocDefinitions = [
        { id: 'overview', index: '01', title: '样本概览' },
        ...sectionDefinitions.map(({ id, index, title }) => ({
            id,
            index,
            title,
        })),
    ];

    const normalize = (value) =>
        String(value ?? '').replace(/\s+/g, ' ').trim();

    const formatTime = (value) => {
        if (!value) return '尚无记录';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return new Intl.DateTimeFormat('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        }).format(date);
    };

    const page = document.querySelector('.page');
    if (!page) return;

    document.body.classList.add('dashboard-ux-enabled');

    const h1 = page.querySelector('h1');
    if (h1) h1.textContent = '岗位市场分析看板 v1.2';
    document.title = '岗位市场分析看板 v1.2';

    const readingTrack = document.createElement('div');
    readingTrack.id = 'ux-reading-track';
    readingTrack.innerHTML = '<div id="ux-reading-progress"></div>';
    document.body.prepend(readingTrack);

    const overviewTarget = page.querySelector('header') ?? page;
    overviewTarget.id = 'overview';
    overviewTarget.style.scrollMarginTop = '98px';

    const sidebar = document.createElement('aside');
    sidebar.id = 'ux-sidebar';
    sidebar.setAttribute('aria-label', '看板目录');
    sidebar.innerHTML = `
        <div class="ux-sidebar-head">
            <p class="ux-sidebar-kicker">JOB MARKET REALITY CHECK</p>
            <h2 class="ux-sidebar-title">看板目录</h2>
            <p id="ux-sidebar-summary" class="ux-sidebar-summary">
                正在读取本地服务状态…
            </p>
        </div>
        <nav class="ux-toc">
            ${tocDefinitions.map((item) => `
                <a class="ux-toc-link" href="#${item.id}" data-target="${item.id}">
                    <span class="ux-toc-index">${item.index}</span>
                    <span>${item.title}</span>
                </a>
            `).join('')}
        </nav>
        <div class="ux-sidebar-footer">
            <button id="ux-sidebar-top" class="ux-sidebar-button" type="button">
                返回顶部
            </button>
        </div>
    `;
    document.body.append(sidebar);

    const livebar = document.createElement('section');
    livebar.id = 'ux-livebar';
    livebar.setAttribute('aria-label', '数据与分析状态');
    livebar.innerHTML = `
        <div class="ux-live-meta">
            <span class="ux-live-item">
                <span id="ux-service-dot" class="ux-status-dot"></span>
                <span>本地服务 <strong id="ux-service-text">检查中</strong></span>
            </span>
            <span class="ux-live-item">
                SQLite <strong id="ux-job-count">—</strong>
            </span>
            <span class="ux-live-item">
                核心样本 <strong id="ux-core-count">—</strong>
            </span>
            <span class="ux-live-item">
                页面生成 <strong>${formatTime(PAGE_CONFIG.generatedAt)}</strong>
            </span>
        </div>
        <div class="ux-pipeline">
            <div class="ux-pipeline-row">
                <span id="ux-pipeline-label" class="ux-pipeline-label">等待分析状态</span>
                <span id="ux-pipeline-count" class="ux-pipeline-count">0/${TOTAL_PIPELINE_STEPS}</span>
            </div>
            <div class="ux-pipeline-track">
                <div id="ux-pipeline-fill" class="ux-pipeline-fill"></div>
            </div>
        </div>
    `;

    const updateBanner = document.createElement('div');
    updateBanner.id = 'ux-update-banner';
    updateBanner.innerHTML = `
        <span id="ux-update-message">发现新的分析结果。</span>
        <button id="ux-refresh-result" class="ux-update-button" type="button">
            立即刷新
        </button>
    `;

    page.prepend(updateBanner);
    page.prepend(livebar);

    const allMovable = [
        ...Array.from(page.querySelectorAll('main.chart-grid > .chart-panel')),
        ...Array.from(page.children).filter((element) =>
            element.classList?.contains('section-card'),
        ),
    ];

    const headingFor = (element) =>
        normalize(element.querySelector('h2')?.textContent);

    const sectionContainer = document.createElement('main');
    sectionContainer.className = 'analysis-sections';

    for (const definition of sectionDefinitions) {
        const section = document.createElement('section');
        section.id = definition.id;
        section.className = 'analysis-section';
        section.dataset.sectionId = definition.id;

        const button = document.createElement('button');
        button.className = 'analysis-section-header';
        button.type = 'button';
        button.setAttribute('aria-expanded', 'true');
        button.innerHTML = `
            <span class="analysis-section-title-row">
                <span class="analysis-section-index">${definition.index}</span>
                <span>
                    <h2 class="analysis-section-title">${definition.title}</h2>
                    <p class="analysis-section-subtitle">${definition.subtitle}</p>
                </span>
            </span>
            <span class="analysis-section-toggle" aria-hidden="true">▼</span>
        `;

        const content = document.createElement('div');
        content.className = 'analysis-section-content';

        for (const element of allMovable) {
            if (definition.headings.includes(headingFor(element))) {
                content.append(element);
            }
        }

        button.addEventListener('click', () => {
            const collapsed = section.classList.toggle('is-collapsed');
            button.setAttribute('aria-expanded', String(!collapsed));
            sessionStorage.setItem(
                `job-dashboard-collapse:${definition.id}`,
                collapsed ? '1' : '0',
            );
        });

        if (
            sessionStorage.getItem(
                `job-dashboard-collapse:${definition.id}`,
            ) === '1'
        ) {
            section.classList.add('is-collapsed');
            button.setAttribute('aria-expanded', 'false');
        }

        section.append(button, content);
        sectionContainer.append(section);
    }

    const oldGrid = page.querySelector('main.chart-grid');
    if (oldGrid) oldGrid.replaceWith(sectionContainer);
    else page.append(sectionContainer);

    for (const orphan of allMovable) {
        if (!orphan.isConnected) continue;
        if (orphan.closest('.analysis-section')) continue;
        sectionContainer.append(orphan);
    }

    const metricValues = Array.from(
        page.querySelectorAll('.metric-card'),
    ).reduce((result, card) => {
        const label = normalize(card.querySelector('.metric-label')?.textContent);
        const value = normalize(card.querySelector('.metric-value')?.textContent);
        result[label] = value;
        return result;
    }, {});

    const coreCount = metricValues['核心岗位样本'] ?? '—';
    document.getElementById('ux-core-count').textContent = coreCount;

    const sidebarSummary = document.getElementById('ux-sidebar-summary');
    sidebarSummary.textContent = `核心样本 ${coreCount} · 自动同步看板`;

    const backTop = document.createElement('button');
    backTop.id = 'ux-back-top';
    backTop.type = 'button';
    backTop.title = '返回顶部';
    backTop.textContent = '↑';
    document.body.append(backTop);

    const mobileTocButton = document.createElement('button');
    mobileTocButton.id = 'ux-mobile-toc-button';
    mobileTocButton.type = 'button';
    mobileTocButton.title = '打开目录';
    mobileTocButton.textContent = '目';
    document.body.append(mobileTocButton);

    const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    backTop.addEventListener('click', scrollToTop);
    document.getElementById('ux-sidebar-top').addEventListener('click', scrollToTop);

    mobileTocButton.addEventListener('click', () => {
        sidebar.classList.toggle('is-open');
    });

    sidebar.addEventListener('click', (event) => {
        const link = event.target.closest('.ux-toc-link');
        if (!link) return;
        if (window.innerWidth <= 1180) sidebar.classList.remove('is-open');
    });

    const readingProgress = document.getElementById('ux-reading-progress');
    const onScroll = () => {
        const max = Math.max(
            1,
            document.documentElement.scrollHeight - window.innerHeight,
        );
        const ratio = Math.min(1, Math.max(0, window.scrollY / max));
        readingProgress.style.width = `${ratio * 100}%`;
        backTop.classList.toggle('is-visible', window.scrollY > window.innerHeight * 0.75);
    };
    document.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();

    const tocLinks = Array.from(document.querySelectorAll('.ux-toc-link'));
    const targets = tocDefinitions
        .map(({ id }) => document.getElementById(id))
        .filter(Boolean);

    const setActiveTarget = (id) => {
        for (const link of tocLinks) {
            link.classList.toggle('is-active', link.dataset.target === id);
        }
    };

    const observer = new IntersectionObserver(
        (entries) => {
            const visible = entries
                .filter((entry) => entry.isIntersecting)
                .sort((left, right) => right.intersectionRatio - left.intersectionRatio);
            if (visible[0]) setActiveTarget(visible[0].target.id);
        },
        {
            rootMargin: '-18% 0px -68% 0px',
            threshold: [0, 0.08, 0.25, 0.5],
        },
    );
    targets.forEach((target) => observer.observe(target));
    setActiveTarget('overview');

    const lightbox = document.createElement('div');
    lightbox.id = 'ux-lightbox';
    lightbox.setAttribute('role', 'dialog');
    lightbox.setAttribute('aria-modal', 'true');
    lightbox.innerHTML = `
        <div class="ux-lightbox-dialog">
            <button class="ux-lightbox-close" type="button" aria-label="关闭">×</button>
            <img class="ux-lightbox-image" alt="图表放大预览">
            <div class="ux-lightbox-caption"></div>
        </div>
    `;
    document.body.append(lightbox);

    const closeLightbox = () => lightbox.classList.remove('is-open');
    lightbox.querySelector('.ux-lightbox-close').addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (event) => {
        if (event.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeLightbox();
    });

    for (const image of document.querySelectorAll('.chart-panel img')) {
        image.addEventListener('click', () => {
            const panel = image.closest('.chart-panel');
            const title = normalize(panel?.querySelector('h2')?.textContent) || '图表';
            lightbox.querySelector('.ux-lightbox-image').src = image.src;
            lightbox.querySelector('.ux-lightbox-caption').textContent = title;
            lightbox.classList.add('is-open');
        });
    }

    const serviceDot = document.getElementById('ux-service-dot');
    const serviceText = document.getElementById('ux-service-text');
    const jobCount = document.getElementById('ux-job-count');
    const pipelineLabel = document.getElementById('ux-pipeline-label');
    const pipelineCount = document.getElementById('ux-pipeline-count');
    const pipelineFill = document.getElementById('ux-pipeline-fill');
    const updateMessage = document.getElementById('ux-update-message');

    const setPipelineStatus = (latest) => {
        const status = latest?.status ?? 'idle';
        const completed = Math.max(
            0,
            Math.min(TOTAL_PIPELINE_STEPS, Number(latest?.completed_steps ?? 0)),
        );
        let percent = (completed / TOTAL_PIPELINE_STEPS) * 100;
        let label = '尚未运行分析';
        let dotClass = 'online';

        if (status === 'queued') {
            label = '分析任务排队中';
            percent = Math.max(percent, 4);
            dotClass = 'running';
        } else if (status === 'running') {
            label = normalize(latest?.current_step) || '分析运行中';
            percent = Math.max(percent, 8);
            dotClass = 'running';
        } else if (status === 'success') {
            label = `最近分析完成 · ${formatTime(latest?.finished_at)}`;
            percent = 100;
            dotClass = 'success';
        } else if (status === 'failed') {
            label = `分析失败 · ${normalize(latest?.error_message) || '请查看日志'}`;
            dotClass = 'failed';
        } else if (status === 'interrupted') {
            label = '上一次分析被中断';
            dotClass = 'failed';
        }

        pipelineLabel.textContent = label;
        pipelineCount.textContent = `${completed}/${TOTAL_PIPELINE_STEPS}`;
        pipelineFill.style.width = `${percent}%`;
        serviceDot.className = `ux-status-dot ${dotClass}`;
    };

    const pageRunId = Number(PAGE_CONFIG.pipelineRunId ?? 0);
    let autoRefreshScheduled = false;

    const shouldOfferRefresh = (latest) => {
        if (!latest || latest.status !== 'success') return false;
        const latestRunId = Number(latest.run_id ?? 0);
        if (pageRunId > 0) return latestRunId > pageRunId;
        const finished = new Date(latest.finished_at ?? 0).getTime();
        const generated = new Date(PAGE_CONFIG.generatedAt ?? 0).getTime();
        return Number.isFinite(finished) && finished > generated + 1500;
    };

    const pollHealth = async () => {
        if (!['http:', 'https:'].includes(window.location.protocol)) {
            serviceText.textContent = '请通过本地 API 打开';
            serviceDot.className = 'ux-status-dot offline';
            pipelineLabel.textContent = '文件模式不支持实时状态';
            return;
        }

        try {
            const response = await fetch('/api/v1/health', {
                cache: 'no-store',
                headers: { Accept: 'application/json' },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const health = await response.json();
            serviceText.textContent = '在线';
            serviceDot.className = 'ux-status-dot online';
            jobCount.textContent = `${health.job_count ?? '—'}条`;
            sidebarSummary.textContent = `SQLite ${health.job_count ?? '—'} · 核心 ${coreCount}`;
            setPipelineStatus(health.latest_pipeline);

            if (shouldOfferRefresh(health.latest_pipeline)) {
                const latestRunId = Number(health.latest_pipeline.run_id ?? 0);
                updateMessage.textContent = `第 ${latestRunId} 次分析已经完成，正在自动载入最新看板。`;
                updateBanner.classList.add('is-visible');
                if (!autoRefreshScheduled) {
                    autoRefreshScheduled = true;
                    sessionStorage.setItem('job-dashboard-restore-scroll', String(window.scrollY));
                    window.setTimeout(() => {
                        const url = new URL(window.location.href);
                        url.searchParams.set('_refresh', String(Date.now()));
                        window.location.replace(url.toString());
                    }, 700);
                }
            } else {
                updateBanner.classList.remove('is-visible');
            }
        } catch (error) {
            serviceText.textContent = '离线';
            serviceDot.className = 'ux-status-dot offline';
            pipelineLabel.textContent = `无法读取本地服务：${error instanceof Error ? error.message : String(error)}`;
        }
    };

    document.getElementById('ux-refresh-result').addEventListener('click', () => {
        sessionStorage.setItem('job-dashboard-restore-scroll', String(window.scrollY));
        const url = new URL(window.location.href);
        url.searchParams.set('_refresh', String(Date.now()));
        window.location.replace(url.toString());
    });

    const restoreScroll = Number(sessionStorage.getItem('job-dashboard-restore-scroll'));
    if (Number.isFinite(restoreScroll) && restoreScroll > 0) {
        sessionStorage.removeItem('job-dashboard-restore-scroll');
        window.setTimeout(() => window.scrollTo({ top: restoreScroll }), 120);
    }

    void pollHealth();
    window.setInterval(pollHealth, 2000);
})();
</script>
"""


def _latest_pipeline_run_id() -> int | None:
    try:
        from local_api.database import latest_pipeline_run

        latest = latest_pipeline_run()
        if latest is None:
            return None
        value = latest.get("run_id")
        return int(value) if value is not None else None
    except Exception:
        return None


def _remove_existing_block(html: str) -> str:
    pattern = re.compile(
        re.escape(START_MARKER)
        + r".*?"
        + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    return pattern.sub("", html)


def enhance_dashboard(path: Path = DEFAULT_DASHBOARD) -> dict[str, Any]:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dashboard not found: {path}")

    original = path.read_text(encoding="utf-8")
    cleaned = _remove_existing_block(original)

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    page_config = {
        "generatedAt": generated_at,
        "pipelineRunId": _latest_pipeline_run_id(),
        "dashboardVersion": "1.2",
    }
    script = JS_TEMPLATE.replace(
        "__PAGE_CONFIG__",
        json.dumps(page_config, ensure_ascii=False),
    )

    head_block = f"\n{START_MARKER}\n{CSS}\n{END_MARKER}\n"
    body_block = f"\n{START_MARKER}\n{script}\n{END_MARKER}\n"

    if "</head>" not in cleaned or "</body>" not in cleaned:
        raise ValueError("Dashboard HTML is missing </head> or </body>.")

    enhanced = cleaned.replace("</head>", head_block + "</head>", 1)
    enhanced = enhanced.replace("</body>", body_block + "</body>", 1)
    path.write_text(enhanced, encoding="utf-8")

    return {
        "dashboard_path": str(path),
        "generated_at": generated_at,
        "pipeline_run_id": page_config["pipelineRunId"],
        "size_bytes": path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhance the generated dashboard with navigation and live status.",
    )
    parser.add_argument(
        "--dashboard",
        type=Path,
        default=DEFAULT_DASHBOARD,
    )
    args = parser.parse_args()
    result = enhance_dashboard(args.dashboard)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
