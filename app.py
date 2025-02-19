import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

def even_split_expenses(
    total_airbnb_cost: float,
    participants_info: list,
    additional_expenses: dict
):
    """
    Distributes the total accommodation cost plus any additional expenses
    across all participants, accounting for different nights stayed.
    Returns a dictionary mapping each participant to their share (final owed).
    """
    total_night_units = sum(p['nights_stayed'] for p in participants_info if p['nights_stayed'] > 0)

    shares = {}
    for participant in participants_info:
        if total_night_units == 0:
            cost_share = total_airbnb_cost / len(participants_info) if len(participants_info) > 0 else 0
        else:
            cost_share = total_airbnb_cost * (participant['nights_stayed'] / total_night_units)
        shares[participant['name']] = cost_share

    total_shared_expenses = sum(additional_expenses.values())
    per_person_additional = (
        total_shared_expenses / len(participants_info)
        if len(participants_info) > 0 else 0
    )

    for participant in participants_info:
        shares[participant['name']] += per_person_additional

    # Round the final result
    for participant, amount in shares.items():
        shares[participant] = float(Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return shares

def main():
    # Configure page with white background and black text
    st.set_page_config(
        page_title="Trip Expense Planner",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS ensuring a white background, no other color changes
    st.markdown("""
    <style>
    body {
        background-color: #FFFFFF; /* White background */
    }
    .title {
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 500;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .results-container {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-top: 1rem;
    }
    .styled-table th, .styled-table td {
        padding: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }
    .styled-table th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    .styled-table tr:nth-child(even) {
        background-color: #fafafa;
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Title and Subtitle
    st.markdown('<div class="title">Trip Expense Planner</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="subtitle">
            Split your trip expenses easily and fairly. Enter the total cost, manage participants, 
            add shared expenses, and compute the breakdown. Download results as CSV for future reference!
        </div>
    """, unsafe_allow_html=True)

    # --- RESET BUTTON ---
    if st.button("Reset All Data"):
        st.session_state.clear()
        st.experimental_rerun()

    # --- SECTION 1: Total Accommodation Cost ---
    st.markdown('<div class="section-header">1. Total Accommodation Cost</div>', unsafe_allow_html=True)
    total_cost = st.number_input(
        "Enter the total cost for accommodation (e.g., Airbnb, hotel)",
        min_value=0.0,
        step=1.0,
        format="%.2f"
    )

    # --- SECTION 2: Participants & Nights Stayed ---
    st.markdown('<div class="section-header">2. Participants & Nights Stayed</div>', unsafe_allow_html=True)
    if "participants" not in st.session_state:
        st.session_state["participants"] = [
            {"name": "Person1", "nights_stayed": 2},
            {"name": "Person2", "nights_stayed": 2}
        ]

    participant_expander = st.expander("Manage Participants", expanded=True)
    with participant_expander:
        remove_participants = []
        for i, participant in enumerate(st.session_state["participants"]):
            row_cols = st.columns([3, 3, 1])
            with row_cols[0]:
                st.session_state["participants"][i]["name"] = st.text_input(
                    f"Name (Participant {i+1})",
                    value=participant["name"],
                    key=f"name_{i}"
                )
            with row_cols[1]:
                st.session_state["participants"][i]["nights_stayed"] = st.number_input(
                    f"Nights (Participant {i+1})",
                    value=participant["nights_stayed"],
                    min_value=0,
                    max_value=365,
                    step=1,
                    key=f"nights_{i}"
                )
            with row_cols[2]:
                if st.button(f"Remove {participant['name']}", key=f"remove_participant_{i}"):
                    remove_participants.append(i)

        for idx in sorted(remove_participants, reverse=True):
            del st.session_state["participants"][idx]

        if st.button("Add Participant"):
            st.session_state["participants"].append({
                "name": f"Person{len(st.session_state['participants'])+1}",
                "nights_stayed": 1
            })

    # --- SECTION 3: Shared Expenses ---
    st.markdown('<div class="section-header">3. Shared Expenses</div>', unsafe_allow_html=True)
    if "extra_expenses" not in st.session_state:
        st.session_state["extra_expenses"] = {"Groceries": 100.0}

    expense_expander = st.expander("Manage Shared Expenses", expanded=True)
    with expense_expander:
        to_remove = []
        for exp, amt in st.session_state["extra_expenses"].items():
            cols = st.columns([3, 2, 1])
            with cols[0]:
                new_exp_name = st.text_input(f"Expense Name: {exp}", value=exp, key=f"expense_name_{exp}")
            with cols[1]:
                new_amt = st.number_input(f"Amount ({exp})", value=amt, step=1.0, key=f"expense_value_{exp}")
            with cols[2]:
                remove_flag = st.button(f"Remove", key=f"remove_{exp}")
                if remove_flag:
                    to_remove.append(exp)

            if new_exp_name != exp:
                st.session_state["extra_expenses"][new_exp_name] = new_amt
                to_remove.append(exp)
            else:
                st.session_state["extra_expenses"][exp] = new_amt

        for rem in to_remove:
            if rem in st.session_state["extra_expenses"]:
                del st.session_state["extra_expenses"][rem]

        if st.button("Add New Expense"):
            st.session_state["extra_expenses"][f"Expense{len(st.session_state['extra_expenses'])+1}"] = 0.0

    # --- SECTION 4: Compute Splits ---
    st.markdown('<div class="section-header">4. Compute Splits</div>', unsafe_allow_html=True)

    if st.button("Compute Splits"):
        participants_info = st.session_state["participants"]
        additional_expenses = {k: float(v) for k, v in st.session_state["extra_expenses"].items()}

        # 1) Calculate final owed amounts using the existing function
        split_result = even_split_expenses(total_cost, participants_info, additional_expenses)

        # 2) Create a more descriptive breakdown DataFrame
        #    showing how each participant's total was derived:
        #       - Nights Stayed
        #       - Accommodation Share
        #       - Additional Share
        #       - Total Owed
        total_night_units = sum(p['nights_stayed'] for p in participants_info if p['nights_stayed'] > 0)
        total_shared_expenses = sum(additional_expenses.values())
        breakdown_rows = []

        for p in participants_info:
            name = p["name"]
            nights = p["nights_stayed"]

            if total_night_units == 0:
                base_cost_share = total_cost / len(participants_info) if len(participants_info) > 0 else 0
            else:
                base_cost_share = total_cost * (nights / total_night_units)

            per_person_additional = (
                total_shared_expenses / len(participants_info)
                if len(participants_info) > 0 else 0
            )

            total_owed = base_cost_share + per_person_additional
            # Round final to two decimals
            total_owed_rounded = float(Decimal(total_owed).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

            breakdown_rows.append({
                "Participant": name,
                "Nights Stayed": nights,
                "Accommodation Share": base_cost_share,
                "Additional Share": per_person_additional,
                "Total Owed": total_owed_rounded
            })

        # Build the DataFrame
        df = pd.DataFrame(breakdown_rows)

        # 3) Format numeric columns for readability
        df["Accommodation Share"] = df["Accommodation Share"].apply(lambda x: f"${x:,.2f}")
        df["Additional Share"] = df["Additional Share"].apply(lambda x: f"${x:,.2f}")
        df["Total Owed"] = df["Total Owed"].apply(lambda x: f"${x:,.2f}")

        # 4) Render table in a container
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        st.markdown("### Final Expense Breakdown")
        st.dataframe(df.style.set_properties(**{'text-align': 'center'}))
        st.markdown('</div>', unsafe_allow_html=True)

        # 5) Provide a download button for the CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Breakdown as CSV",
            data=csv_data,
            file_name="trip_expense_breakdown.csv",
            mime="text/csv"
        )

        st.success("Cost splits computed successfully!")

def run_app():
    main()

if __name__ == "__main__":
    run_app()
