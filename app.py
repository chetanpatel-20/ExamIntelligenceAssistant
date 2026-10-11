import csv
from pathlib import Path
from pypdf import PdfReader
import re

# ==========================================
# EXAM INTELLIGENCE ASSISTANT
# ==========================================

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "Question_papers"

topic_keywords = {
    "Variables and Data Types": [
        "variable", "data types"
    ],
    "Functions": [
        "function", "functions"
    ],
    "Loops": [
        "loops", "for and while", "while loops"
    ],
    "Conditional Statements": [
        "conditional statements", "if statement"
    ],
    "Lists and Tuples": [
        "lists and tuples", "list", "tuple"
    ],
    "File Handling": [
        "file handling"
    ]
}


def extract_questions(pdf_text):
    """Extract numbered questions from PDF text."""
    questions = []

    for line in pdf_text.splitlines():
        line = line.strip()

        if re.match(r"^Q\d+\.", line, re.IGNORECASE):
            questions.append(line)

    return questions


def get_marks(question):
    """Read marks written like (5 marks)."""
    match = re.search(
        r"\((\d+)\s*marks?\)",
        question,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return 0


def matches_topic(question, keywords):
    """Check whether a question matches a topic."""
    question = question.lower()

    return any(
        keyword.lower() in question
        for keyword in keywords
    )


def main():
    print("=" * 55)
    print("             EXAM INTELLIGENCE ASSISTANT")
    print("=" * 55)

    # STEP 1: Find PDF files
    if not PDF_DIR.exists():
        print("\nERROR: Question_papers folder nahi mila.")
        print("Project folder mein Question_papers naam ka folder banao.")
        return

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print("\nKoi PDF nahi mili!")
        print("Apni PDF files Question_papers folder mein rakho.")
        return

    print(f"\nPDF files found: {len(pdf_files)}")

    questions_by_pdf = {}

    # STEP 2: Read every PDF
    for pdf_file in pdf_files:
        print(f"\nReading: {pdf_file.name}")

        try:
            reader = PdfReader(str(pdf_file))
            pdf_text = ""

            for page in reader.pages:
                pdf_text += (page.extract_text() or "") + "\n"

            questions = extract_questions(pdf_text)
            questions_by_pdf[pdf_file.name] = questions

            print(f"Questions extracted: {len(questions)}")

        except Exception as error:
            print(f"PDF read nahi ho payi: {error}")

    # Keep only PDFs from which questions were extracted
    questions_by_pdf = {
        filename: questions
        for filename, questions in questions_by_pdf.items()
        if questions
    }

    if not questions_by_pdf:
        print("\nKisi PDF se questions extract nahi hue.")
        print("Check karo ki PDF text-based hai aur questions Q1. format mein hain.")
        return

    all_questions = []

    for questions in questions_by_pdf.values():
        all_questions.extend(questions)

    total_questions = len(all_questions)

    # STEP 3: Overall analysis
    print("\n" + "=" * 55)
    print("OVERALL ANALYSIS")
    print("=" * 55)

    print(f"PDF files processed with questions: {len(questions_by_pdf)}")
    print(f"Total questions found: {total_questions}")

    topic_counts = {}
    topic_marks = {}
    matched_questions_by_topic = {}

    # STEP 4: Topic analysis
    print("\nTOPIC ANALYSIS")
    print("-" * 55)

    for topic, keywords in topic_keywords.items():
        matched = [
            question
            for question in all_questions
            if matches_topic(question, keywords)
        ]

        topic_counts[topic] = len(matched)
        matched_questions_by_topic[topic] = matched
        topic_marks[topic] = sum(
            get_marks(question) for question in matched
        )

        if matched:
            print(
                f"{topic}: {len(matched)} question(s), "
                f"{topic_marks[topic]} marks"
            )

    # STEP 5: Priority scores
    # Scores are based on marks found in the loaded papers.
    total_matched_marks = sum(topic_marks.values())

    print("\nSTUDY PRIORITY LIST")
    print("-" * 55)

    ranked_topics = sorted(
        [
            topic for topic in topic_keywords
            if topic_counts[topic] > 0
        ],
        key=lambda topic: (
            topic_marks[topic],
            topic_counts[topic]
        ),
        reverse=True
    )

    for rank, topic in enumerate(ranked_topics, start=1):
        count = topic_counts[topic]
        marks = topic_marks[topic]

        if total_matched_marks > 0:
            priority_score = (
                marks / total_matched_marks * 100
            )
        else:
            priority_score = 0

        # Confidence here means data coverage, not exam probability.
        confidence_score = (
            count / total_questions * 100
            if total_questions else 0
        )

        if priority_score >= 25:
            priority_level = "HIGH"
            recommendation = "Study this topic first and practise questions."
        elif priority_score >= 12:
            priority_level = "MEDIUM"
            recommendation = "Revise the concepts and solve practice questions."
        else:
            priority_level = "LOW"
            recommendation = "Review this topic after higher-priority topics."

        print(f"\n{rank}. {topic}")
        print(f"   Questions found: {count}")
        print(f"   Marks found: {marks}")
        print(f"   Priority Score: {priority_score:.1f}/100")
        print(f"   Priority Level: {priority_level}")
        print(f"   Confidence Score: {confidence_score:.1f}/100")
        print(
            f"   Reason: {count} question(s) matched this topic, "
            f"carrying {marks} marks across the loaded PDFs."
        )
        print(f"   Recommendation: {recommendation}")

    # STEP 6: Year-wise topic trend
    print("\n" + "=" * 55)
    print("YEAR-WISE TOPIC TREND ANALYSIS")
    print("=" * 55)

    for filename, questions in questions_by_pdf.items():
        year_match = re.search(r"20\d{2}", filename)
        year = year_match.group() if year_match else "Year unknown"

        print(f"\nPaper: {filename} | Year: {year}")

        for topic, keywords in topic_keywords.items():
            count = sum(
                1 for question in questions
                if matches_topic(question, keywords)
            )

            if count > 0:
                print(f"   {topic}: {count} question(s)")

    # STEP 7: Compare topics across different PDFs
    print("\n" + "=" * 55)
    print("REPEAT-TOPIC COMPARISON")
    print("=" * 55)

    repeat_found = False

    for topic, keywords in topic_keywords.items():
        papers_with_topic = []

        for filename, questions in questions_by_pdf.items():
            found = any(
                matches_topic(question, keywords)
                for question in questions
            )

            if found:
                papers_with_topic.append(filename)

        if len(papers_with_topic) > 1:
            repeat_found = True
            print(
                f"\n{topic}: Found in "
                f"{len(papers_with_topic)} different papers"
            )

            for filename in papers_with_topic:
                print(f"   - {filename}")

    if not repeat_found:
        print("No topics were found in more than one paper.")

        # STEP 8: Exact repeated-question analysis
    print("\n" + "=" * 55)
    print("EXACT REPEATED QUESTION ANALYSIS")
    print("=" * 55)

    normalized_questions = {}

    for filename, questions in questions_by_pdf.items():
        for question in questions:
            # Remove Q numbers and marks for comparison
            clean_question = re.sub(
                r"^Q\d+\.\s*",
                "",
                question,
                flags=re.IGNORECASE
            )

            clean_question = re.sub(
                r"\(\d+\s*marks?\)",
                "",
                clean_question,
                flags=re.IGNORECASE
            )

            clean_question = " ".join(
                clean_question.lower().split()
            )

            if clean_question not in normalized_questions:
                normalized_questions[clean_question] = {
                    "text": question,
                    "papers": []
                }

            if filename not in normalized_questions[clean_question]["papers"]:
                normalized_questions[clean_question]["papers"].append(filename)

    repeated_count = 0

    for question_data in normalized_questions.values():
        if len(question_data["papers"]) > 1:
            repeated_count += 1

            print(f"\nQuestion: {question_data['text']}")
            print(
                f"Found in {len(question_data['papers'])} papers:"
            )

            for filename in question_data["papers"]:
                print(f"  - {filename}")

    if repeated_count == 0:
        print("No exact repeated questions found.")

    print(f"\nTotal repeated question patterns: {repeated_count}")

    # STEP 9: Export topic analysis to CSV
    csv_path = BASE_DIR / "study_priority_report.csv"

    try:
        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow([
                "Rank",
                "Topic",
                "Questions Found",
                "Marks Found",
                "Priority Score",
                "Priority Level",
                "Confidence Score",
                "Recommendation"
            ])

            for rank, topic in enumerate(ranked_topics, start=1):
                count = topic_counts[topic]
                marks = topic_marks[topic]

                if total_matched_marks > 0:
                    priority_score = (
                        marks / total_matched_marks * 100
                    )
                else:
                    priority_score = 0

                confidence_score = (
                    count / total_questions * 100
                    if total_questions else 0
                )

                if priority_score >= 25:
                    priority_level = "HIGH"
                    recommendation = (
                        "Study first and practise questions"
                    )
                elif priority_score >= 12:
                    priority_level = "MEDIUM"
                    recommendation = (
                        "Revise concepts and solve practice questions"
                    )
                else:
                    priority_level = "LOW"
                    recommendation = (
                        "Review basics after higher-priority topics"
                    )

                writer.writerow([
                    rank,
                    topic,
                    count,
                    marks,
                    round(priority_score, 1),
                    priority_level,
                    round(confidence_score, 1),
                    recommendation
                ])

        print(f"\nCSV report saved successfully: {csv_path.name}")

    except OSError as error:
        print(f"\nCSV report save nahi ho payi: {error}")

    print("\n" + "=" * 55)
    print("Analysis complete!")
    print("=" * 55)


if __name__ == "__main__":
    main()