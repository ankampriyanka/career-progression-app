title: Team Career Progression Assistant
emoji: 🧭
colorFrom: indigo
colorTo: green
sdk: streamlit
app_file: app.py
pinned: false
----

# 🧭 Team Career Progression Assistant.

This app helps **Program Managers, People Leads, and Scrum Masters**:

- Analyse team members' **career readiness**
- Suggest **next roles**
- Generate **personalised action plans**
- Visualise the **talent pipeline** via dashboards

Built with **Streamlit + Python**, deployed on **Hugging Face Spaces**, and versioned in **GitHub**.

## 🔧 Features

- CSV upload or sample data
- Readiness score (0–100) per team member
- Suggested next role (e.g., *Senior Engineer*, *Team Lead / Scrum Master*)
- Recommended actions based on:
  - Experience
  - Skill ratings
  - Leadership interest
  - Domain interest
  - Career goals
- Dashboards:
  - Readiness bar chart
  - Role pipeline pie chart
- Downloadable recommendations as CSV

## ▶️ Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
