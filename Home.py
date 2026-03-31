import streamlit as st

st.set_page_config(
    page_title="SharedCare Ledger",
    page_icon="💼",
    layout="wide",
)

st.markdown(
    """
    <style>
        .hero {
            padding: 2.5rem 2rem;
            border-radius: 20px;
            background: linear-gradient(135deg, #eef4ff 0%, #f8fbff 100%);
            border: 1px solid #d9e6ff;
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            font-size: 2.7rem;
            margin-bottom: 0.4rem;
            color: #12325b;
        }
        .hero p {
            font-size: 1.05rem;
            color: #355070;
            max-width: 760px;
            margin-bottom: 0;
        }
        .summary-box {
            background: #ffffff;
            border: 1px solid #e6ebf2;
            border-radius: 16px;
            padding: 1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }
        .summary-box h4 {
            margin: 0 0 0.5rem 0;
            color: #16324f;
        }
        .footer-note {
            color: #6b7280;
            font-size: 0.9rem;
            margin-top: 2rem;
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>💼 SharedCare Ledger</h1>
        <p>
            A cleaner way for co-parents to track shared child expenses, upload receipts,
            monitor reimbursements, and see what is still outstanding.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([2, 1])

with left:
    st.subheader("Shared expenses, clearly tracked.")
    st.write(
        "Keep a single record of school, medical, childcare, and activity expenses "
        "with documentation and status tracking in one place."
    )

    cta1, cta2 = st.columns(2)
    with cta1:
        st.button("Get Started", type="primary", use_container_width=True)
    with cta2:
        st.button("View Demo", use_container_width=True)

with right:
    st.markdown(
        """
        <div class="summary-box">
            <h4>Live Summary</h4>
            Total shared expenses: <strong>$842.15</strong><br>
            Reimbursed: <strong>$420.00</strong><br>
            Outstanding: <strong>$422.15</strong><br><br>
            <em>14 of 16 expenses have matching receipts</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

with st.expander("Core Features"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            **Expense Tracking**
            
            Log medical, school, childcare, activities, transportation,
            and other shared child expenses in one place.

            **Receipt Uploads**
            
            Attach receipts, invoices, and supporting documents directly
            to each expense entry.

            **Payment Status**
            
            Track whether an expense is outstanding, partially paid, or fully reimbursed.
            """
        )

    with col2:
        st.markdown(
            """
            **Shared Visibility**
            
            Give both parents access to the same expense ledger for transparency.

            **Balance Overview**
            
            See submitted, reimbursed, and outstanding totals at a glance.

            **Export-Ready Records**
            
            Keep documentation organized for personal records, mediation, or legal review.
            """
        )

with st.expander("How It Works"):
    step1, step2, step3, step4 = st.columns(4)

    with step1:
        st.markdown("### 1")
        st.write("Add a child-related expense with the amount, date, category, and notes.")

    with step2:
        st.markdown("### 2")
        st.write("Upload a receipt or invoice so the expense has supporting documentation.")

    with step3:
        st.markdown("### 3")
        st.write("Share the record with the co-parent inside one organized ledger.")

    with step4:
        st.markdown("### 4")
        st.write("Update payments as reimbursements are made and received.")

with st.expander("Built for clarity and accountability"):
    st.write(
        "SharedCare Ledger is designed for cooperative financial recordkeeping "
        "with clear documentation, shared visibility, and a professional audit trail."
    )
    st.write(
        "It is intended for co-parents who want a respectful, transparent way "
        "to manage shared expenses without relying on texts, email chains, "
        "or scattered spreadsheets."
    )

with st.expander("Planned Features"):
    st.markdown(
        """
        - Secure document storage
        - Recurring expenses
        - Payment reminders
        - Monthly summaries
        - Downloadable reimbursement reports
        - Parent account permissions
        """
    )

st.divider()

footer_left, footer_right = st.columns([3, 1])

with footer_left:
    st.markdown("### Start organizing shared expenses with confidence")
    st.write(
        "Reduce confusion, keep every receipt in one place, and maintain a clear record of what is owed."
    )

with footer_right:
    st.button("Create Account", type="primary", use_container_width=True)

st.markdown(
    '<div class="footer-note">© 2026 SharedCare Ledger. Professional expense tracking for modern co-parenting.</div>',
    unsafe_allow_html=True,
)