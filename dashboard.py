
import re
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st
from pypdf import PdfReader


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Exam Intelligence Assistant",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Exam Intelligence Assistant")
st.caption(
    "Analyze question papers, identify important topics, "
    "compare marks weightage, and plan your study."
)


# --------------------------------------------------
# QUESTION PAPER FOLDER
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PAPER_DIR = BASE_DIR / "Question_papers"

if not PAPER_DIR.exists():
    PAPER_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# TOPIC MAPPING
# --------------------------------------------------
TOPIC_KEYWORDS = {
    "Variables and Data Types": [
        "variable", "data type", "data types", "type casting",
        "type conversion", "integer", "float", "string", "boolean"
    ],
    "Conditional Statements": [
        "if statement", "if-else", "if else", "elif",
        "conditional statement", "conditional statements",
        "nested if", "decision making"
    ],
    "Loops": [
        "for loop", "while loop", "for and while",
        "loops", "looping", "break statement",
        "continue statement", "range function"
    ],
    "Functions": [
        "function", "functions", "parameter", "parameters",
        "argument", "arguments", "return statement",
        "lambda function", "recursive function", "recursion"
    ],
    "Lists and Tuples": [
        "list", "lists", "tuple", "tuples",
        "list comprehension", "list slicing"
    ],
    "Dictionaries and Sets": [
        "dictionary", "dictionaries", "dict", "set",
        "sets", "key-value", "key value"
    ],
    "Strings": [
        "string", "strings", "string slicing",
        "string manipulation", "string methods"
    ],
    "Object-Oriented Programming": [
        "oops", "object oriented", "object-oriented",
        "class", "classes", "object", "objects",
        "inheritance", "polymorphism", "encapsulation",
        "abstraction", "constructor", "self keyword"
    ],
    "File Handling": [
        "file handling", "file handling in python",
        "reading a file", "writing a file", "file modes",
        "open a file", "open function", "read function",
        "write function"
    ],
    "Exception Handling": [
        "exception", "exceptions", "exception handling",
        "try except", "try-except", "finally block",
        "raise statement"
    ],
    "Modules and Packages": [
        "module", "modules", "package", "packages",
        "import statement", "importing modules"
    ],
    "Operators": [
        "operator", "operators", "arithmetic operator",
        "logical operator", "comparison operator",
        "assignment operator", "bitwise operator"
    ],
    "Python Basics": [
        "python features", "features of python",
        "introduction to python", "python programming",
        "advantages of python", "disadvantages of python"
    ],
}


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def normalize_question(question):
    """Normalize text to identify repeated questions."""
    text = question.lower()
    text = re.sub(r"\b\d+\s*marks?\b", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def year_from_filename(filename):
    """Find year in filenames such as paper_2024.pdf."""
    match = re.search(r"(?:19|20)\d{2}", filename)
    return match.group(0) if match else "Unknown"


def get_marks(question):
    """Extract marks when explicitly shown in a question."""
    patterns = [
        r"\[\s*(\d+)\s*marks?\s*\]",
        r"\(\s*(\d+)\s*marks?\s*\)",
        r"[-–—]\s*(\d+)\s*marks?\b",
        r"\b(\d+)\s*marks?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def find_topics(question):
    """Map a question to matching topics using keywords."""
    text = question.lower()
    found_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundaries to avoid matching a word
            # inside an unrelated longer word.
            pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"

            if re.search(pattern, text):
                found_topics.append(topic)
                break

    if not found_topics:
        return ["Unclassified"]

    return found_topics


def is_instruction_or_heading(text):
    cleaned = text.strip().lower()

    if len(cleaned) < 12:
        return True

    ignored_phrases = [
        "time allowed",
        "maximum marks",
        "total marks",
        "subject:",
        "practice year:",
        "all questions are compulsory",
        "attempt any",
        "attempt all",
        "answer any",
        "answer all",
        "instructions to candidates",
        "section a",
        "section b",
        "section c",
        "question paper",
        "roll number",
        "write your answers",
        "figures to the right",
        "draw neat diagrams",
        "marks for each question",
        "practice paper created",
    ]

    if any(phrase in cleaned for phrase in ignored_phrases):
        return True

    if re.fullmatch(r"[\W\d_]+", cleaned):
        return True

    return False


def split_into_questions(text):
    """
    Split extracted PDF text into likely questions.
    This works best when questions are separated by line breaks
    or start with question numbers.
    """
    text = text.replace("\r", "\n")

    # Put numbered questions on separate lines.
    text = re.sub(
        r"(?<!\n)\s+(?=(?:Q(?:uestion)?\s*)?\d{1,2}\s*[.)])",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    questions = []

    for line in lines:
        line = re.sub(
            r"^(?:Q(?:uestion)?\s*)?\d{1,2}\s*[.)]\s*",
            "",
            line,
            flags=re.IGNORECASE,
        )

        line = re.sub(r"\s+", " ", line).strip()

        if is_instruction_or_heading(line):
            continue

        # Remove obvious page-only remnants.
        if len(line.split()) < 3:
            continue

        questions.append(line)

    return questions


@st.cache_data(show_spinner=False)
def extract_pdf_questions(pdf_path, file_name):
    """Extract likely questions from a text-based PDF."""
    records = []

    try:
        reader = PdfReader(str(pdf_path))

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            questions = split_into_questions(text)

            for question in questions:
                records.append({
                    "Paper": file_name,
                    "Year": year_from_filename(file_name),
                    "Page": page_number,
                    "Question": question,
                    "Normalized": normalize_question(question),
                    "Marks": get_marks(question),
                    "Topic List": find_topics(question),
                })

    except Exception as error:
        st.warning(f"Could not read {file_name}: {error}")

    return records


# --------------------------------------------------
# LOAD PAPERS
# --------------------------------------------------
pdf_files = sorted(PAPER_DIR.glob("*.pdf"))

if not pdf_files:
    st.warning(
        f"No PDF files found in `{PAPER_DIR}`. "
        "Put your question-paper PDFs inside the Question_papers folder."
    )
    st.stop()

all_records = []

with st.spinner("Reading question papers..."):
    for pdf_file in pdf_files:
        all_records.extend(
            extract_pdf_questions(pdf_file, pdf_file.name)
        )

if not all_records:
    st.error(
        "No questions could be extracted. "
        "Check whether the PDFs contain selectable text. "
        "Scanned PDFs may require OCR."
    )
    st.stop()

df = pd.DataFrame(all_records)

# Remove repeated extraction of the same question within one paper,
# but preserve the same question when it occurs in another paper.
df = df.drop_duplicates(
    subset=["Paper", "Normalized"],
    keep="first"
).reset_index(drop=True)

# Ensure all questions have a valid topic list.
df["Topic List"] = df["Topic List"].apply(
    lambda value: value if isinstance(value, list) else ["Unclassified"]
)

df["Topics"] = df["Topic List"].apply(lambda topics: ", ".join(topics))


# --------------------------------------------------
# BUILD TOPIC ANALYSIS
# --------------------------------------------------
topic_counts = Counter()
topic_marks = Counter()
topic_papers = defaultdict(set)
topic_years = defaultdict(set)
topic_question_texts = defaultdict(set)
topic_known_marks_count = Counter()

for _, row in df.iterrows():
    for topic in row["Topic List"]:
        topic_counts[topic] += 1
        topic_papers[topic].add(row["Paper"])
        topic_question_texts[topic].add(row["Normalized"])

        if row["Year"] != "Unknown":
            topic_years[topic].add(row["Year"])

        if pd.notna(row["Marks"]):
            topic_marks[topic] += int(row["Marks"])
            topic_known_marks_count[topic] += 1


total_identified_marks = sum(topic_marks.values())
total_questions = len(df)
unique_question_count = df["Normalized"].nunique()

topic_rows = []

for topic, count in topic_counts.items():
    marks = topic_marks[topic]

    if total_identified_marks > 0:
        marks_weightage = round(
            marks / total_identified_marks * 100, 2
        )
    else:
        marks_weightage = 0.0

    # Heuristic score, not a guarantee of exam appearance.
    priority_score = count * 2 + marks

    if priority_score >= 20:
        priority = "Study First"
    elif priority_score >= 10:
        priority = "Study Next"
    else:
        priority = "Revise Later"

    if count >= 3 and marks >= 10:
        reason = (
            f"Appears {count} times and has {marks} identified marks; "
            "review this topic early."
        )
    elif count >= 2:
        reason = (
            f"Appears {count} times across the extracted questions; "
            "practice it and review the examples."
        )
    elif marks >= 10:
        reason = (
            f"Has {marks} identified marks; "
            "review the relevant concepts and practice questions."
        )
    else:
        reason = (
            "Fewer occurrences in these papers; "
            "revise after higher-priority topics."
        )

    # Coverage indicator: proportion of unique extracted questions
    # mapped to this topic. It is NOT a calibrated probability.
    confidence = (
        len(topic_question_texts[topic]) / unique_question_count * 100
        if unique_question_count else 0
    )

    topic_rows.append({
        "Topic": topic,
        "Question Count": count,
        "Identified Marks": marks,
        "Marks Weightage (%)": marks_weightage,
        "Years Seen": ", ".join(sorted(topic_years[topic])),
        "Papers Seen": len(topic_papers[topic]),
        "Confidence (%)": round(confidence, 1),
        "Priority Score": priority_score,
        "Priority": priority,
        "Reason": reason,
    })

topic_df = pd.DataFrame(topic_rows)

priority_order = {
    "Study First": 0,
    "Study Next": 1,
    "Revise Later": 2,
}

topic_df["_Priority Order"] = topic_df["Priority"].map(priority_order)

topic_df = topic_df.sort_values(
    by=["_Priority Order", "Priority Score", "Question Count"],
    ascending=[True, False, False],
).drop(columns=["_Priority Order"]).reset_index(drop=True)


# --------------------------------------------------
# TOP SUMMARY
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("PDF Papers", len(pdf_files))
col2.metric("Extracted Questions", total_questions)
col3.metric("Topics Identified", len(topic_counts))
col4.metric("Identified Marks", total_identified_marks)

st.info(
    "Note: results depend on the text extracted from your PDFs. "
    "Marks weightage uses only questions with identifiable marks. "
    "Priority scores are heuristic study guidance, not exam predictions."
)


# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Topic Priority",
    "📝 All Questions",
    "🔁 Repeated Questions",
    "📈 Year-wise Trends",
])


# --------------------------------------------------
# TAB 1: TOPIC PRIORITY + MARKS WEIGHTAGE
# --------------------------------------------------
with tab1:
    st.subheader("Topic-wise Marks Weightage")

    if total_identified_marks == 0:
        st.warning(
            "No question marks could be identified. "
            "Add marks to the question text or check the PDF formatting."
        )
    else:
        chart_df = topic_df[
            topic_df["Identified Marks"] > 0
        ].sort_values("Marks Weightage (%)", ascending=False)

        st.bar_chart(
            chart_df.set_index("Topic")["Marks Weightage (%)"]
        )

    st.subheader("Study Priority List")

    first_topics = topic_df[
        topic_df["Priority"] == "Study First"
    ]
    next_topics = topic_df[
        topic_df["Priority"] == "Study Next"
    ]
    later_topics = topic_df[
        topic_df["Priority"] == "Revise Later"
    ]

    with st.expander(
        f"🔴 Study First ({len(first_topics)} topics)",
        expanded=True
    ):
        if first_topics.empty:
            st.write("No topics currently fall in this group.")
        else:
            for _, row in first_topics.iterrows():
                st.markdown(
                    f"**{row['Topic']}** — Score: {row['Priority Score']}  \n"
                    f"Questions: {row['Question Count']} | "
                    f"Identified marks: {row['Identified Marks']} | "
                    f"Weightage: {row['Marks Weightage (%)']}%  \n"
                    f"Reason: {row['Reason']}"
                )

    with st.expander(
        f"🟠 Study Next ({len(next_topics)} topics)"
    ):
        if next_topics.empty:
            st.write("No topics currently fall in this group.")
        else:
            for _, row in next_topics.iterrows():
                st.markdown(
                    f"**{row['Topic']}** — Score: {row['Priority Score']}  \n"
                    f"Questions: {row['Question Count']} | "
                    f"Identified marks: {row['Identified Marks']} | "
                    f"Weightage: {row['Marks Weightage (%)']}%  \n"
                    f"Reason: {row['Reason']}"
                )

    with st.expander(
        f"🟢 Revise Later ({len(later_topics)} topics)"
    ):
        if later_topics.empty:
            st.write("No topics currently fall in this group.")
        else:
            for _, row in later_topics.iterrows():
                st.markdown(
                    f"**{row['Topic']}** — Score: {row['Priority Score']}  \n"
                    f"Questions: {row['Question Count']} | "
                    f"Identified marks: {row['Identified Marks']} | "
                    f"Weightage: {row['Marks Weightage (%)']}%  \n"
                    f"Reason: {row['Reason']}"
                )

    st.subheader("Complete Topic Analysis")

    st.dataframe(
        topic_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Topic Analysis CSV",
        data=topic_df.to_csv(index=False).encode("utf-8"),
        file_name="topic_analysis.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# TAB 2: ALL QUESTIONS
# --------------------------------------------------
with tab2:
    st.subheader("All Extracted Questions")

    available_papers = sorted(df["Paper"].unique().tolist())

    selected_papers = st.multiselect(
        "Filter by paper",
        options=available_papers,
        default=available_papers,
    )

    question_view = df[
        df["Paper"].isin(selected_papers)
    ][[
        "Year",
        "Paper",
        "Page",
        "Question",
        "Topics",
        "Marks",
    ]].copy()

    st.dataframe(
        question_view,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download All Questions CSV",
        data=question_view.to_csv(index=False).encode("utf-8"),
        file_name="all_questions.csv",
        mime="text/csv",
    )



# --------------------------------------------------
# TAB 3: EXACT + SIMILAR QUESTIONS
# --------------------------------------------------
with tab3:
    st.subheader("Repeated and Similar Questions")

    from difflib import SequenceMatcher

    exact_groups = df.groupby("Normalized")["Paper"].nunique()
    exact_keys = exact_groups[exact_groups >= 2].index

    exact_df = df[df["Normalized"].isin(exact_keys)].copy()

    st.markdown("### Exact Repeated Questions")

    if exact_df.empty:
        st.info("No exact repeated questions found.")
    else:
        st.dataframe(
            exact_df[[
                "Year", "Paper", "Question", "Topics", "Marks"
            ]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("### Similar Questions")

    # Compare questions from different papers.
    rows = df.to_dict("records")
    similar_pairs = []
    seen_pairs = set()

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a = rows[i]
            b = rows[j]

            if a["Paper"] == b["Paper"]:
                continue

            if a["Normalized"] == b["Normalized"]:
                continue

            similarity = SequenceMatcher(
                None,
                a["Normalized"],
                b["Normalized"]
            ).ratio()

            common_topics = set(a["Topic List"]) & set(b["Topic List"])

            # Similar wording OR a shared mapped topic.
            
            if common_topics and similarity >= 0.50:

                pair_key = tuple(sorted([
                    a["Paper"] + "|" + a["Normalized"],
                    b["Paper"] + "|" + b["Normalized"]
                ]))

                if pair_key in seen_pairs:
                    continue

                seen_pairs.add(pair_key)

                similar_pairs.append({
                    "Similarity (%)": round(similarity * 100, 1),
                    "Year 1": a["Year"],
                    "Paper 1": a["Paper"],
                    "Question 1": a["Question"],
                    "Year 2": b["Year"],
                    "Paper 2": b["Paper"],
                    "Question 2": b["Question"],
                    "Common Topics": ", ".join(sorted(common_topics))
                    if common_topics else "No common mapped topic",
                })

    if similar_pairs:
        similar_df = pd.DataFrame(similar_pairs)
        similar_df = similar_df.sort_values(
            "Similarity (%)", ascending=False
        )

        st.dataframe(
            similar_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Similar Questions CSV",
            data=similar_df.to_csv(index=False).encode("utf-8"),
            file_name="similar_questions.csv",
            mime="text/csv",
        )
    else:
        st.info("No similar questions detected.")



# --------------------------------------------------
# TAB 4: YEAR-WISE TRENDS
# --------------------------------------------------
with tab4:
    st.subheader("Year-wise Topic Trends")

    known_year_df = df[df["Year"] != "Unknown"].copy()

    if known_year_df.empty:
        st.info(
            "No years detected. Include a year in each PDF filename, "
            "for example paper_2024.pdf."
        )
    else:
        trend_rows = []

        for _, row in known_year_df.iterrows():
            for topic in row["Topic List"]:
                trend_rows.append({
                    "Year": row["Year"],
                    "Topic": topic,
                    "Question Count": 1,
                    "Marks": row["Marks"] if pd.notna(row["Marks"]) else 0,
                })

        trend_df = pd.DataFrame(trend_rows)

        year_topic_counts = trend_df.pivot_table(
            index="Year",
            columns="Topic",
            values="Question Count",
            aggfunc="sum",
            fill_value=0,
        )

        st.markdown("**Questions by year and topic**")
        st.bar_chart(year_topic_counts)

        year_marks = trend_df.groupby("Year")["Marks"].sum()

        st.markdown("**Identified marks by year**")
        st.bar_chart(year_marks)

        st.dataframe(
            year_topic_counts.reset_index(),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Year-wise Trends CSV",
            data=year_topic_counts.reset_index().to_csv(
                index=False
            ).encode("utf-8"),
            file_name="year_wise_trends.csv",
            mime="text/csv",
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "Exam Intelligence Assistant | Prototype for past-paper analysis. "
    "Validate topic mapping against your official syllabus."
)
