from pipeline.dashboard_compat import enhance_management_link
from pipeline.dashboard_enhancer import enhance_dashboard

import base64
import html
import json
import re
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


INPUT_JSONL = Path(
    "output/analysis_v1_1/jobs_skill_audited.jsonl"
)

CORE_FREQUENCY_FILE = Path(
    "output/analysis_v1_1/skill_frequency_core.csv"
)

FULL_FREQUENCY_FILE = Path(
    "output/analysis_v1_1/skill_frequency_full.csv"
)

OUTPUT_DIR = Path("output/visualization_v1_1")
CHART_DIR = OUTPUT_DIR / "charts"

DASHBOARD_FILE = (
    OUTPUT_DIR / "visual_dashboard_v11.html"
)

SUMMARY_FILE = (
    OUTPUT_DIR / "visual_summary_v11.md"
)

DASHBOARD_DATA_FILE = (
    OUTPUT_DIR / "dashboard_jobs.csv"
)


PALETTE = [
    "#0F766E",
    "#2563EB",
    "#F59E0B",
    "#DC2626",
    "#7C3AED",
    "#0891B2",
    "#65A30D",
]


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "font.size": 12,
            "axes.labelsize": 13,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 11,
            "figure.dpi": 140,
            "savefig.dpi": 220,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def clean_text(value) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\xa0", " "),
    ).strip()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"找不到输入文件：{path.resolve()}"
        )

    records = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"第 {line_number} 行JSON错误："
                    f"{exc}"
                ) from exc

    if not records:
        raise RuntimeError("没有读取到岗位记录。")

    return records


def parse_salary(salary: str) -> dict:
    salary = clean_text(salary)

    result = {
        "salary_type": "其他",
        "salary_low": None,
        "salary_high": None,
        "salary_midpoint": None,
        "salary_unit": "",
    }

    daily_match = re.search(
        r"(\d+(?:\.\d+)?)\s*-\s*"
        r"(\d+(?:\.\d+)?)\s*元/天",
        salary,
    )

    if daily_match:
        low = float(daily_match.group(1))
        high = float(daily_match.group(2))

        result.update(
            {
                "salary_type": "日薪",
                "salary_low": low,
                "salary_high": high,
                "salary_midpoint": (
                    low + high
                ) / 2,
                "salary_unit": "元/天",
            }
        )

        return result

    monthly_match = re.search(
        r"(\d+(?:\.\d+)?)\s*-\s*"
        r"(\d+(?:\.\d+)?)\s*[kK]",
        salary,
    )

    if monthly_match:
        low = float(monthly_match.group(1))
        high = float(monthly_match.group(2))

        result.update(
            {
                "salary_type": "月薪",
                "salary_low": low,
                "salary_high": high,
                "salary_midpoint": (
                    low + high
                ) / 2,
                "salary_unit": "K/月",
            }
        )

    return result


def enrich_salary(records: list[dict]) -> None:
    for record in records:
        record.update(
            parse_salary(
                record.get("salary", "")
            )
        )


def wrap_label(
    value: str,
    width: int = 18,
) -> str:
    value = clean_text(value)

    return "\n".join(
        textwrap.wrap(
            value,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
        )
    )


def shorten_text(
    value: str,
    limit: int = 22,
) -> str:
    value = clean_text(value)

    if len(value) <= limit:
        return value

    return value[: limit - 1] + "…"


def style_axis(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

    axis.grid(
        axis="x",
        alpha=0.20,
        linestyle="--",
    )

    axis.set_axisbelow(True)


def save_figure(
    figure,
    filename: str,
) -> None:
    figure.savefig(
        CHART_DIR / filename,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)


def save_count_bar(
    counts: Counter,
    filename: str,
    total: int,
    max_items: int | None = None,
    label_width: int = 18,
) -> None:
    items = counts.most_common(max_items)

    if not items:
        return

    frame = pd.DataFrame(
        items,
        columns=["label", "count"],
    ).sort_values(
        "count",
        ascending=True,
    )

    height = max(
        4.8,
        len(frame) * 0.64 + 1.4,
    )

    figure, axis = plt.subplots(
        figsize=(10.8, height),
        constrained_layout=True,
    )

    bars = axis.barh(
        [
            wrap_label(value, label_width)
            for value in frame["label"]
        ],
        frame["count"],
        color=PALETTE[1],
        height=0.62,
    )

    axis.set_xlabel("岗位数")
    axis.set_ylabel("")
    style_axis(axis)

    maximum = max(frame["count"])

    axis.set_xlim(
        0,
        maximum * 1.32 + 0.3,
    )

    for bar, count in zip(
        bars,
        frame["count"],
    ):
        percentage = (
            count / total
            if total
            else 0
        )

        axis.text(
            bar.get_width() + 0.10,
            bar.get_y()
            + bar.get_height() / 2,
            f"{count}（{percentage:.1%}）",
            va="center",
            fontsize=11,
        )

    save_figure(
        figure,
        filename,
    )


def save_skill_frequency_chart(
    frequency: pd.DataFrame,
) -> None:
    frame = (
        frequency.head(20)
        .copy()
        .sort_values(
            "出现岗位数",
            ascending=True,
        )
    )

    figure, axis = plt.subplots(
        figsize=(13.5, 10),
        constrained_layout=True,
    )

    bars = axis.barh(
        frame["技能"],
        frame["出现岗位数"],
        color=PALETTE[1],
        height=0.64,
    )

    axis.set_xlabel("出现岗位数")
    axis.set_ylabel("")
    style_axis(axis)

    maximum = frame["出现岗位数"].max()

    axis.set_xlim(
        0,
        maximum * 1.27,
    )

    for bar, (_, row) in zip(
        bars,
        frame.iterrows(),
    ):
        axis.text(
            bar.get_width() + 0.10,
            bar.get_y()
            + bar.get_height() / 2,
            (
                f"{int(row['出现岗位数'])}"
                f"（{row['岗位覆盖率百分比']}）"
            ),
            va="center",
            fontsize=11,
        )

    save_figure(
        figure,
        "01_top_skills.png",
    )


def save_requirement_breakdown(
    frequency: pd.DataFrame,
) -> None:
    frame = (
        frequency.head(15)
        .copy()
        .sort_values(
            "出现岗位数",
            ascending=True,
        )
    )

    columns = [
        "必备岗位数",
        "优先岗位数",
        "职责岗位数",
        "普通或标题提及岗位数",
    ]

    labels = [
        "必备",
        "优先",
        "职责",
        "普通或标题提及",
    ]

    figure, axis = plt.subplots(
        figsize=(13.5, 9),
        constrained_layout=True,
    )

    left = np.zeros(len(frame))

    for index, column in enumerate(columns):
        values = frame[column].to_numpy()

        axis.barh(
            frame["技能"],
            values,
            left=left,
            label=labels[index],
            color=PALETTE[index],
            height=0.66,
        )

        left += values

    axis.set_xlabel("岗位数")
    axis.set_ylabel("")
    style_axis(axis)

    axis.legend(
        loc="lower right",
        frameon=False,
        ncol=2,
    )

    save_figure(
        figure,
        "02_skill_requirement_breakdown.png",
    )


def save_full_core_comparison(
    full_frequency: pd.DataFrame,
    core_frequency: pd.DataFrame,
    full_count: int,
    core_count: int,
) -> None:
    skills = (
        core_frequency.head(14)["技能"]
        .tolist()
    )

    full_map = dict(
        zip(
            full_frequency["技能"],
            full_frequency["出现岗位数"],
        )
    )

    core_map = dict(
        zip(
            core_frequency["技能"],
            core_frequency["出现岗位数"],
        )
    )

    frame = pd.DataFrame(
        {
            "技能": skills,
            "全样本": [
                full_map.get(skill, 0)
                for skill in skills
            ],
            "核心样本": [
                core_map.get(skill, 0)
                for skill in skills
            ],
        }
    ).sort_values(
        "核心样本",
        ascending=True,
    )

    y_position = np.arange(len(frame))
    bar_height = 0.34

    figure, axis = plt.subplots(
        figsize=(13.5, 8.5),
        constrained_layout=True,
    )

    axis.barh(
        y_position - bar_height / 2,
        frame["全样本"],
        height=bar_height,
        label=f"全样本（{full_count}条）",
        color=PALETTE[2],
    )

    axis.barh(
        y_position + bar_height / 2,
        frame["核心样本"],
        height=bar_height,
        label=f"核心样本（{core_count}条）",
        color=PALETTE[1],
    )

    axis.set_yticks(y_position)
    axis.set_yticklabels(frame["技能"])
    axis.set_xlabel("出现岗位数")
    axis.set_ylabel("")
    style_axis(axis)

    axis.legend(
        frameon=False,
        loc="lower right",
    )

    save_figure(
        figure,
        "03_full_core_comparison.png",
    )


def save_skill_group_chart(
    records: list[dict],
) -> None:
    counter = Counter()

    for record in records:
        groups = {
            detail.get("group", "")
            for detail in record.get(
                "skill_details_v11",
                [],
            )
            if detail.get("group")
        }

        counter.update(groups)

    save_count_bar(
        counter,
        "04_skill_groups.png",
        len(records),
        label_width=16,
    )


def save_salary_range_chart(
    records: list[dict],
    salary_type: str,
    filename: str,
    xlabel: str,
) -> None:
    rows = []

    for record in records:
        if (
            record.get("salary_type")
            != salary_type
        ):
            continue

        if (
            record.get("salary_low") is None
            or record.get("salary_high") is None
        ):
            continue

        rows.append(
            {
                "job_title": record.get(
                    "job_title",
                    "",
                ),
                "salary_low": record[
                    "salary_low"
                ],
                "salary_high": record[
                    "salary_high"
                ],
                "salary_midpoint": record[
                    "salary_midpoint"
                ],
            }
        )

    if not rows:
        return

    frame = pd.DataFrame(rows).sort_values(
        "salary_midpoint",
        ascending=True,
    )

    height = max(
        5.5,
        len(frame) * 0.65 + 1.8,
    )

    figure, axis = plt.subplots(
        figsize=(15, height),
        constrained_layout=True,
    )

    positions = np.arange(len(frame))

    axis.hlines(
        y=positions,
        xmin=frame["salary_low"],
        xmax=frame["salary_high"],
        color=PALETTE[1],
        linewidth=5,
        alpha=0.85,
    )

    axis.scatter(
        frame["salary_low"],
        positions,
        color=PALETTE[0],
        s=42,
        zorder=3,
    )

    axis.scatter(
        frame["salary_high"],
        positions,
        color=PALETTE[3],
        s=42,
        zorder=3,
    )

    axis.set_yticks(positions)

    axis.set_yticklabels(
        [
            shorten_text(value, 26)
            for value in frame["job_title"]
        ]
    )

    axis.set_xlabel(xlabel)
    axis.set_ylabel("")
    style_axis(axis)

    maximum = frame["salary_high"].max()

    axis.set_xlim(
        max(0, frame["salary_low"].min() * 0.87),
        maximum * 1.14,
    )

    for position, (_, row) in enumerate(
        frame.iterrows()
    ):
        axis.text(
            row["salary_high"],
            position,
            (
                f"  {row['salary_low']:g}"
                f"-{row['salary_high']:g}"
            ),
            va="center",
            fontsize=10,
        )

    save_figure(
        figure,
        filename,
    )


def median_or_none(values):
    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return None

    return float(
        pd.Series(values).median()
    )


def image_data_uri(path: Path) -> str:
    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("ascii")

    return (
        "data:image/png;base64,"
        + encoded
    )


def option_html(values: list[str]) -> str:
    return "".join(
        (
            f'<option value="{html.escape(value, quote=True)}">'
            f"{html.escape(value)}"
            "</option>"
        )
        for value in values
    )


def build_dashboard_dataframe(
    records: list[dict],
) -> pd.DataFrame:
    rows = []

    for record in records:
        skills = record.get(
            "skills_v11",
            [],
        )

        rows.append(
            {
                "岗位名称": clean_text(
                    record.get("job_title")
                ),
                "岗位类别": clean_text(
                    record.get(
                        "role_category_v11"
                    )
                )
                or "其他/综合",
                "公司": clean_text(
                    record.get(
                        "company_full_name"
                    )
                ),
                "城市": clean_text(
                    record.get("city")
                )
                or "未披露",
                "薪资": clean_text(
                    record.get("salary")
                ),
                "招聘类型": clean_text(
                    record.get(
                        "employment_type"
                    )
                )
                or "未分类",
                "学历": clean_text(
                    record.get("education")
                )
                or "未披露",
                "实习出勤": clean_text(
                    record.get(
                        "internship_days_per_week"
                    )
                )
                or "未披露",
                "实习周期": clean_text(
                    record.get(
                        "internship_duration"
                    )
                )
                or "未披露",
                "技能": "；".join(skills),
                "链接": clean_text(
                    record.get("source_url")
                ),
            }
        )

    return pd.DataFrame(rows)


def build_job_table_html(
    dataframe: pd.DataFrame,
) -> str:
    rows = []

    for _, record in dataframe.iterrows():
        search_text = " ".join(
            clean_text(value)
            for value in record.tolist()
        )

        url = clean_text(record["链接"])

        link_html = (
            (
                f'<a class="job-link" '
                f'href="{html.escape(url, quote=True)}" '
                f'target="_blank" '
                f'rel="noopener noreferrer">'
                "查看岗位"
                "</a>"
            )
            if url
            else "无"
        )

        skills = clean_text(record["技能"])

        skill_badges = "".join(
            (
                '<span class="skill-badge">'
                + html.escape(skill)
                + "</span>"
            )
            for skill in skills.split("；")[:8]
            if skill
        )

        rows.append(
            f"""
            <tr
                data-category="{html.escape(clean_text(record['岗位类别']), quote=True)}"
                data-employment="{html.escape(clean_text(record['招聘类型']), quote=True)}"
                data-city="{html.escape(clean_text(record['城市']), quote=True)}"
                data-search="{html.escape(search_text, quote=True)}"
            >
                <td class="job-title-cell">
                    {html.escape(clean_text(record['岗位名称']))}
                </td>
                <td>{html.escape(clean_text(record['岗位类别']))}</td>
                <td>{html.escape(clean_text(record['公司']))}</td>
                <td>{html.escape(clean_text(record['城市']))}</td>
                <td>{html.escape(clean_text(record['薪资']))}</td>
                <td>{html.escape(clean_text(record['招聘类型']))}</td>
                <td>{html.escape(clean_text(record['学历']))}</td>
                <td>
                    {html.escape(clean_text(record['实习出勤']))}
                    /
                    {html.escape(clean_text(record['实习周期']))}
                </td>
                <td class="skills-cell">{skill_badges}</td>
                <td>{link_html}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def dataframe_html_table(
    dataframe: pd.DataFrame,
    columns: list[str],
    rows: int = 20,
) -> str:
    frame = (
        dataframe[columns]
        .head(rows)
        .copy()
    )

    headings = "".join(
        f"<th>{html.escape(str(column))}</th>"
        for column in columns
    )

    body_rows = []

    for _, row in frame.iterrows():
        cells = "".join(
            "<td>"
            + html.escape(clean_text(value))
            + "</td>"
            for value in row.tolist()
        )

        body_rows.append(
            f"<tr>{cells}</tr>"
        )

    return (
        "<table>"
        f"<thead><tr>{headings}</tr></thead>"
        "<tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def write_dashboard(
    full_record_count: int,
    core_records: list[dict],
    frequency: pd.DataFrame,
    dashboard_dataframe: pd.DataFrame,
) -> None:
    total = len(core_records)
    excluded_count = max(
        full_record_count - total,
        0,
    )

    if excluded_count:
        sample_note = (
            f"数据来自已经完成字段清洗和技能证据审计的 "
            f"BOSS 收藏岗位。当前看板使用{total}条核心样本；"
            f"{excluded_count}条记录保留在全样本中，"
            "但不参与核心统计。"
        )
    else:
        sample_note = (
            f"数据来自已经完成字段清洗和技能证据审计的 "
            f"BOSS 收藏岗位。当前看板使用{total}条核心样本。"
        )

    internship_count = sum(
        record.get("employment_type")
        in {"实习", "实习/可转正"}
        for record in core_records
    )

    city_counter = Counter(
        clean_text(record.get("city"))
        or "未披露"
        for record in core_records
    )

    top_city, top_city_count = (
        city_counter.most_common(1)[0]
    )

    daily_median = median_or_none(
        [
            record.get("salary_midpoint")
            for record in core_records
            if record.get("salary_type")
            == "日薪"
        ]
    )

    monthly_median = median_or_none(
        [
            record.get("salary_midpoint")
            for record in core_records
            if record.get("salary_type")
            == "月薪"
        ]
    )

    top_skill = (
        clean_text(frequency.iloc[0]["技能"])
        if not frequency.empty
        else "无"
    )

    cards = [
        ("核心岗位样本", str(total)),
        (
            "实习相关岗位",
            (
                f"{internship_count}"
                f"（{internship_count / total:.1%}）"
            ),
        ),
        (
            "主要城市",
            f"{top_city} {top_city_count}条",
        ),
        (
            "日薪中位数",
            (
                f"{daily_median:.0f}元/天"
                if daily_median is not None
                else "无"
            ),
        ),
        (
            "月薪中位数",
            (
                f"{monthly_median:.1f}K/月"
                if monthly_median is not None
                else "无"
            ),
        ),
        ("最高频技能", top_skill),
    ]

    card_html = "".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                {html.escape(label)}
            </div>
            <div class="metric-value">
                {html.escape(value)}
            </div>
        </div>
        """
        for label, value in cards
    )

    chart_configs = [
        (
            "核心样本最高频技能",
            "01_top_skills.png",
            "查看哪些技术、方法和工作能力在职位描述中反复出现。",
            True,
        ),
        (
            "技能要求性质",
            "02_skill_requirement_breakdown.png",
            "区分必备、优先、岗位职责和普通提及，避免只看总词频。",
            True,
        ),
        (
            "全样本与核心样本比较",
            "03_full_core_comparison.png",
            "观察被标记的异常招聘文案对技能统计产生的影响。",
            True,
        ),
        (
            "五类能力维度",
            "04_skill_groups.png",
            "技术栈、AI与统计方法、工作任务、产品项目和通用能力的覆盖情况。",
            False,
        ),
        (
            "岗位类别",
            "05_role_categories.png",
            "当前收藏样本主要关注的岗位方向。",
            False,
        ),
        (
            "招聘类型",
            "06_employment_types.png",
            "实习、校招和常规招聘的样本组成。",
            False,
        ),
        (
            "城市分布",
            "07_cities.png",
            "该分布反映当前收藏结果，不代表全国招聘市场。",
            False,
        ),
        (
            "实习出勤要求",
            "08_internship_days.png",
            "统计实习相关岗位每周要求到岗的天数。",
            False,
        ),
        (
            "实习周期",
            "09_internship_duration.png",
            "统计实习相关岗位明确写出的实习周期。",
            False,
        ),
        (
            "公司规模",
            "10_company_sizes.png",
            "当前收藏岗位对应公司的规模分布。",
            False,
        ),
        (
            "行业分布",
            "11_industries.png",
            "当前收藏岗位覆盖的主要行业。",
            False,
        ),
        (
            "实习日薪区间",
            "12_daily_salary_ranges.png",
            "每条横线表示一个岗位的最低到最高日薪。",
            True,
        ),
        (
            "月薪岗位区间",
            "13_monthly_salary_ranges.png",
            "月薪单位为K/月，不与日薪混合计算。",
            True,
        ),
    ]

    chart_html = []

    for (
        title,
        filename,
        description,
        wide,
    ) in chart_configs:
        path = CHART_DIR / filename

        if not path.exists():
            continue

        panel_class = (
            "chart-panel wide"
            if wide
            else "chart-panel"
        )

        chart_html.append(
            f"""
            <section class="{panel_class}">
                <div class="chart-heading">
                    <h2>{html.escape(title)}</h2>
                    <p>{html.escape(description)}</p>
                </div>
                <img
                    src="{image_data_uri(path)}"
                    alt="{html.escape(title)}"
                >
            </section>
            """
        )

    categories = sorted(
        dashboard_dataframe[
            "岗位类别"
        ].dropna().unique().tolist()
    )

    employment_types = sorted(
        dashboard_dataframe[
            "招聘类型"
        ].dropna().unique().tolist()
    )

    cities = sorted(
        dashboard_dataframe[
            "城市"
        ].dropna().unique().tolist()
    )

    top_table = dataframe_html_table(
        frequency,
        [
            "排名",
            "技能",
            "技能组",
            "出现岗位数",
            "岗位覆盖率百分比",
            "必备岗位数",
            "优先岗位数",
            "职责岗位数",
        ],
        rows=20,
    )

    job_rows = build_job_table_html(
        dashboard_dataframe
    )

    dashboard = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>
<title>个人收藏岗位可视化看板 v1.1</title>

<style>
    :root {{
        --background: #f3f6f8;
        --card: #ffffff;
        --text: #17262c;
        --muted: #60727a;
        --primary: #0f766e;
        --primary-light: #e6f5f2;
        --border: #e2e9ec;
        --warning: #fff6d9;
        --warning-border: #d89d00;
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        font-family:
            "Microsoft YaHei",
            "PingFang SC",
            Arial,
            sans-serif;
        background: var(--background);
        color: var(--text);
    }}

    .page {{
        width: min(1460px, calc(100% - 32px));
        margin: 0 auto;
        padding: 34px 0 64px;
    }}

    h1 {{
        margin: 0 0 10px;
        font-size: 34px;
        line-height: 1.25;
    }}

    h2 {{
        margin: 0;
    }}

    .subtitle {{
        max-width: 980px;
        color: var(--muted);
        line-height: 1.8;
        margin: 0 0 24px;
    }}

    .notice {{
        background: var(--warning);
        border-left: 5px solid var(--warning-border);
        padding: 15px 18px;
        line-height: 1.75;
        margin: 22px 0;
        border-radius: 10px;
    }}

    .metrics {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin: 24px 0 30px;
    }}

    .metric-card {{
        position: relative;
        overflow: hidden;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 21px 22px;
        box-shadow: 0 5px 18px rgba(23, 52, 64, 0.06);
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        background: var(--primary);
    }}

    .metric-label {{
        color: var(--muted);
        font-size: 14px;
    }}

    .metric-value {{
        margin-top: 9px;
        font-size: 25px;
        font-weight: 750;
    }}

    .chart-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 22px;
    }}

    .chart-panel {{
        min-width: 0;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 22px;
        box-shadow: 0 5px 18px rgba(23, 52, 64, 0.06);
    }}

    .chart-panel.wide {{
        grid-column: 1 / -1;
    }}

    .chart-heading {{
        margin-bottom: 8px;
    }}

    .chart-heading h2 {{
        font-size: 21px;
        line-height: 1.35;
    }}

    .chart-heading p {{
        margin: 8px 0 0;
        min-height: 26px;
        color: var(--muted);
        line-height: 1.65;
    }}

    .chart-panel img {{
        display: block;
        width: 100%;
        height: auto;
        margin-top: 6px;
    }}

    .section-card {{
        margin-top: 24px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 23px;
        box-shadow: 0 5px 18px rgba(23, 52, 64, 0.06);
    }}

    .section-card > p {{
        color: var(--muted);
        line-height: 1.7;
    }}

    .table-wrap {{
        overflow-x: auto;
        margin-top: 16px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}

    th {{
        position: sticky;
        top: 0;
        z-index: 1;
        background: var(--primary);
        color: white;
        padding: 12px 10px;
        text-align: left;
        white-space: nowrap;
    }}

    td {{
        padding: 11px 10px;
        border-bottom: 1px solid var(--border);
        vertical-align: top;
    }}

    tbody tr:hover td {{
        background: #f4faf8;
    }}

    .filters {{
        display: grid;
        grid-template-columns:
            minmax(240px, 2fr)
            repeat(3, minmax(150px, 1fr));
        gap: 12px;
        margin: 18px 0 10px;
    }}

    .filters input,
    .filters select {{
        width: 100%;
        border: 1px solid #cfdadd;
        border-radius: 9px;
        padding: 11px 12px;
        background: white;
        color: var(--text);
        font: inherit;
    }}

    .filters input:focus,
    .filters select:focus {{
        outline: 2px solid rgba(15, 118, 110, 0.20);
        border-color: var(--primary);
    }}

    .result-count {{
        margin: 10px 0;
        color: var(--muted);
    }}

    .job-title-cell {{
        min-width: 245px;
        font-weight: 650;
    }}

    .skills-cell {{
        min-width: 320px;
        max-width: 450px;
    }}

    .skill-badge {{
        display: inline-block;
        margin: 2px 4px 2px 0;
        padding: 4px 7px;
        border-radius: 999px;
        background: var(--primary-light);
        color: #075e57;
        font-size: 12px;
        white-space: nowrap;
    }}

    .job-link {{
        display: inline-block;
        white-space: nowrap;
        color: var(--primary);
        text-decoration: none;
        font-weight: 650;
    }}

    .job-link:hover {{
        text-decoration: underline;
    }}

    .footer-note {{
        margin-top: 28px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
    }}

    @media (max-width: 980px) {{
        .metrics {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}

        .chart-grid {{
            grid-template-columns: 1fr;
        }}

        .chart-panel.wide {{
            grid-column: auto;
        }}

        .filters {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}

    @media (max-width: 620px) {{
        .page {{
            width: min(100% - 20px, 1460px);
            padding-top: 22px;
        }}

        h1 {{
            font-size: 27px;
        }}

        .metrics {{
            grid-template-columns: 1fr;
        }}

        .filters {{
            grid-template-columns: 1fr;
        }}

        .chart-panel,
        .section-card {{
            padding: 16px;
        }}
    }}
</style>
</head>

<body>
<div class="page">
    <header>
        <h1>个人收藏岗位可视化看板 v1.1</h1>

        <p class="subtitle">
            {html.escape(sample_note)}
        </p>
    </header>

    <div class="notice">
        本看板描述的是当前收藏与关注岗位，
        不是全国招聘市场的随机样本。
        深圳岗位占比较高，主要由当前采样范围造成。
    </div>

    <section class="metrics">
        {card_html}
    </section>

    <main class="chart-grid">
        {''.join(chart_html)}
    </main>

    <section class="section-card">
        <h2>核心样本技能频率</h2>
        <p>
            “出现岗位数”表示有多少份JD明确提到该项能力；
            必备、优先和职责分类来自证据句中的规则判断。
        </p>

        <div class="table-wrap">
            {top_table}
        </div>
    </section>

    <section class="section-card">
        <h2>岗位明细筛选</h2>

        <p>
            可按岗位名称、公司、技能、岗位类别、
            招聘类型和城市进行本地筛选。
        </p>

        <div class="filters">
            <input
                id="searchInput"
                type="search"
                placeholder="搜索岗位、公司或技能"
            >

            <select id="categoryFilter">
                <option value="">全部岗位类别</option>
                {option_html(categories)}
            </select>

            <select id="employmentFilter">
                <option value="">全部招聘类型</option>
                {option_html(employment_types)}
            </select>

            <select id="cityFilter">
                <option value="">全部城市</option>
                {option_html(cities)}
            </select>
        </div>

        <div class="result-count">
            当前显示
            <strong id="visibleCount">
                {len(dashboard_dataframe)}
            </strong>
            条岗位
        </div>

        <div class="table-wrap">
            <table id="jobTable">
                <thead>
                    <tr>
                        <th>岗位名称</th>
                        <th>岗位类别</th>
                        <th>公司</th>
                        <th>城市</th>
                        <th>薪资</th>
                        <th>招聘类型</th>
                        <th>学历</th>
                        <th>出勤/周期</th>
                        <th>明确提及技能</th>
                        <th>原岗位</th>
                    </tr>
                </thead>

                <tbody>
                    {job_rows}
                </tbody>
            </table>
        </div>
    </section>

    <p class="footer-note">
        本HTML已将所有PNG图表嵌入文件内部，
        单独复制 visual_dashboard_v11.html
        即可保留全部图表。
    </p>
</div>

<script>
    const searchInput =
        document.getElementById("searchInput");

    const categoryFilter =
        document.getElementById("categoryFilter");

    const employmentFilter =
        document.getElementById("employmentFilter");

    const cityFilter =
        document.getElementById("cityFilter");

    const visibleCount =
        document.getElementById("visibleCount");

    const rows = Array.from(
        document.querySelectorAll(
            "#jobTable tbody tr"
        )
    );

    function applyFilters() {{
        const keyword =
            searchInput.value.trim().toLowerCase();

        const category =
            categoryFilter.value;

        const employment =
            employmentFilter.value;

        const city =
            cityFilter.value;

        let visible = 0;

        rows.forEach((row) => {{
            const matchesKeyword =
                !keyword
                || row.dataset.search
                    .toLowerCase()
                    .includes(keyword);

            const matchesCategory =
                !category
                || row.dataset.category === category;

            const matchesEmployment =
                !employment
                || row.dataset.employment
                    === employment;

            const matchesCity =
                !city
                || row.dataset.city === city;

            const show =
                matchesKeyword
                && matchesCategory
                && matchesEmployment
                && matchesCity;

            row.style.display =
                show ? "" : "none";

            if (show) {{
                visible += 1;
            }}
        }});

        visibleCount.textContent =
            String(visible);
    }}

    [
        searchInput,
        categoryFilter,
        employmentFilter,
        cityFilter,
    ].forEach((element) => {{
        element.addEventListener(
            "input",
            applyFilters,
        );

        element.addEventListener(
            "change",
            applyFilters,
        );
    }});
</script>
</body>
</html>
"""

    DASHBOARD_FILE.write_text(
        dashboard,
        encoding="utf-8",
    )


def write_summary(
    core_records: list[dict],
    frequency: pd.DataFrame,
) -> None:
    internship_records = [
        record
        for record in core_records
        if record.get("employment_type")
        in {"实习", "实习/可转正"}
    ]

    daily_median = median_or_none(
        [
            record.get("salary_midpoint")
            for record in core_records
            if record.get("salary_type")
            == "日薪"
        ]
    )

    monthly_median = median_or_none(
        [
            record.get("salary_midpoint")
            for record in core_records
            if record.get("salary_type")
            == "月薪"
        ]
    )

    lines = [
        "# 岗位可视化摘要 v1.1",
        "",
        f"- 核心岗位样本：{len(core_records)}条",
        f"- 实习相关岗位：{len(internship_records)}条",
        (
            "- 日薪中位数："
            + (
                f"{daily_median:.0f}元/天"
                if daily_median is not None
                else "无"
            )
        ),
        (
            "- 月薪中位数："
            + (
                f"{monthly_median:.1f}K/月"
                if monthly_median is not None
                else "无"
            )
        ),
        "",
        "## 核心样本最高频技能",
        "",
    ]

    for _, row in frequency.head(
        10
    ).iterrows():
        lines.append(
            f"- {row['技能']}："
            f"{int(row['出现岗位数'])}条，"
            f"{row['岗位覆盖率百分比']}"
        )

    lines.extend(
        [
            "",
            "## 看板文件",
            "",
            "`visual_dashboard_v11.html`",
            "",
            "该HTML已内嵌全部PNG图表，"
            "可以作为单文件打开或分享。",
        ]
    )

    SUMMARY_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    configure_matplotlib()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = load_jsonl(INPUT_JSONL)
    enrich_salary(records)

    core_records = [
        record
        for record in records
        if record.get("core_sample", True)
    ]

    core_frequency = pd.read_csv(
        CORE_FREQUENCY_FILE,
        encoding="utf-8-sig",
    )

    full_frequency = pd.read_csv(
        FULL_FREQUENCY_FILE,
        encoding="utf-8-sig",
    )

    save_skill_frequency_chart(
        core_frequency
    )

    save_requirement_breakdown(
        core_frequency
    )

    save_full_core_comparison(
        full_frequency,
        core_frequency,
        len(records),
        len(core_records),
    )

    save_skill_group_chart(
        core_records
    )

    role_counter = Counter(
        clean_text(
            record.get("role_category_v11")
        )
        or "其他/综合"
        for record in core_records
    )

    save_count_bar(
        role_counter,
        "05_role_categories.png",
        len(core_records),
    )

    employment_counter = Counter(
        clean_text(
            record.get("employment_type")
        )
        or "未分类"
        for record in core_records
    )

    save_count_bar(
        employment_counter,
        "06_employment_types.png",
        len(core_records),
    )

    city_counter = Counter(
        clean_text(record.get("city"))
        or "未披露"
        for record in core_records
    )

    save_count_bar(
        city_counter,
        "07_cities.png",
        len(core_records),
    )

    internship_records = [
        record
        for record in core_records
        if record.get("employment_type")
        in {"实习", "实习/可转正"}
    ]

    days_counter = Counter(
        clean_text(
            record.get(
                "internship_days_per_week"
            )
        )
        or "未披露"
        for record in internship_records
    )

    save_count_bar(
        days_counter,
        "08_internship_days.png",
        len(internship_records),
    )

    duration_counter = Counter(
        clean_text(
            record.get(
                "internship_duration"
            )
        )
        or "未披露"
        for record in internship_records
    )

    save_count_bar(
        duration_counter,
        "09_internship_duration.png",
        len(internship_records),
    )

    company_size_counter = Counter(
        clean_text(
            record.get("company_size")
        )
        or "未披露"
        for record in core_records
    )

    save_count_bar(
        company_size_counter,
        "10_company_sizes.png",
        len(core_records),
    )

    industry_counter = Counter(
        clean_text(
            record.get("industry")
        )
        or "未披露"
        for record in core_records
    )

    save_count_bar(
        industry_counter,
        "11_industries.png",
        len(core_records),
        max_items=12,
    )

    save_salary_range_chart(
        core_records,
        "日薪",
        "12_daily_salary_ranges.png",
        "元/天",
    )

    save_salary_range_chart(
        core_records,
        "月薪",
        "13_monthly_salary_ranges.png",
        "K/月",
    )

    dashboard_dataframe = (
        build_dashboard_dataframe(
            core_records
        )
    )

    dashboard_dataframe.to_csv(
        DASHBOARD_DATA_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    write_dashboard(
        len(records),
        core_records,
        core_frequency,
        dashboard_dataframe,
    )

    enhance_dashboard(DASHBOARD_FILE)
    enhance_management_link(DASHBOARD_FILE)

    write_summary(
        core_records,
        core_frequency,
    )

    chart_count = len(
        list(CHART_DIR.glob("*.png"))
    )

    file_size_mb = (
        DASHBOARD_FILE.stat().st_size
        / 1024
        / 1024
    )

    print("=" * 72)
    print("岗位可视化 v1.1 完成")
    print("=" * 72)
    print(f"全样本岗位：{len(records)}")
    print(f"核心样本岗位：{len(core_records)}")
    print(f"生成图表：{chart_count} 张")
    print(
        "岗位筛选表："
        f"{len(dashboard_dataframe)} 条"
    )
    print(f"图表目录：{CHART_DIR.resolve()}")
    print(f"单文件看板：{DASHBOARD_FILE.resolve()}")
    print(
        f"看板文件大小：{file_size_mb:.2f} MB"
    )
    print(f"明细数据：{DASHBOARD_DATA_FILE.resolve()}")
    print(f"摘要文件：{SUMMARY_FILE.resolve()}")


if __name__ == "__main__":
    main()


# PHASE_7B2_DASHBOARD_LINK
