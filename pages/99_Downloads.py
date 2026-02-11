import streamlit as st
import os
import base64

st.set_page_config(page_title="DataGuardian Pro - Downloads", layout="wide")

st.title("DataGuardian Pro - Promotional Images")
st.markdown("Click the download button below each image to save it.")

promo_images = [
    ("dataguardian_promo_1.jpg", "Global Cybersecurity - Hero banner / social media header"),
    ("dataguardian_promo_2.jpg", "EU GDPR Protection - Compliance marketing"),
    ("dataguardian_promo_3.jpg", "Analytics Dashboard - Platform capabilities"),
    ("dataguardian_promo_4.jpg", "Team Collaboration - Enterprise trust"),
    ("dataguardian_promo_5.jpg", "AI-Powered Analysis - Technology showcase"),
]

for filename, description in promo_images:
    filepath = os.path.join("attached_assets", filename)
    if os.path.exists(filepath):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(filepath, caption=description, use_container_width=True)
        with col2:
            st.markdown(f"**{description}**")
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            st.download_button(
                label=f"Download {filename}",
                data=image_bytes,
                file_name=filename,
                mime="image/jpeg",
                key=filename,
            )
            file_size = os.path.getsize(filepath) / 1024
            st.caption(f"Size: {file_size:.0f} KB | 1280px wide | JPEG")
        st.divider()

st.caption("These images are licensed stock photos for promotional use with DataGuardian Pro.")
