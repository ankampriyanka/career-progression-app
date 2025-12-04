import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

st.set_page_config(
    page_title="Team Career Progression Assistant for a Program Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------- Helper functions ---------
def compute_readiness_score(row):
    # Normalise years of experience to 1–5 (cap at 10 years)
    years_norm = min(row.get("YearsExperience", 0), 10) / 10 * 5

    tech = row.get("TechSkillRating", 0)
    soft = row.get("SoftSkillRating", 0)
    perf = row.get("PerformanceRating", 0)
    leadership = 5 if str(row.get("LeadershipInterest", "")).strip().lower() in ["yes", "y"] else 2

    # Weighted score (0–5)
    score_5 = (
        0.3 * years_norm
        + 0.2 * tech
        + 0.2 * soft
        + 0.2 * perf
        + 0.1 * leadership
    )
    return round(score_5 / 5 * 100, 1)  # convert to 0–100


def suggest_next_role_and_actions(row):
    score = row["ReadinessScore"]
    domain = str(row.get("DomainInterest", "")).lower()
    goal = str(row.get("CareerGoal", "")).lower()
    leadership = str(row.get("LeadershipInterest", "")).strip().lower() in ["yes", "y"]

    # ------------------------
    # Next Role Suggestion
    # ------------------------
    if score >= 80:
        if leadership:
            next_role = "Team Lead / Scrum Master / SAFe Team Coach"
        else:
            next_role = f"Senior {row.get('CurrentRole', 'Professional')}"
    elif 60 <= score < 80:
        next_role = f"Mid-level {row.get('CurrentRole', 'Professional')}"
    else:
        next_role = "Upskill & Consolidate Current Role"

    # ------------------------
    # Base Action Recommendations
    # ------------------------
    actions = []

    if score >= 80:
        actions.append("Take stretch assignments and mentor junior team members.")
        actions.append("Lead an initiative end-to-end in the next quarter.")
        actions.append("Demonstrate decision-making in cross-functional areas.")
    elif 60 <= score < 80:
        actions.append("Strengthen 1–2 core competencies to reach 4+/5.")
        actions.append("Request ownership of modules or feature areas.")
    else:
        actions.append("Focus on consistency and delivery excellence.")
        actions.append("Engage with a mentor for monthly feedback cycles.")

    # ------------------------
    # Domain-Specific Recommendations (Expanded)
    # ------------------------

    # --- Data & Analytics ---
    if "data" in domain or "analytics" in domain:
        actions.extend([
            "Pursue certifications in SQL, Power BI, or Tableau.",
            "Contribute to small ETL / dashboard projects.",
            "Strengthen storytelling using data."
        ])

    # --- Cloud & DevOps ---
    if "cloud" in domain or "aws" in domain or "azure" in domain or "gcp" in domain:
        actions.extend([
            "Target AWS/Azure/GCP associate-level certifications.",
            "Learn CI/CD and infrastructure fundamentals.",
            "Contribute to cloud migration or automation tasks."
        ])

    # --- AI / Machine Learning ---
    if "ai" in domain or "ml" in domain or "machine learning" in domain:
        actions.extend([
            "Build 1–2 end-to-end ML mini projects.",
            "Complete an applied ML or MLOps certification.",
            "Learn prompt engineering and build a small chatbot or automation."
        ])

    # --- Product / Business Analysis ---
    if "product" in domain or "ba" in domain or "business analysis" in domain:
        actions.extend([
            "Practice writing clear user stories and acceptance criteria.",
            "Shadow product discovery sessions or customer calls.",
            "Develop prioritization skills (WSJF, RICE, MoSCoW)."
        ])

    # --- Testing / QA / Automation ---
    if "qa" in domain or "test" in domain:
        actions.extend([
            "Learn test automation frameworks (Selenium, Cypress, Playwright).",
            "Contribute to building regression suites.",
            "Develop skills in API testing (Postman, Karate)."
        ])

    # --- Architecture / System Design ---
    if "architecture" in domain or "design" in domain:
        actions.extend([
            "Study system design patterns and distributed systems basics.",
            "Lead design conversations in 1–2 upcoming features.",
            "Strengthen understanding of non-functional requirements."
        ])

    # --- Support / Customer Success ---
    if "support" in domain or "customer" in domain:
        actions.extend([
            "Improve product knowledge and case troubleshooting.",
            "Participate in customer feedback analysis.",
            "Develop documentation and knowledge base improvements."
        ])

    # ------------------------
    # Agile / SAFe Career Recommendations  (NEW)
    # ------------------------
    if leadership:
        actions.extend([
            "Lead daily standups or retrospectives under supervision.",
            "Take ownership of dependencies and risk updates in team events.",
        ])

    # --- SAFe-specific ---
    if any(keyword in domain for keyword in ["agile", "scrum", "safe", "lean", "kanban"]):
        actions.extend([
            "Participate actively in PI planning preparation.",
            "Learn SAFe fundamentals (Lean Portfolio, ARTs, Value Streams).",
            "Improve backlog refinement and estimation facilitation skills.",
            "Develop stakeholder communication and coordination abilities.",
            "Consider SAFe Scrum Master (SSM) / SAFe POPM certification."
        ])

    # ------------------------
    # Career Goal Specific Guidance
    # ------------------------
    if "manager" in goal or "lead" in goal:
        actions.extend([
            "Enhance stakeholder communication and conflict management.",
            "Practice leadership in ceremonies (standups, retros, planning).",
            "Drive at least one improvement initiative this quarter."
        ])

    if "architect" in goal:
        actions.extend([
            "Lead technical deep dives and evaluate solution alternatives.",
            "Strengthen cloud architecture and design concepts."
        ])

    if "scrum" in goal or "agile" in goal:
        actions.extend([
            "Run at least two retrospectives end-to-end under guidance.",
            "Take responsibility for team health metrics (velocity, WIP, predictability)."
        ])

    # Final cleanup
    return next_role, list(dict.fromkeys(actions))  # remove duplicates, preserve order

def build_recommendations(df):
    df = df.copy()
    df["ReadinessScore"] = df.apply(compute_readiness_score, axis=1)
    next_roles = []
    recs = []

    for _, row in df.iterrows():
        role, actions = suggest_next_role_and_actions(row)
        next_roles.append(role)
        recs.append("• " + "\n• ".join(actions))

    df["SuggestedNextRole"] = next_roles
    df["RecommendedActions"] = recs
    return df


# --------- UI ---------
st.title("🧭 Team Career Progression Assistant")
st.markdown(
    """
This app helps a **Program Manager / People Lead** analyse team career readiness  
and generate **next-role recommendations & action plans** for each member.
"""
)

with st.sidebar:
    st.header("1️⃣ Input Options")
    st.write("Upload a CSV or start from the sample dataset.")

    uploaded_file = st.file_uploader("Upload team data (CSV)", type=["csv"])

    st.markdown(
        """
**Expected columns** (case-sensitive):

- `Name`
- `CurrentRole`
- `YearsExperience` (number)
- `TechSkillRating` (1–5)
- `SoftSkillRating` (1–5)
- `PerformanceRating` (1–5)
- `LeadershipInterest` (Yes/No)
- `DomainInterest` (text)
- `CareerGoal` (text)
"""
    )

    use_sample = st.checkbox("Use sample data", value=True if not uploaded_file else False)

# Load data
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
elif use_sample:
    df_raw = pd.read_csv("sample_data/team_members_sample.csv")
else:
    st.info("Upload a CSV or tick 'Use sample data' to begin.")
    st.stop()

st.subheader("👥 Input Data")
st.dataframe(df_raw, use_container_width=True)

# Compute recommendations
df = build_recommendations(df_raw)

st.subheader("📋 Recommendations by Team Member")
st.dataframe(
    df[
        [
            "Name",
            "CurrentRole",
            "YearsExperience",
            "ReadinessScore",
            "SuggestedNextRole",
            "RecommendedActions",
        ]
    ],
    use_container_width=True,
)

# --------- Dashboard visuals ---------
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
    fig_scores.update_layout(yaxis_range=[0, 110])
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
    st.plotly_chart(fig_roles, use_container_width=True)

st.markdown("---")
st.header("📝 Download Results")

csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Download recommendations as CSV",
    data=csv_buffer.getvalue(),
    file_name="career_recommendations.csv",
    mime="text/csv",
)

st.caption(
    "Note: This tool provides **guidance**, not strict HR decisions. "
    "Use along with your judgment as a people leader."
)
