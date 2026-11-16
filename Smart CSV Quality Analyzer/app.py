
import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Smart CSV Text Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("Smart CSV Text Analyzer")

st.write(
    "Upload a text-based CSV file to identify categories, "
    "review potentially ambiguous statements, and download results."
)

# Category rules are maintained internally
RULES = [
    ("female", "Gender"),
    ("male", "Gender"),
    ("other", "Gender"),
    ("gender", "Gender"),

    ("high", "Level"),
    ("low", "Level"),

    ("stress", "Wellbeing"),
    ("stressed", "Wellbeing"),
    ("anxious", "Wellbeing"),
    ("worried", "Wellbeing"),
    ("overwhelmed", "Wellbeing"),
    ("sad", "Wellbeing"),
    ("tired", "Wellbeing"),
    ("calm", "Wellbeing"),

    ("quickly", "Ambiguous"),
    ("efficiently", "Ambiguous"),
    ("soon", "Ambiguous"),
    ("smoothly", "Ambiguous"),
    ("promptly", "Ambiguous"),
    ("reasonable time", "Ambiguous"),
    ("relevant results", "Ambiguous"),

    ("shall", "Requirement"),
    ("must", "Requirement"),
    ("should", "Requirement")
]

# Phrases that may indicate vague requirements
VAGUE_PHRASES = [
    "quickly",
    "efficiently",
    "soon",
    "promptly",
    "smoothly",
    "user friendly",
    "high performance",
    "better experience",
    "reasonable time",
    "relevant results",
    "fast",
    "easy"
]

# Generic statements that may need more detail
INCOMPLETE_PHRASES = [
    "the system should process the information",
    "the application shall generate the report",
    "the website shall notify the user",
    "the system must handle errors",
    "the system shall provide access",
    "the system shall provide the feature",
    "the application shall generate the requested output"
]


def contains_phrase(text, phrase):
    pattern = (
        r"(?<!\w)"
        + re.escape(phrase.lower())
        + r"(?!\w)"
    )

    return re.search(pattern, text.lower()) is not None


def analyze_text(value):
    if pd.isna(value) or str(value).strip() == "":
        return {
            "Identified Category": "Empty",
            "Matched Terms": "",
            "Analysis Note": "No text provided"
        }

    text = str(value).lower()

    found_categories = []
    matched_terms = []

    # Match the predefined category rules
    for phrase, category in RULES:
        if contains_phrase(text, phrase):
            if category not in found_categories:
                found_categories.append(category)

            matched_terms.append(phrase)

    # Identify potentially ambiguous language
    vague_found = []

    for phrase in VAGUE_PHRASES:
        if contains_phrase(text, phrase):
            vague_found.append(phrase)

    if vague_found:
        if "Ambiguous" not in found_categories:
            found_categories.append("Ambiguous")

        matched_terms.extend(vague_found)

    # Flag selected generic statements for review
    incomplete_found = []

    for phrase in INCOMPLETE_PHRASES:
        if phrase in text:
            incomplete_found.append(phrase)

    if incomplete_found:
        if "Incomplete" not in found_categories:
            found_categories.append("Incomplete")

        matched_terms.extend(incomplete_found)

    # Prepare the result
    if found_categories:
        category_text = ", ".join(found_categories)
        note = "Matched predefined rules or review patterns"
    else:
        category_text = "Uncategorized"
        note = "No predefined pattern matched"

    return {
        "Identified Category": category_text,
        "Matched Terms": ", ".join(dict.fromkeys(matched_terms)),
        "Analysis Note": note
    }


# Upload a CSV file
uploaded_file = st.file_uploader(
    "Upload your CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        if len(df.columns) == 0:
            st.error("Your CSV file has no columns.")

        elif df.empty:
            st.warning("Your CSV file has no data rows.")

        else:
            st.subheader("CSV Preview")

            st.dataframe(
                df.head(10),
                use_container_width=True
            )

            # Let the user select the text column
            text_column = st.selectbox(
                "Select the column containing text",
                df.columns
            )

            expected_column = None

            if "expected_category" in df.columns:
                expected_column = "expected_category"

                st.info(
                    "Reference labels were found. "
                    "You can compare them with the analyzer's results."
                )

            if st.button("Analyze Text", type="primary"):
                results = []

                # Analyze each row
                for value in df[text_column]:
                    result = analyze_text(value)
                    results.append(result)

                # Add analysis results to the original data
                output = df.copy()

                output["Identified Category"] = [
                    result["Identified Category"]
                    for result in results
                ]

                output["Matched Terms"] = [
                    result["Matched Terms"]
                    for result in results
                ]

                output["Analysis Note"] = [
                    result["Analysis Note"]
                    for result in results
                ]

                st.subheader("Analysis Results")

                st.dataframe(
                    output,
                    use_container_width=True
                )

                # Category summary
                st.subheader("Category Summary")

                counts = (
                    output["Identified Category"]
                    .value_counts()
                    .reset_index()
                )

                counts.columns = ["Category", "Count"]

                st.dataframe(
                    counts,
                    use_container_width=True
                )

                # Download results
                csv_data = output.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="Download Analysis Results",
                    data=csv_data,
                    file_name="text_analysis_results.csv",
                    mime="text/csv"
                )

                # Optional comparison against reference labels
                if expected_column:
                    st.subheader("Reference Label Comparison")

                    predicted = (
                        output["Identified Category"]
                        .str.split(", ")
                        .apply(set)
                    )

                    expected = (
                        df[expected_column]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                    comparable = expected != ""

                    if comparable.any():
                        correct = 0
                        total = int(comparable.sum())

                        for index in df.index:
                            if not comparable.loc[index]:
                                continue

                            expected_label = expected.loc[index]
                            predicted_labels = predicted.loc[index]

                            if expected_label in predicted_labels:
                                correct += 1

                        st.write(
                            f"Expected category found in "
                            f"{correct} out of {total} labeled rows."
                        )

                        st.caption(
                            "This is a category-match check, not a "
                            "full machine-learning accuracy score. "
                            "A row may receive multiple categories."
                        )

    except Exception as error:
        st.error("Could not analyze this CSV file.")
        st.caption(str(error))

else:
    st.info("Upload a CSV file to get started.")








