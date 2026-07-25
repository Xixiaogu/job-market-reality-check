# Job Market Reality Check

> An evidence-based AI skill for exploring career options, skill gaps, and learning priorities from job-posting data.

## About

**Job Market Reality Check** compares a user's background with a supplied job-posting dataset.

It aims to answer three practical questions:

- What roles are realistic with my current background?
- Which skills appear most often in relevant job postings?
- What should I learn next?

The project is designed for students, new graduates, and early-career job seekers interested in data analysis, Python, machine learning, and related roles.

## Planned Workflow

```text
User profile
    +
Job-posting dataset
    ↓
Data cleaning and normalization
    ↓
Job-category and skill extraction
    ↓
Role matching and skill-gap analysis
    ↓
Evidence-based report
```

## Planned Features

- Analyze job titles, cities, salaries, education, and experience requirements
- Extract technical skills from job descriptions
- Compare job requirements with a user profile
- Identify realistic, stretch, and currently unsuitable roles
- Rank missing skills by their frequency in relevant postings
- Generate a Markdown career reality-check report
- Optionally use fastai for a job-category classification baseline

## Example Output

```text
Realistic roles
- Data Analyst Intern
- Data Operations Intern
- Python Data Processing Intern

Stretch roles
- Machine Learning Intern

Common skill gaps
1. SQL
2. Linux
3. PyTorch

Evidence
- Results based on the supplied job-posting sample
- Salary figures refer to advertised salary ranges
- Findings do not represent the entire labor market
```

## Project Structure

```text
job-market-reality-check/
├── SKILL.md
├── README.md
├── LICENSE
├── references/
│   ├── data_schema.md
│   ├── methodology.md
│   └── skill_taxonomy.yml
├── scripts/
├── assets/
└── examples/
```

## Project Status

The project is currently under development.

### v0.1

- [x] Create the repository
- [x] Define the project scope
- [ ] Write the initial `SKILL.md`
- [ ] Define the job-data schema
- [ ] Create the skill taxonomy
- [ ] Build a minimal working example

### Later Versions

- [ ] Salary normalization
- [ ] Skill extraction
- [ ] User-profile matching
- [ ] Report generation
- [ ] fastai classification baseline
- [ ] Additional job datasets and regions

## Design Principles

- Use evidence instead of generic career claims
- Keep matching rules understandable
- Separate dataset findings from broader market conclusions
- Never invent job postings, salaries, or skill frequencies
- Clearly report sample size, source, filters, and limitations
- Do not bypass logins, CAPTCHAs, or website access restrictions

## Limitations

The quality of the output depends on the supplied data.

A small or biased sample cannot represent the entire job market. Advertised salaries may differ from actual compensation, and keyword matching cannot prove that a user has mastered a skill.

The generated report should be treated as exploratory career evidence, not as a hiring prediction or employment guarantee.

## License

This project is licensed under the MIT License.