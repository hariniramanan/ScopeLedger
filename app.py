import os

import requests
import streamlit as st
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# PAGE CONFIG

st.set_page_config(
    page_title="ScopeLedger",
    page_icon="📋",
    layout="wide",
)



# CONFIGURATION

load_dotenv()

API_URL = os.getenv("SCOPELEDGER_API_URL")
WRITE_KEY = os.getenv("SCOPELEDGER_WRITE_KEY")


EMBEDDING_MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)



@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

if not API_URL:
    st.error(
        "SCOPELEDGER_API_URL was not found in your .env file."
    )
    st.stop()

embedding_model = load_embedding_model()

# AWS API


def load_project_truth():
    response = requests.get(
        f"{API_URL}/memory",
        timeout=30,
    )

    response.raise_for_status()

    return response.json()

def submit_meeting(
    title,
    meeting_date,
    raw_notes,
):
    response = requests.post(
        f"{API_URL}/meetings",
        headers={
            "x-scopeledger-key": WRITE_KEY
        },
        json={
            "title": title,
            "meetingDate": meeting_date.isoformat(),
            "rawNotes": raw_notes,
        },
        timeout=20,
    )

    if not response.ok:
        try:
            error_data = response.json()
        except Exception:
            error_data = {
                "message": response.text
            }

        raise RuntimeError(
            error_data.get(
                "message",
                "Meeting submission failed."
            )
        )

    return response.json()

def search_project_memory(question):
    query_vector = (
        embedding_model.encode(
            question,
            normalize_embeddings=True,
        )
        .tolist()
    )

    response = requests.post(
        f"{API_URL}/search",
        headers={
            "x-scopeledger-key": WRITE_KEY
        },
        json={
            "queryVector": query_vector
        },
        timeout=30,
    )

    if not response.ok:
        try:
            error_data = response.json()
        except Exception:
            error_data = {
                "message": response.text
            }

        raise RuntimeError(
            error_data.get(
                "message",
                "Semantic search failed."
            )
        )

    return response.json().get(
        "results",
        []
    )
def answer_project_question(
    question,
    data,
):
    question_lower = question.lower().strip()

    project = data["project"]
    optimization = data.get("optimization")
    risk = data.get("risk")

    # ---------------------------------------------
    # BUDGET / COST / AFFORDABILITY QUESTIONS
    # ---------------------------------------------

    budget_keywords = [
        "budget",
        "afford",
        "cost",
        "spend",
        "expense",
        "manage the budget",
        "within budget",
    ]

    if any(
        keyword in question_lower
        for keyword in budget_keywords
    ):
        evidence = search_project_memory(
            question
        )

        current_budget = project.get(
            "currentBudget"
        )

        if not optimization:
            return {
                "answerType": "budget",
                "answer": (
                    f"The current recorded project budget is "
                    f"${float(current_budget):,.2f}."
                    if current_budget
                    else "The current budget is unknown."
                ),
                "evidence": evidence,
            }

        calculation = optimization[
            "calculation"
        ]

        plans = optimization[
            "plans"
        ]

        shortfall = calculation[
            "capacityShortfallDays"
        ]

        pending_scope = calculation[
            "pendingUnapprovedWorkDays"
        ]

        if shortfall == 0:
            assessment = (
                "Yes. Based on the current approved scope "
                "and planning assumptions, the project fits "
                "within available delivery capacity."
            )
        else:
            assessment = (
                "The current plan has delivery pressure. "
                "The budget can be protected if the team "
                "accepts the Protect Budget option and keeps "
                "unapproved scope out of the current release."
            )

        plan_lines = []

        for plan in plans:
            plan_lines.append(
                (
                    f"{plan['name']}: "
                    f"${plan['additionalCost']:,.2f} additional cost, "
                    f"{plan['additionalCapacityDays']} extra capacity day(s), "
                    f"{plan['deadlineExtensionDays']} schedule extension day(s)."
                )
            )

        answer = (
            f"{assessment}\n\n"
            f"Current budget: ${float(current_budget):,.2f}\n"
            f"Capacity shortfall: {shortfall} day(s)\n"
            f"Pending unapproved scope impact: {pending_scope} day(s)\n\n"
            + "\n".join(plan_lines)
        )

        return {
            "answerType": "budget",
            "answer": answer,
            "evidence": evidence,
        }

    # ---------------------------------------------
    # DEADLINE / TIMELINE QUESTIONS
    # ---------------------------------------------

    deadline_keywords = [
        "deadline",
        "timeline",
        "launch",
        "schedule",
        "on time",
        "hit the date",
    ]

    if any(
        keyword in question_lower
        for keyword in deadline_keywords
    ):
        evidence = search_project_memory(
            question
        )

        deadline = project.get(
            "currentDeadline"
        )

        if optimization:
            shortfall = optimization[
                "calculation"
            ][
                "capacityShortfallDays"
            ]

            if shortfall > 0:
                assessment = (
                    f"The current deadline is {deadline}. "
                    f"ScopeLedger calculates a capacity "
                    f"shortfall of {shortfall} day(s), so "
                    f"the deadline is under pressure unless "
                    f"capacity increases or scope is adjusted."
                )
            else:
                assessment = (
                    f"The current deadline is {deadline}, "
                    "and the approved work currently fits "
                    "within available capacity."
                )
        else:
            assessment = (
                f"The current recorded deadline is {deadline}."
            )

        return {
            "answerType": "deadline",
            "answer": assessment,
            "evidence": evidence,
        }

    # ---------------------------------------------
    # RISK QUESTIONS
    # ---------------------------------------------

    risk_keywords = [
        "risk",
        "risky",
        "problem",
        "concern",
        "danger",
    ]

    if any(
        keyword in question_lower
        for keyword in risk_keywords
    ):
        evidence = search_project_memory(
            question
        )

        return {
            "answerType": "risk",
            "answer": (
                f"Current risk level: {risk['level']}.\n\n"
                f"{risk['reason']}\n\n"
                f"Recommended action: "
                f"{risk['recommendedAction']}"
            ),
            "evidence": evidence,
        }

    # ---------------------------------------------
    # DEFAULT = SEMANTIC MEMORY SEARCH
    # ---------------------------------------------

    evidence = search_project_memory(
        question
    )

    return {
        "answerType": "memory",
        "answer": None,
        "evidence": evidence,
    }
# LOAD PROJECT MEMORY


try:
    data = load_project_truth()

except Exception as error:
    st.error(
        "ScopeLedger could not reach the AWS backend."
    )

    st.code(str(error))

    st.stop()


project = data["project"]
risk = data["risk"]
summary = data["summary"]
submission_message = (
    st.session_state.pop(
        "submission_message",
        None
    )
)


# HEADER


st.title("ScopeLedger")

st.caption(
    "Evidence-backed agentic project memory"
)

st.success(
    "AWS backend connected — "
    f"{summary['meetingsRemembered']} meetings remembered."
)
if submission_message:

    st.success(
        submission_message
    )


with st.expander(
    "Add New Meeting",
    expanded=False,
):

    st.write(
        "Paste new Minutes of Meeting notes. "
        "ScopeLedger will send them through the AWS backend "
        "and store them in persistent project memory."
    )

    with st.form(
        "new_meeting_form",
        clear_on_submit=False,
    ):

        meeting_title = st.text_input(
            "Meeting title",
            placeholder=(
                "Example: Website Redesign - "
                "Client Review"
            ),
        )

        meeting_date = st.date_input(
            "Meeting date"
        )

        meeting_notes = st.text_area(
            "Minutes of Meeting",
            height=300,
            placeholder=(
                "Paste your meeting notes here..."
            ),
        )

        submit_button = (
            st.form_submit_button(
                "Save & Analyze Meeting",
                type="primary",
            )
        )

    if submit_button:

        if not meeting_title.strip():

            st.warning(
                "Please enter a meeting title."
            )

        elif not meeting_notes.strip():

            st.warning(
                "Please paste meeting notes."
            )

        else:

            try:

                with st.spinner(
                    "ScopeLedger is processing the meeting..."
                ):

                    result = submit_meeting(
                        title=
                            meeting_title.strip(),

                        meeting_date=
                            meeting_date,

                        raw_notes=
                            meeting_notes.strip(),
                    )

                extraction = result.get(
                    "extraction",
                    {}
                )

                meetings_remembered = (
                    result.get(
                        "meetingsRemembered",
                        "?"
                    )
                )

                st.session_state[
                    "submission_message"
                ] = (
                    "Meeting saved successfully. "
                    f"ScopeLedger now remembers "
                    f"{meetings_remembered} meetings."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    "ScopeLedger could not save "
                    "the meeting."
                )

                st.code(
                    str(error)
                )
st.divider()



# PROJECT TRUTH


st.subheader("Project Truth")

st.write(
    f"### {project['name']} — {project['clientName']}"
)



# TOP METRICS


col1, col2, col3, col4 = st.columns(4)


with col1:

    budget = project["currentBudget"]

    if budget:
        st.metric(
            "Current Budget",
            f"${float(budget):,.2f} {project['currency']}",
        )
    else:
        st.metric(
            "Current Budget",
            "Unknown",
        )


with col2:

    deadline = project["currentDeadline"]

    st.metric(
        "Current Deadline",
        deadline or "Unknown",
    )


with col3:

    st.metric(
        "Project Status",
        project["status"].title(),
    )


with col4:

    st.metric(
        "Meetings Remembered",
        summary["meetingsRemembered"],
    )


st.divider()



# DELIVERY HEALTH


st.subheader("Delivery Health")


if risk["level"] == "HIGH":

    st.error(
        "HIGH RISK — Delivery constraints conflict "
        "with the current project memory."
    )

elif risk["level"] == "MEDIUM":

    st.warning(
        "MEDIUM RISK — ScopeLedger detected "
        "potential delivery concerns."
    )

else:

    st.success(
        "LOW RISK — No major delivery conflict detected."
    )


st.write(
    risk["reason"]
)



# RISK EXPLANATION


with st.expander(
    "Why did ScopeLedger flag this?"
):

    signals = risk["signals"]

    st.write(
        "**Scope changed:**",
        "Yes"
        if signals["scopeChanged"]
        else "No",
    )

    st.write(
        "**Schedule impact detected:**",
        "Yes"
        if signals["scheduleImpactDetected"]
        else "No",
    )

    st.write(
        "**Budget unchanged:**",
        "Yes"
        if signals["budgetUnchanged"]
        else "No",
    )

    st.write(
        "**Deadline unchanged:**",
        "Yes"
        if signals["deadlineUnchanged"]
        else "No",
    )

    st.divider()

    st.write(
        "### Recommended PM Action"
    )

    st.warning(
        risk["recommendedAction"]
    )
# =========================================================
# DELIVERY OPTIMIZER
# =========================================================

optimization = data.get(
    "optimization"
)

if optimization:

    st.divider()

    st.subheader(
        "Delivery Optimizer"
    )

    calculation = optimization[
        "calculation"
    ]

    st.write(
        "ScopeLedger calculates delivery options "
        "from stored project memory and explicit "
        "planning assumptions."
    )

    calc1, calc2, calc3, calc4 = st.columns(4)

    with calc1:

        st.metric(
            "Required Work",
            (
                f"{calculation['requiredWorkDays']}"
                " days"
            ),
        )

    with calc2:

        st.metric(
            "Available Capacity",
            (
                f"{calculation['availableCapacityDays']}"
                " days"
            ),
        )

    with calc3:

        st.metric(
            "Capacity Shortfall",
            (
                f"{calculation['capacityShortfallDays']}"
                " days"
            ),
        )

    with calc4:

        st.metric(
            "Pending Scope Impact",
            (
                f"{calculation['pendingUnapprovedWorkDays']}"
                " days"
            ),
        )

    st.write(
        "### Delivery Options"
    )

    plans = optimization[
        "plans"
    ]

    plan_col1, plan_col2, plan_col3 = (
        st.columns(3)
    )

    plan_columns = [
        plan_col1,
        plan_col2,
        plan_col3,
    ]

    for column, plan in zip(
        plan_columns,
        plans,
    ):

        with column:

            st.write(
                f"### {plan['name']}"
            )

            st.metric(
                "Additional Cost",
                f"${plan['additionalCost']:,.2f}",
            )

            st.metric(
                "Extra Capacity",
                (
                    f"{plan['additionalCapacityDays']}"
                    " days"
                ),
            )

            st.metric(
                "Schedule Extension",
                (
                    f"{plan['deadlineExtensionDays']}"
                    " days"
                ),
            )

            st.write(
                plan["action"]
            )

    st.success(
        "Recommended Plan: "
        + optimization[
            "recommendedPlan"
        ]
    )

    st.write(
        optimization[
            "recommendationReason"
        ]
    )

    pending_items = optimization.get(
        "pendingScopeImpact",
        []
    )

    if pending_items:

        with st.expander(
            "Pending scope not included in these plans"
        ):

            for item in pending_items:

                st.write(
                    f"**{item['item']}** — "
                    f"{item['days']} estimated day(s)"
                )

st.divider()

# =========================================================
# ASK SCOPELEDGER
# =========================================================

st.divider()

st.subheader(
    "Ask ScopeLedger"
)

st.write(
    "Search project history by meaning, "
    "not just exact keywords."
)


with st.form(
    "semantic_search_form"
):

    question = st.text_input(
        "Ask about this project",
        placeholder=(
            "Example: What did the client "
            "say about the launch timeline?"
        ),
    )

    search_button = (
        st.form_submit_button(
            "Search Project Memory",
            type="primary",
        )
    )


if search_button:

    if not question.strip():

        st.warning(
            "Enter a question first."
        )

    else:

        try:

            with st.spinner(
                "Searching project memory..."
            ):

                answer_result  = (
                    answer_project_question(
                        question.strip(), 
                        data,
                    )
                )
                results = answer_result.get(
                    "evidence",
                    []
                )

                generated_answer = (
                    answer_result.get(
                        "answer"
                    )
                )

            if generated_answer:
                st.write(
                    "### ScopeLedger Assessment"
                )
                st.info(
                    generated_answer
                )

            if not results:

                st.info(
                    "No relevant memories found."
                )

            else:

                st.write(
                    "### Most Relevant Evidence"
                )

                for index, result in enumerate(
                    results,
                    start=1,
                ):

                    similarity = result.get(
                        "similarity",
                        0,
                    )

                    memory_type = result.get(
                        "memoryType",
                        "memory",
                    )

                    memory_text = result.get(
                        "memoryText",
                        "",
                    )

                    with st.container(
                        border=True
                    ):

                        st.write(
                            f"**Result #{index} "
                            f"— {memory_type}**"
                        )

                        st.write(
                            memory_text
                        )

                        st.caption(
                            "Semantic similarity: "
                            f"{similarity:.3f}"
                        )

        except Exception as error:

            st.error(
                "ScopeLedger could not "
                "search project memory."
            )

            st.code(
                str(error)
            )

# MEMORY SUMMARY


st.subheader("Memory Summary")

summary_col1, summary_col2, summary_col3, summary_col4 = (
    st.columns(4)
)


with summary_col1:
    st.metric(
        "Decisions",
        summary["decisions"],
    )


with summary_col2:
    st.metric(
        "Open Commitments",
        summary["openCommitments"],
    )


with summary_col3:
    st.metric(
        "Scope Records",
        summary["scopeRecords"],
    )


with summary_col4:
    st.metric(
        "Evidence Records",
        summary["evidenceRecords"],
    )


st.divider()



# TABS


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Decisions",
        "Commitments",
        "Scope History",
        "Changes",
        "Evidence",
        "Meetings",
    ]
)



# DECISIONS


with tab1:

    st.subheader("Decision Memory")

    decisions = data["decisions"]

    if not decisions:
        st.info(
            "No decisions have been remembered yet."
        )

    for decision in decisions:

        st.write(
            f"**• {decision['text']}**"
        )

        if decision["reasoning"]:
            st.write(
                f"Reasoning: {decision['reasoning']}"
            )

        if decision["confidence"]:

            confidence = (
                float(decision["confidence"]) * 100
            )

            st.caption(
                f"Confidence: {confidence:.0f}%"
            )

        st.divider()



# COMMITMENTS


with tab2:

    st.subheader("Commitment Memory")

    commitments = data["commitments"]

    if not commitments:
        st.info(
            "No commitments remembered yet."
        )

    for commitment in commitments:

        left, right = st.columns(
            [3, 1]
        )

        with left:

            st.write(
                f"**{commitment['text']}**"
            )

            st.write(
                "Owner:",
                commitment["owner"]
                or "Unknown",
            )

            if commitment["dueDate"]:
                st.write(
                    "Due:",
                    commitment["dueDate"],
                )

        with right:

            st.write(
                "**Status**"
            )

            st.write(
                commitment[
                    "status"
                ].title()
            )

        if commitment["estimatedDays"]:

            st.caption(
                "Estimated effort: "
                f"{commitment['estimatedDays']} days"
            )

        if commitment["estimatedCost"]:

            st.caption(
                "Estimated cost: "
                f"${commitment['estimatedCost']}"
            )

        st.divider()


# =========================================================
# SCOPE HISTORY
# =========================================================

with tab3:

    st.subheader("Scope History")

    st.caption(
        "ScopeLedger keeps historical state rather "
        "than overwriting previous project memory."
    )

    scope_items = data["scope"]

    if not scope_items:
        st.info(
            "No scope records remembered yet."
        )

    for item in scope_items:

        st.write(
            f"### {item['item']}"
        )

        st.write(
            f"**Status:** {item['status']}"
        )

        if item["impact"]:

            st.write(
                f"**Impact:** {item['impact']}"
            )

        if item["confidence"]:

            confidence = (
                float(item["confidence"]) * 100
            )

            st.caption(
                f"Confidence: {confidence:.0f}%"
            )

        st.divider()



# PROJECT CHANGES


with tab4:

    st.subheader("Project Change History")

    changes = data["changes"]

    if not changes:
        st.info(
            "No project changes remembered yet."
        )

    for change in changes:

        change_type = (
            change["type"]
            .replace("_", " ")
            .title()
        )

        st.write(
            f"### {change_type}"
        )

        if change["meetingDate"]:
            st.caption(
                f"Meeting: {change['meetingDate']}"
            )

        st.write(
            f"**Previous:** "
            f"{change['oldValue']}"
        )

        st.write(
            f"**New:** "
            f"{change['newValue']}"
        )

        if change["reason"]:
            st.info(
                change["reason"]
            )

        st.divider()



# EVIDENCE


with tab5:

    st.subheader("Evidence Memory")

    st.write(
        "ScopeLedger keeps original meeting evidence "
        "behind project conclusions."
    )

    evidence = data["evidence"]

    if not evidence:
        st.info(
            "No evidence remembered yet."
        )

    for item in evidence:

        evidence_type = (
            item["type"]
            or "evidence"
        )

        st.write(
            "**"
            + evidence_type.replace(
                "_",
                " ",
            ).title()
            + "**"
        )

        if item["meetingDate"]:
            st.caption(
                f"{item['meetingDate']} — "
                f"{item['meetingTitle']}"
            )

        st.info(
            item["text"]
        )



# MEETING HISTORY


with tab6:

    st.subheader("Meeting History")

    meetings = data["meetings"]

    if not meetings:
        st.info(
            "No meetings remembered yet."
        )

    for meeting in meetings:

        title = (
            meeting["title"]
            or "Meeting"
        )

        if meeting["meetingDate"]:

            title += (
                " — "
                + meeting[
                    "meetingDate"
                ]
            )

        with st.expander(title):

            st.write(
                meeting["rawNotes"]
            )



# ARCHITECTURE FOOTER


st.divider()

st.caption(
    "Project memory: CockroachDB Cloud "
    "• Backend: AWS Lambda + API Gateway"
)

