import streamlit as st

# ------------------------------------------------------------
# SharedCare Ledger - Basic homepage for a co-parenting site
# Run with: streamlit run sharedcare_ledger_homepage.py
# ------------------------------------------------------------

st.set_page_config(
    page_title="SharedCare Ledger",
    page_icon="💼",
    layout="wide",
)

# Minimal styling
st.markdown(
    """
    <style>
        .hero {
            padding: 3rem 1rem 2rem 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #eef4ff 0%, #f8fbff 100%);
            border: 1px solid #d9e6ff;
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
            color: #12325b;
        }
        .hero p {
            font-size: 1.1rem;
            color: #355070;
            max-width: 780px;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
            color: #16324f;
        }
        .feature-card {
            background: #ffffff;
            border: 1px solid #e6ebf2;
            border-radius: 16px;
            padding: 1.25rem;
            min-height: 170px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }
        .feature-card h3 {
            color: #16324f;
            margin-bottom: 0.5rem;
        }
        .feature-card p {
            color: #4b5d73;
        }
        .highlight-box {
            background: #f7f9fc;
            border: 1px solid #e6ebf2;
            padding: 1rem 1.25rem;
            border-radius: 14px;
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

# Top navigation
left_nav, right_nav = st.columns([3, 2])
with left_nav:
    st.markdown("## 💼 SharedCare Ledger")
with right_nav:
    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        st.button("Features", use_container_width=True)
    with nav2:
        st.button("How It Works", use_container_width=True)
    with nav3:
        st.button("Sign In", use_container_width=True)

# Hero section
st.markdown(
    """
    <div class="hero">
        <h1>Shared expenses, clearly tracked.</h1>
        <p>
            SharedCare Ledger helps co-parents record child-related expenses,
            upload receipts, track reimbursements, and see exactly what has been
            paid and what remains outstanding.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.markdown("### A simpler way to manage shared financial responsibilities")
    st.write(
        "Keep a clean record of every expense, attach supporting documents, "
        "and maintain transparency between households with a shared view of balances."
    )

    cta1, cta2 = st.columns([1, 1])
    with cta1:
        st.button("Create Free Account", type="primary", use_container_width=True)
    with cta2:
        st.button("View Demo", use_container_width=True)

with hero_right:
    st.markdown(
        """
        <div class="highlight-box">
            <strong>Live Summary</strong><br><br>
            Total shared expenses this month: <strong>$842.15</strong><br>
            Reimbursed: <strong>$420.00</strong><br>
            Outstanding balance: <strong>$422.15</strong><br><br>
            <em>Receipt matched to 14 of 16 expenses</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Features
st.markdown('<div class="section-title">Core Features</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Expense Tracking</h3>
            <p>
                Log medical, school, childcare, sports, and everyday expenses in one place.
                Categorize each entry for faster reporting.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Receipt Uploads</h3>
            <p>
                Attach receipts, invoices, and supporting documents directly to each expense
                so every charge has documentation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Payment Status</h3>
            <p>
                Mark expenses as pending, partially paid, reimbursed, or outstanding to keep
                a clear and current balance between co-parents.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Shared Visibility</h3>
            <p>
                Give each parent access to the same expense ledger to reduce confusion and
                improve transparency.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Balance Overview</h3>
            <p>
                See total submitted, total paid, and outstanding amounts at a glance across
                current and prior months.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col6:
    st.markdown(
        """
        <div class="feature-card">
            <h3>Export-Ready Records</h3>
            <p>
                Prepare expense summaries and supporting receipts for personal records,
                mediation, or legal review.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# How it works
st.markdown('<div class="section-title">How It Works</div>', unsafe_allow_html=True)
steps = st.columns(4)
step_titles = [
    "1. Add Expense",
    "2. Upload Receipt",
    "3. Share With Co-Parent",
    "4. Track Payment",
]
step_text = [
    "Enter the date, amount, category, and notes for a child-related expense.",
    "Attach an image or PDF receipt to keep the record complete.",
    "Both parents can review the expense details in a single shared workspace.",
    "Update the payment status when reimbursement is sent or received.",
]

for i, col in enumerate(steps):
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <h3>{step_titles[i]}</h3>
                <p>{step_text[i]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Trust / privacy section
st.markdown('<div class="section-title">Built for clarity and accountability</div>', unsafe_allow_html=True)
trust_left, trust_right = st.columns([3, 2])

with trust_left:
    st.write(
        "SharedCare Ledger is designed to support cooperative financial recordkeeping "
        "with clear documentation, shared visibility, and a professional audit trail."
    )
    st.write(
        "Ideal for co-parents who want a respectful, transparent way to manage shared "
        "child expenses without relying on text messages or scattered spreadsheets."
    )

with trust_right:
    st.info(
        "Planned modules: secure document storage, recurring expenses, payment reminders, "
        "monthly summaries, and downloadable reimbursement reports."
    )

# Footer CTA
st.divider()
footer_left, footer_right = st.columns([3, 1])
with footer_left:
    st.markdown("### Start organizing shared expenses with confidence")
    st.write("Create a shared record, reduce disputes, and keep every receipt in one secure place.")
with footer_right:
    st.button("Get Started", type="primary", use_container_width=True)

st.markdown(
    '<div class="footer-note">© 2026 SharedCare Ledger. Professional expense tracking for modern co-parenting.</div>',
    unsafe_allow_html=True,
)
