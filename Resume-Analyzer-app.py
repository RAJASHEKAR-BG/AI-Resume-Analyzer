import streamlit as st
import PyPDF2
import openai
import os
import json

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .main-header {font-size:2.5rem; font-weight:700; color:#4F46E5;}
    .score-card {background:#F0FDF4; border-left:4px solid #22C55E; padding:1rem; border-radius:8px;}
    .warning-card {background:#FFF7ED; border-left:4px solid #F59E0B; padding:1rem; border-radius:8px;}
    .danger-card {background:#FEF2F2; border-left:4px solid #EF4444; padding:1rem; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">📄 AI Resume Analyzer</p>', unsafe_allow_html=True)
st.markdown("Upload your resume and get **AI-powered feedback** to land your dream job.")
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    target_role = st.text_input("Target Job Role", placeholder="e.g. Data Scientist")
    experience_level = st.selectbox("Experience Level", ["Entry", "Mid", "Senior"])
    analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)

# ── Helper functions ───────────────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def analyze_resume_with_llm(resume_text: str, role: str, level: str, api_key: str) -> dict:
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are an expert HR consultant and career coach. Analyze the following resume for a {level}-level {role} position.

RESUME:
{resume_text[:4000]}

Provide a detailed analysis in the following JSON format:
{{
  "overall_score": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
  "missing_keywords": ["<keyword 1>", "<keyword 2>", "<keyword 3>"],
  "ats_score": <integer 0-100>,
  "recommendations": ["<action 1>", "<action 2>", "<action 3>", "<action 4>"],
  "section_scores": {{
    "experience": <0-100>,
    "skills": <0-100>,
    "education": <0-100>,
    "formatting": <0-100>
  }}
}}
Respond ONLY with valid JSON.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)

def score_color(score):
    if score >= 75:
        return "score-card"
    elif score >= 50:
        return "warning-card"
    return "danger-card"

# ── Main UI ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("📎 Upload Resume (PDF)", type=["pdf"])

if uploaded_file:
    st.success(f"✅ Uploaded: **{uploaded_file.name}**")
    with st.expander("📖 Preview Extracted Text"):
        raw_text = extract_text_from_pdf(uploaded_file)
        st.text_area("", raw_text[:2000] + "..." if len(raw_text) > 2000 else raw_text, height=200)

if analyze_btn:
    if not uploaded_file:
        st.warning("Please upload a resume PDF first.")
    elif not api_key:
        st.warning("Please enter your OpenAI API key.")
    elif not target_role:
        st.warning("Please enter a target job role.")
    else:
        with st.spinner("🤖 AI is analyzing your resume..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            result = analyze_resume_with_llm(raw_text, target_role, experience_level, api_key)

        st.divider()
        st.subheader("📊 Analysis Results")

        # Overall scores
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Score", f"{result['overall_score']}/100")
        col2.metric("ATS Score", f"{result['ats_score']}/100")
        col3.metric("Role Match", f"{target_role} ({experience_level})")

        st.markdown(f"**Summary:** {result['summary']}")
        st.divider()

        # Section scores
        st.subheader("📈 Section Breakdown")
        cols = st.columns(4)
        for i, (section, score) in enumerate(result["section_scores"].items()):
            cols[i].metric(section.title(), f"{score}/100")

        st.divider()

        # Strengths & Weaknesses
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("✅ Strengths")
            for s in result["strengths"]:
                st.markdown(f'<div class="score-card">✔ {s}</div><br>', unsafe_allow_html=True)

        with col_b:
            st.subheader("⚠️ Weaknesses")
            for w in result["weaknesses"]:
                st.markdown(f'<div class="warning-card">⚠ {w}</div><br>', unsafe_allow_html=True)

        st.divider()

        # Missing keywords
        st.subheader("🔑 Missing Keywords")
        st.markdown(" ".join([f"`{kw}`" for kw in result["missing_keywords"]]))

        # Recommendations
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(result["recommendations"], 1):
            st.markdown(f"**{i}.** {rec}")
