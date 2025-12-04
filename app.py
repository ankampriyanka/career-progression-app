import os
from io import StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from transformers import pipeline

# ------------------ Streamlit Page Config ------------------ #
st.set_page_config(
    page_title="Team Career Progression Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------ THEME SETUP ------------------ #

THEME_COLORS = {
    "Corporate Blue": {"bg": "#f0f4ff", "primary": "#1a73e8", "accent": "#0b3d91"},
    "Consulting Grey": {"bg": "#f7f7f7", "primary": "#4a4a4a", "accent": "#808080"},
    "Tech Gradient": {"bg": "#f5f3ff", "primary": "#6a11cb", "accent": "#2575fc"},
    "Healthcare Green": {"bg": "#e8fff1", "primary": "#2e8b57", "accent": "#66bb6a"},
    "FinTech Neon": {"bg": "#f0fdf4", "primary": "#00bcd4", "accent": "#0284c7"},
    "Education Warm": {"bg": "#fff7ed", "primary": "#fb923c", "accent": "#ea580c"},
    "PeopleOps Pastel": {"bg": "#fdf2f8", "primary": "#ec4899", "accent": "#db2777"},
}


def apply_theme(theme_choice: str):
    colors = THEME_COLORS[theme_choice]
    st.markdown(
        f"""
    <style>
    body {{
        background: {colors["bg"]} !important;
    }}
    [data-testid="stHeader"] {{
        background-color: transparent;
    }}
    h1, h2, h3 {{
        color: {colors["primary"]} !important;
    }}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )
    return colors


# ------------------ LLM LOADING ------------------ #


@st.cache_resource
def load_llm():
    """
    Load a small, instruction-tuned model.
    FLAN-T5-small is light enough for CPU Spaces.
    """
    try:
        generator = pipeline(
            "text2text-generation",
            model="google/flan-t5-small",
        )
        return generator
    except Exception as e:
        st.warning(
            "⚠️ Could not load LLM (FLAN-T5). "
            "Falling back to rule-based recommendations only.\n\n"
            f"Details: {e}"
        )
        return None


@st.cache_data
def generate_llm_plan_cached(profile_text: str, industry: str):
    """
    Cached wrapper so we don’t call the LLM repeatedly
    for the same profile.
    """
    llm = load_llm()
    if llm is None:
        return "LLM not available in this environment. Using rule-based recommendations only."

    prompt = (
        "You are a career coach helping a manager plan growth for their team member.\n\n"
        "Given the profile below and the industry, write:\n"
        "1) A short narrative summary of the person's current strengths and gaps.\n"
        "2) A concrete 30-60-90 day development plan.\n"
        "Use concise bullet points. Avoid generic advice.\n\n"
        f"Industry: {industry}\n"
        f"Profile:\n{profile_text}\n\n"
        "Answer:"
    )

    try:
        out = llm(prompt, max_new_tokens=220, do_sample=False)
        return out[0]["generated_text"].strip()
    except Exception as e:
        return f"LLM generation failed: {e}"


# ------------------ SCORING & RULE-BASED LOGIC ------------------ #


def compute_readiness_score(row: pd.Series) -> float:
    years_norm = min(row.get("YearsExperience", 0), 10) / 10 * 5
    tech = row.get("TechSkillRating", 0)
    soft = row.get("SoftSkillRating", 0)
    perf = row.get("PerformanceRating", 0)
    leadership = (
        5
        if str(row.get("LeadershipInterest", "")).strip().lower() in ["yes", "y"]
        else 2
    )

    score_5 = (
        0.3 * years_norm
        + 0.2 * tech
        + 0.2 * soft
        + 0.2 * perf
        + 0.1 * leadership
    )
    return round(score_5 / 5 * 100, 1)


def suggest_next_role_and_actions(row: pd.Series, industry_choice: str):
    score = row["ReadinessScore"]
    domain = str(row.get("DomainInterest", "")).lower()
    goal = str(row.get("CareerGoal", "")).lower()
    leadership = (
        str(row.get("LeadershipInterest", "")).strip().lower() in ["yes", "y"]
    )

    # ----- Next Role -----
    if score >= 80:
        if leadership:
            next_role = "Team Lead / Scrum Master / SAFe Team Coach"
        else:
            next_role = f"Senior {row.get('CurrentRole', 'Professional')}"
    elif 60 <= score < 80:
        next_role = f"Mid-level {row.get('CurrentRole', 'Professional')}"
    else:
        next_role = "Upskill & Consolidate Current Role"

    actions = []

    # ----- Generic banded actions -----
    if score >= 80:
        actions.extend(
            [
                "Take stretch assignments and mentor junior team members.",
                "Lead at least one initiative end-to-end this quarter.",
                "Show decision-making in cross-team topics.",
            ]
        )
    elif 60 <= score < 80:
        actions.extend(
            [
                "Strengthen 1–2 core competencies to reach 4+/5.",
                "Request ownership of a module or feature area.",
            ]
        )
    else:
        actions.extend(
            [
                "Focus on delivery consistency and quality.",
                "Pair with a mentor and set up regular feedback sessions.",
            ]
        )

    # ----- Domain-specific -----
    if "data" in domain or "analytics" in domain:
        actions.extend(
            [
                "Pursue SQL, Power BI, or Tableau certifications.",
                "Deliver at least one analytics dashboard or report.",
                "Practice data storytelling for business stakeholders.",
            ]
        )

    if "cloud" in domain or any(k in domain for k in ["aws", "azure", "gcp"]):
        actions.extend(
            [
                "Target an associate-level cloud certification.",
                "Learn CI/CD and infrastructure fundamentals.",
                "Contribute to cloud migration or automation tasks.",
            ]
        )

    if "ai" in domain or "ml" in domain or "machine learning" in domain:
        actions.extend(
            [
                "Complete an applied ML course and build 1–2 small projects.",
                "Experiment with LLMs to automate team workflows.",
                "Understand basic MLOps concepts.",
            ]
        )

    if "product" in domain or "ba" in domain or "business analysis" in domain:
        actions.extend(
            [
                "Practice writing crisp user stories and acceptance criteria.",
                "Shadow product discovery or customer calls.",
                "Apply prioritisation frameworks like WSJF or RICE.",
            ]
        )

    if "qa" in domain or "test" in domain:
        actions.extend(
            [
                "Learn an automation framework (Selenium, Cypress, Playwright).",
                "Own regression suites and test strategy for a module.",
                "Strengthen API testing skills.",
            ]
        )

    if "architecture" in domain or "design" in domain:
        actions.extend(
            [
                "Study system design patterns and trade-offs.",
                "Lead technical design for at least one feature.",
                "Deepen understanding of non-functional requirements.",
            ]
        )

    if "support" in domain or "customer" in domain:
        actions.extend(
            [
                "Deepen product & troubleshooting knowledge.",
                "Contribute to knowledge base and runbooks.",
                "Participate in customer feedback analysis.",
            ]
        )

    # ----- Agile / SAFe ----- #
    if leadership:
        actions.extend(
            [
                "Facilitate standups or retrospectives under guidance.",
                "Take responsibility for risk and dependency updates.",
            ]
        )

    if any(k in domain for k in ["agile", "scrum", "safe", "kanban", "lean"]):
        actions.extend(
            [
                "Participate actively in PI planning preparation.",
                "Improve backlog refinement and estimation facilitation.",
                "Track team health metrics (velocity, WIP, predictability).",
                "Consider SAFe Scrum Master or POPM certification.",
            ]
        )

    # ----- Goal-specific -----
    if "manager" in goal or "lead" in goal:
        actions.extend(
            [
                "Invest in stakeholder communication and conflict management.",
                "Lead at least one improvement initiative for the team.",
            ]
        )

    if "architect" in goal:
        actions.extend(
            [
                "Own design for complex features or components.",
                "Mentor others on design principles.",
            ]
        )

    if "scrum" in goal or "agile" in goal:
        actions.extend(
            [
                "Run retrospectives end-to-end with clear outcomes.",
                "Drive actions from retros back into the backlog.",
            ]
        )

    # ----- Industry-specific -----
    if industry_choice == "Technology":
        actions.extend(
            [
                "Stay current with engineering best practices and new tools.",
                "Increase exposure to system design and scalability topics.",
            ]
        )
    elif industry_choice == "Consulting":
        actions.extend(
            [
                "Shape problem statements and hypotheses for clients.",
                "Practice slide-making and structured storylines.",
            ]
        )
    elif industry_choice == "Banking / FinTech":
        actions.extend(
            [
                "Understand key regulatory concepts (AML, KYC, PCI-DSS).",
                "Strengthen domain skills in payments, lending, or risk.",
            ]
        )
    elif industry_choice == "Healthcare":
        actions.extend(
            [
                "Learn key healthcare processes and data privacy needs.",
                "Understand EHR/EMR workflows and quality of care metrics.",
            ]
        )
    elif industry_choice == "Retail / E-commerce":
        actions.extend(
            [
                "Use customer analytics to inform feature ideas.",
                "Understand funnel metrics, A/B testing, and experimentation.",
            ]
        )
    elif industry_choice == "Manufacturing":
        actions.extend(
            [
                "Learn basics of supply chain and production workflows.",
                "Identify automation opportunities in existing processes.",
            ]
        )
    elif industry_choice == "Education":
        actions.extend(
            [
                "Apply learning design principles to any internal training.",
                "Help create or improve onboarding materials.",
            ]
        )
    elif industry_choice == "Public Sector/Government":
        actions.extend(
            [
                "Understand procurement and governance processes.",
                "Document decisions clearly for audit and traceability.",
            ]
        )

    actions = list(dict.fromkeys(actions))  # dedupe, preserve order
    return next_role, actions


def build_recommendations(df: pd.DataFrame, industry_choice: str) -> pd.DataFrame:
    df = df.copy()
    df["ReadinessScore"] = df.apply(compute_readiness_score, axis=1)

    next_roles = []
    rule_actions = []
    llm_plans = []

    for _, row in df.iterrows():
        next_role, actions = suggest_next_role_and_actions(row, industry_choice)
        next_roles.append(next_role)
        rule_actions.append("• " + "\n• ".join(actions))

        profile_text = (
            f"Name: {row.get('Name')}\n"
            f"Current role: {row.get('CurrentRole')}\n"
            f"Years of experience: {row.get('YearsExperience')}\n"
            f"Tech skill rating (1-5): {row.get('TechSkillRating')}\n"
            f"Soft skill rating (1-5): {row.get('SoftSkillRating')}\n"
            f"Performance rating (1-5): {row.get('PerformanceRating')}\n"
            f"Leadership interest: {row.get('LeadershipInterest')}\n"
            f"Domain interest: {row.get('DomainInterest')}\n"
            f"Career goal: {row.get('CareerGoal')}\n"
            f"Readiness score (0-100): {row.get('ReadinessScore')}\n"
            f"Suggested next role (rule-based): {next_role}"
        )

        llm_text = generate_llm_plan_cached(profile_text, industry_choice)
        llm_plans.append(llm_text)

    df["SuggestedNextRole"] = next_roles
    df["RecommendedActions"] = rule_actions
    df["LLMPlan"] = llm_plans
    return df


# ------------------ SIDEBAR CONTROLS ------------------ #

with st.sidebar:
    st.header("🎨 UI & Context Settings")

    theme_choice = st.selectbox(
        "Choose a Theme",
        list(THEME_COLORS.keys()),
        index=0,
    )
    colors = apply_theme(theme_choice)

    industry_choice = st.selectbox(
        "Select Industry",
        [
            "Technology",
            "Consulting",
            "Banking / FinTech",
            "Healthcare",
            "Retail / E-commerce",
            "Manufacturing",
            "Education",
            "Public Sector/Government",
        ],
        index=0,
    )

    st.markdown("---")
    st.header("📥 Input Options")

    uploaded_file = st.file_uploader("Upload team data (CSV)", type=["csv"])

    st.markdown(
        """
**Expected columns (case-sensitive):**

- `Name`
- `CurrentRole`
- `YearsExperience`
- `TechSkillRating` (1–5)
- `SoftSkillRating` (1–5)
- `PerformanceRating` (1–5)
- `LeadershipInterest` (Yes/No)
- `DomainInterest`
- `CareerGoal`
"""
    )

    use_sample = st.checkbox(
        "Use sample data",
        value=uploaded_file is None,
        help="Tick this if you want to see a pre-filled example.",
    )

# ------------------ DATA LOADING ------------------ #

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
elif use_sample:
    sample_path = os.path.join("sample_data", "team_members_sample.csv")
    if os.path.exists(sample_path):
        df_raw = pd.read_csv(sample_path)
    else:
        st.error(
            f"Sample file not found at `{sample_path}`. "
            "Please upload a CSV or add the sample_data folder."
        )
        st.stop()
else:
    st.info("Upload a CSV or tick 'Use sample data' in the sidebar to begin.")
    st.stop()

# ------------------ MAIN LAYOUT ------------------ #

st.title("🧭 Team Career Progression Assistant")
st.caption(
    "This app helps a **Program Manager / People Lead** analyse team career readiness "
    "and generate next-role recommendations & 30–60–90 day plans."
)

# Input data view
st.subheader("📥 Input Data")
st.dataframe(df_raw, use_container_width=True)

# Build recommendations (rule-based + LLM)
df = build_recommendations(df_raw, industry_choice)

# Recommendations table
st.subheader("📋 Recommendations by Team Member")
st.dataframe(
    df[
        [
            "Name",
            "CurrentRole",
            "YearsExperience",
            "ReadinessScore",
            "SuggestedNextRole",
        ]
    ],
    use_container_width=True,
)

# Detailed per-member view with LLM output
st.markdown("---")
st.subheader("🧠 Detailed View & LLM 30–60–90 Day Plan")

for _, row in df.iterrows():
    with st.expander(f"{row['Name']} — {row['SuggestedNextRole']}"):
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("**Rule-based recommended actions:**")
            st.markdown(row["RecommendedActions"])
        with col_b:
            st.markdown("**LLM-generated narrative & 30–60–90 day plan:**")
            st.markdown(row["LLMPlan"])

# Dashboard visuals
st.markdown("---")
st.header("📊 Team Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Readiness Score by Member")
    fig_scores = px.bar(
        df,
        x="Name",
        y="ReadinessScore",
        color="SuggestedNextRole",
        labels={"ReadinessScore": "Readiness Score (0–100)"},
        text="ReadinessScore",
    )
    fig_scores.update_traces(textposition="outside")
    fig_scores.update_layout(
        yaxis_range=[0, 110],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_scores, use_container_width=True)

with col2:
    st.subheader("Role Pipeline Overview")
    role_counts = df["SuggestedNextRole"].value_counts().reset_index()
    role_counts.columns = ["SuggestedNextRole", "Count"]
    fig_roles = px.pie(
        role_counts,
        names="SuggestedNextRole",
        values="Count",
        hole=0.4,
    )
    fig_roles.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_roles, use_container_width=True)

# Download
st.markdown("---")
st.header("📥 Download Results")

csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Download recommendations (with LLM plan) as CSV",
    data=csv_buffer.getvalue(),
    file_name="career_recommendations_with_llm.csv",
    mime="text/csv",
)

st.caption(
    "Note: This tool provides *decision support* for people leaders. "
    "Always combine insights with your own judgment and HR guidelines."
)
