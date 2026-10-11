# Exam Intelligence Assistant

An intelligent exam preparation dashboard that analyzes previous years' question papers and helps students prioritize their studies.

## Features

- **Question Paper Analysis:** Extracts questions from past examination papers.
- **Topic Mapping:** Groups questions by syllabus topics.
- **Topic Priority:** Highlights important topics using question frequency and marks weightage.
- **Repeated Questions:** Identifies exact and similar questions across papers.
- **Year-wise Trends:** Compares question patterns across different years.
- **Study Priority Dashboard:** Helps students plan their preparation.

## Tech Stack

- Python
- Streamlit
- Pandas
- pypdf

## Project Structure

```text
ExamIntelligenceAssistant/
├── app.py
├── dashboard.py
├── requirements.txt
├── paper_2024.pdf
└── question_paper_2025.pdf
```

## Installation and Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/chetanpatel-20/ExamIntelligenceAssistant.git
   ```

2. Open the project folder:

   ```bash
   cd ExamIntelligenceAssistant
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the dashboard:

   ```bash
   python -m streamlit run dashboard.py
   ```

5. Open the local URL displayed in the terminal.

## Purpose

The goal of this project is to help students analyze previous examination papers, understand topic trends, and make more informed study plans.

## Note

Topic priority is based on the available question papers and detected marks. Similarity scores indicate text similarity, not the probability that a question will appear in a future examination.
