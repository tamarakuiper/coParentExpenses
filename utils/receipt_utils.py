from pathlib import Path
import streamlit as st



def render_receipt(receipt_path, key_prefix="receipt"):
    if not receipt_path:
        st.write("**Receipt:** No file uploaded")
        return

    path = Path(receipt_path)

    if not path.exists():
        st.warning(f"Receipt file not found: {receipt_path}")
        return

    suffix = path.suffix.lower()

    with open(path, "rb") as f:
        file_bytes = f.read()

    st.write(f"**Receipt File:** {path.name}")

    if suffix in [".png", ".jpg", ".jpeg", ".webp"]:
        st.image(file_bytes, caption=path.name, use_container_width=True)
        st.download_button(
            "Download Receipt",
            data=file_bytes,
            file_name=path.name,
            mime=f"image/{suffix.replace('.', '') if suffix != '.jpg' else 'jpeg'}",
            key=f"{key_prefix}_download",
        )
    elif suffix == ".pdf":
        st.download_button(
            "Download Receipt PDF",
            data=file_bytes,
            file_name=path.name,
            mime="application/pdf",
            key=f"{key_prefix}_download",
        )
    else:
        st.download_button(
            "Download Receipt File",
            data=file_bytes,
            file_name=path.name,
            mime="application/octet-stream",
            key=f"{key_prefix}_download",
        )