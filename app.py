import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
from huggingface_hub import InferenceClient

# --------------------------
# Streamlit Setup
# --------------------------
st.set_page_config(
    page_title="Team Career Progression Assistant",
    layout="wide"
)

st.title("🧭 Team Career Progression Assistant")
st.caption("Program Managers • Scrum Masters • People Leads")

# --------------------------
# Load LLM client (optional)
# --------------------------
@st.cache_resource
def load_llm():
    return InferenceClient("google/flan-t5-small")

def generate_llm_plan(row):
    client = load_llm()

    prompt = f"""
    You are an expert career coach. Summarize strengths and gaps.
    Then give a 30-60-90 day plan.

    Profile:
    Name: {row['Name']}
    Current Role: {row['CurrentRole']}
    Years Exp: {row['YearsExperience']}
    Tech Skills: {row['TechSkillRating']}
    Soft Skills: {row['SoftSkillRating']}
    Performance: {row['PerformanceRating']}
    Leadership: {row['LeadershipInterest']}
    Domain: {row['DomainInterest']}
    Career Goal: {row['CareerGoal']}
    """

    try:
        response = client.text_generation(prompt, max_new_tokens=200)
        return response.strip()
    except Exception as e:
        return f"LLM Error: {e}"

# --------------------------
# Compute readiness score
# --------------------------
def score(row):
    years = min(row["YearsExperience"], 10) / 10 * 5
    tech = row["TechSkillRating"]
    soft = row["SoftSkillRating"]
    perf = row["PerformanceRating"]
    leadership = 5 if str(row["LeadershipInterest"]).lower() == "yes" else 2

    score_5 = (0.3 * years + 0.2 * tech + 0.2 * soft +
               0.2 * perf + 0.1 * leadership)
    return round(score_5 / 5 * 100, 1)

# --------------------------
# Next role + actions
# --------------------------
def suggest_next_role(row):
    s = row["ReadinessScore"]

    if s >= 80:
        return "Team Lead / Scrum Master"
    elif s >= 60:
        return f"Mid-level {row['CurrentRole']}"
    else:
        return "Upskill Current Role"

def suggest_actions(row):
    actions = []

    if row["ReadinessScore"] >= 80:
        actions = [
            "Lead small initiatives",
            "Mentor junior teammates",
            "Improve decision-making"
        ]
    elif row["ReadinessScore"] >= 60:
        actions = [
            "Improve core technical skills",
            "Own a module or feature",
            "Drive small improvements"
        ]
    else:
        actions = [
            "Focus on consistency",
            "Work with mentor weekly",
            "Upskill using certifications"
        ]

    return "• " + "\n• ".join(actions)

# --------------------------
# Sidebar Inputs
# --------------------------
with st.sidebar:
    st.header("📂 Upload CSV or Use Sample")
    file = st.file_uploader("Upload CSV", type=["csv"])
    use_sample = st.checkbox("Use sample data", value=True)

    st.header("🤖 LLM Options")
    use_llm = st.checkbox("Enable AI-generated 30-60-90 plans", value=False)

# --------------------------
# Load data
# --------------------------
if file:
    df_raw = pd.read_csv(file)
elif use_sample:
    df_raw = pd.read_csv("sample_data/team_members_sample.csv")
else:
    st.stop()

st.subheader("📥 Input Data")
st.dataframe(df_raw, use_container_width=True)

# --------------------------
# Calculate Results
# --------------------------
df = df_raw.copy()
df["ReadinessScore"] = df.apply(score, axis=1)
df["SuggestedNextRole"] = df.apply(suggest_next_role, axis=1)
df["RecommendedActions"] = df.apply(suggest_actions, axis=1)

if use_llm:
    df["LLMPlan"] = df.apply(generate_llm_plan, axis=1)
else:
    df["LLMPlan"] = "LLM disabled"

# --------------------------
# Summary Output
# --------------------------
st.subheader("📊 Team Summary")
st.dataframe(
    df[["Name", "CurrentRole", "YearsExperience", "ReadinessScore",
        "SuggestedNextRole"]],
    use_container_width=True
)

# --------------------------
# Detailed Cards
# --------------------------
st.subheader("🧠 Detailed Recommendations")

for _, row in df.iterrows():
    with st.expander(f"{row['Name']} — {row['SuggestedNextRole']}"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Recommended Actions")
            st.write(row["RecommendedActions"])

        with col2:
            st.markdown("### 30-60-90 AI Plan")
            st.write(row["LLMPlan"])

# --------------------------
# Dashboard
# --------------------------
st.markdown("---")
st.header("📈 Team Dashboard")

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(df, x="Name", y="ReadinessScore", text="ReadinessScore")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    count = df["SuggestedNextRole"].value_counts().reset_index()
    count.columns = ["Role", "Count"]
    fig2 = px.pie(count, names="Role", values="Count")
    st.plotly_chart(fig2, use_container_width=True)


# --------------------------
# Download results
# --------------------------
buffer = StringIO()
df.to_csv(buffer, index=False)

st.download_button(
    "📥 Download Full Results CSV",
    buffer.getvalue(),
    "career_progression_results.csv",
    "text/csv"
)
