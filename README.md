# Job Market Reality Check

<p align="center">

An evidence-based AI skill for understanding career opportunities, skill gaps, and job-market fit through real-world job posting data.

</p>

---

## 1. Overview

Job Market Reality Check is an open-source AI Skill designed to help students, early-career developers, and career explorers make more informed decisions based on real job-market evidence.

Many people make career decisions based on:

- General internet advice
- Personal opinions
- Social media trends
- Individual success stories

However, these sources often fail to answer practical questions:

- What jobs can I realistically apply for with my current skills?
- Which skills are actually demanded by companies?
- What is the gap between my current ability and market requirements?
- Which skills should I learn next to improve employability?
- Are my expectations aligned with the actual job market?

This project aims to transform career planning from a subjective decision into a data-driven analysis process.

The core idea is:

> **Do not guess your career path. Analyze where your current skills fit in the real job market.**

---

# 2. Motivation

For students and early-career developers, choosing a technical direction is often difficult.

For example:

A student may know:

- Python
- Basic machine learning
- Data analysis
- Deep learning frameworks

But still does not know:

- Whether they are closer to a data analyst or machine learning engineer;
- Which additional skills are required;
- Whether their current learning path matches industry demand;
- What realistic entry-level opportunities exist.

Traditional career advice often provides general recommendations:

```
Learn Python.
Learn AI.
Build projects.
Improve your resume.
```

However, such advice lacks personalized evidence.

Job Market Reality Check attempts to answer these questions by combining:

```
Personal Profile
        +
Job Market Data
        +
Skill Requirement Analysis
        +
Compatibility Evaluation
        ↓
Evidence-based Career Report
```

---

# 3. Project Goals

The goal of this project is NOT to:

- Predict employment outcomes;
- Guarantee job offers;
- Replace professional career consulting;
- Automatically apply for jobs.

Instead, it focuses on:

## 3.1 Career Reality Assessment

Understand:

- Current suitable job categories;
- Possible career directions;
- Market demand level.

---

## 3.2 Skill Gap Analysis

Identify:

- Existing strengths;
- Missing skills;
- High-value learning priorities.

---

## 3.3 Evidence-Based Decision Making

Provide recommendations supported by:

- Job posting statistics;
- Skill frequency analysis;
- Compatibility evaluation.

---

# 4. Core Workflow

The system follows the workflow:

```
                User Profile

        Education
        Major
        Skills
        Projects
        Experience
              |
              |
              ↓

          Job Dataset

        Position
        Salary
        Location
        Requirements
        Skills
              |
              |
              ↓

      Data Processing Pipeline

        Cleaning
        Normalization
        Skill Extraction
        Classification
              |
              |
              ↓

       Career Reality Report

        Suitable Roles
        Skill Match
        Skill Gap
        Salary Range
        Learning Roadmap
```

---

# 5. Main Features

## 5.1 Job Market Analysis

Analyze collected job posting data:

### Basic Information

- Job title
- Company
- Location
- Salary
- Education requirement
- Experience requirement


### Market Statistics

Generate:

- Job category distribution;
- Geographic distribution;
- Salary distribution;
- Requirement frequency.


Example:

```
Sample Analysis:

Data Analyst Related Jobs

Python:
72%

SQL:
65%

Excel:
51%

Power BI:
38%
```

---

# 5.2 Skill Demand Analysis

The system extracts technical skills from job descriptions.

Supported categories:

## Programming

- Python
- Java
- C++
- JavaScript


## Data Analysis

- pandas
- NumPy
- Excel
- SQL
- Tableau
- Power BI


## Machine Learning

- Scikit-learn
- PyTorch
- TensorFlow
- Deep Learning


## Engineering

- Linux
- Git
- Docker
- Cloud Platform

---

# 5.3 Personal Skill Matching

The system compares:

```
User Capability

        VS

Job Requirements
```

Example:

```
User Profile:

Python          ✓
Pandas          ✓
Scikit-learn    ✓
SQL             △
Docker          ✕

--------------------------------

Analysis:

High Compatibility:

✓ Data Analyst Intern
✓ Data Science Intern


Medium Compatibility:

△ Machine Learning Intern


Main Skill Gaps:

1. SQL
2. Linux
3. Docker
```

---

# 5.4 Explainable Recommendations

Instead of producing an unexplained score:

```
Match Score: 86%
```

the system emphasizes evidence:

Example:

```
Recommendation:

Data Analyst Intern

Reasons:

✓ Python requirement satisfied
✓ Data processing experience available
✓ Machine learning background is beneficial

Missing:

△ SQL
△ Business intelligence tools
```

---

# 6. Design Principles

## 6.1 Evidence Over Assumption

All recommendations should be based on:

- Available job posting data;
- Clearly defined analysis rules;
- Transparent methodology.

---

## 6.2 Explainability Over Black-box Prediction

The system prioritizes:

```
Why this recommendation?
What evidence supports it?
What should be improved?
```

rather than only producing numerical scores.

---

## 6.3 Honest Limitations

Career analysis contains uncertainty.

Therefore:

- Small datasets cannot represent the entire labor market;
- Job advertisements may contain inaccurate salary information;
- Keyword matching does not prove actual ability;
- Recommendations are exploratory evidence, not guarantees.

---

# 7. Project Structure

Current planned structure:

```
job-market-reality-check/

├── SKILL.md
│
├── README.md
│
├── LICENSE
│
├── references/
│   ├── data_schema.md
│   ├── skill_taxonomy.yml
│   └── methodology.md
│
├── scripts/
│   ├── salary_parser.py
│   ├── skill_extractor.py
│   └── report_generator.py
│
├── assets/
│
└── examples/
    └── demo/
```

---

# 8. Technology Stack

Planned technologies:

## Data Processing

- Python
- pandas
- NumPy


## Visualization

- Matplotlib
- Plotly


## Machine Learning

- Scikit-learn

Optional:

- fastai
- PyTorch


## AI Skill Framework

- OpenAI Skill format
- Markdown-based workflow definition

---

# 9. Roadmap

## Version 0.1 - Project Initialization

Status:

🚧 In Progress

Tasks:

- Define Skill specification;
- Create project structure;
- Define data schema;
- Define skill taxonomy.


---

## Version 0.2 - Job Market Analysis Pipeline

Tasks:

- Import job datasets;
- Clean and normalize data;
- Extract technical skills;
- Generate market statistics.


---

## Version 0.3 - Personal Matching Engine

Tasks:

- Create user profile format;
- Implement skill matching;
- Generate compatibility reports.


---

## Version 0.4 - Machine Learning Enhancement

Potential extensions:

- Job category classification;
- Semantic skill matching;
- Embedding-based retrieval;
- fastai baseline models.


---

# 10. Example Use Cases

## Case 1

Input:

```
Bachelor student

Skills:

Python
pandas
machine learning basics

Goal:

Find suitable AI/data jobs
```

Output:

```
Recommended:

Data Analyst Intern
Data Science Intern

Need improvement:

SQL
Visualization
Deployment skills
```

---

## Case 2

Input:

```
Current skills:

Embedded systems
C
STM32

Interested in AI transition
```

Output:

```
Possible transition paths:

Embedded AI Engineer
Edge AI Developer

Recommended skills:

Python
PyTorch
Computer Vision
Linux
```

---

# 11. Future Extensions

Possible future improvements:

- Support different countries and regions;
- Add industry-specific analysis;
- Add semantic matching models;
- Integrate vector retrieval;
- Build interactive dashboards;
- Create personalized learning plans.

---

# 12. Disclaimer

This project is an experimental open-source tool.

It does not provide:

- Employment guarantees;
- Salary guarantees;
- Professional career counseling.

All recommendations should be interpreted according to:

- Data source;
- Sample size;
- Analysis methodology;
- Individual circumstances.

---

# 13. License

MIT License