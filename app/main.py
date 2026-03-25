import streamlit as st
from ingest import extract_text_from_pdf, chunk_text
from rag import (
    get_client,
    create_index_if_not_exists,
    store_chunks,
    search_chunks,
    generate_simple_answer,
    check_skill_in_resume,
    analyze_resume_vs_jd
)

st.set_page_config(page_title="Resume JD Matcher", layout="wide")

st.title("AI Resume vs JD Matcher using Endee")
st.write("Upload a Resume PDF and a Job Description PDF, then ask questions.")

resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"], key="resume")
jd_file = st.file_uploader("Upload Job Description PDF", type=["pdf"], key="jd")

if "indexed" not in st.session_state:
    st.session_state.indexed = False

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

if st.button("Process and Index Documents"):
    if resume_file and jd_file:
        with st.spinner("Extracting text and indexing in Endee..."):
            resume_text = extract_text_from_pdf(resume_file)
            jd_text = extract_text_from_pdf(jd_file)

            st.session_state.resume_text = resume_text
            st.session_state.jd_text = jd_text

            resume_chunks = chunk_text(resume_text)
            jd_chunks = chunk_text(jd_text)

            client = get_client()
            index = create_index_if_not_exists(client)

            store_chunks(index, resume_chunks, "resume")
            store_chunks(index, jd_chunks, "jd")

            st.session_state.indexed = True

        st.success("Documents indexed successfully in Endee.")
    else:
        st.warning("Please upload both Resume and JD PDFs.")

question = st.text_input(
    "Ask a question",
    placeholder="Example: What skills are missing, or Is Java present in the resume?"
)

if st.button("Search / Analyze"):
    if not st.session_state.indexed:
        st.warning("Please process and index the documents first.")
    elif question:
        q = question.lower().strip()

        # exact yes/no skill check
        skill_result = check_skill_in_resume(question, st.session_state.resume_text)

        if any(x in q for x in ["missing skill", "skills are missing", "missing skills", "match percentage", "matching percentage", "how much percentage", "match score", "jd and resume"]):
            analysis = analyze_resume_vs_jd(
                st.session_state.resume_text,
                st.session_state.jd_text
            )

            st.subheader("Resume vs JD Analysis")
            st.metric("Match Percentage", f"{analysis['match_percentage']}%")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Matched Skills")
                if analysis["matched_skills"]:
                    for skill in analysis["matched_skills"]:
                        st.write(f"✅ {skill}")
                else:
                    st.write("No matched skills found.")

            with col2:
                st.markdown("### Missing Skills")
                if analysis["missing_skills"]:
                    for skill in analysis["missing_skills"]:
                        st.write(f"❌ {skill}")
                else:
                    st.write("No missing skills found.")

            st.markdown("### Resume Skills")
            if analysis["resume_skills"]:
                st.write(", ".join(analysis["resume_skills"]))
            else:
                st.write("No resume skills found.")

            st.markdown("### JD Skills")
            if analysis["jd_skills"]:
                st.write(", ".join(analysis["jd_skills"]))
            else:
                st.write("No JD skills found.")

        elif skill_result is not None:
            st.subheader("Exact Answer")
            st.success(skill_result["answer"])
            st.write(f"**Skill Checked:** {skill_result['skill']}")
            if skill_result["matched_keyword"]:
                st.write(f"**Matched Keyword:** {skill_result['matched_keyword']}")
            else:
                st.write("**Matched Keyword:** Not found")

        else:
            with st.spinner("Searching relevant chunks..."):
                client = get_client()
                index = create_index_if_not_exists(client)

                results = search_chunks(index, question, top_k=5)
                answer = generate_simple_answer(results, question)

            st.subheader("Answer")
            st.write(answer)

            st.subheader("Top Retrieved Chunks")
            for i, r in enumerate(results, 1):
                st.markdown(f"**Result {i}**")
                st.write(r["meta"].get("text", ""))
                st.write(f"Source: {r['meta'].get('source', 'unknown')}")
                st.write("---")
    else:
        st.warning("Please enter a question.")