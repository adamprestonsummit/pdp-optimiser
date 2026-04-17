import streamlit as st
import json
import time
import pandas as pd
from scraper import scrape_page
from gemini_helper import generate_optimised_content

# --- Page config ---
st.set_page_config(
    page_title="PDP Content Optimiser",
    page_icon="🛒",
    layout="wide"
)

# --- Styling ---
st.markdown("""
<style>
    .output-card {
        background: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .char-count {
        font-size: 0.75rem;
        color: #888;
        margin-top: 2px;
    }
    .char-ok { color: #4CAF50; }
    .char-warn { color: #FF9800; }
    .char-over { color: #f44336; }
    .section-header {
        font-weight: 600;
        color: #333;
        margin-bottom: 4px;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stTextArea textarea { font-size: 0.9rem; }
    .result-url {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


def char_indicator(text, ideal_min, ideal_max):
    n = len(text)
    if n < ideal_min:
        cls = "char-warn"
    elif n > ideal_max:
        cls = "char-over"
    else:
        cls = "char-ok"
    return f'<span class="char-count {cls}">{n} characters (ideal: {ideal_min}–{ideal_max})</span>'


def render_result(result, url):
    """Render a single result block."""
    st.markdown(f'<div class="result-url">📄 {url}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Meta Title</div>', unsafe_allow_html=True)
        st.text_area("", result.get("meta_title", ""), key=f"mt_{url}", height=70, label_visibility="collapsed")
        st.markdown(char_indicator(result.get("meta_title", ""), 50, 60), unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:16px;">Meta Description</div>', unsafe_allow_html=True)
        st.text_area("", result.get("meta_description", ""), key=f"md_{url}", height=90, label_visibility="collapsed")
        st.markdown(char_indicator(result.get("meta_description", ""), 140, 160), unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:16px;">Page Title (H1)</div>', unsafe_allow_html=True)
        st.text_area("", result.get("h1", ""), key=f"h1_{url}", height=70, label_visibility="collapsed")

    with col2:
        st.markdown('<div class="section-header">Benefit-Led Bullets</div>', unsafe_allow_html=True)
        bullets = result.get("bullets", [])
        bullets_text = "\n".join([f"• {b}" for b in bullets])
        st.text_area("", bullets_text, key=f"bullets_{url}", height=180, label_visibility="collapsed")

        st.markdown('<div class="section-header" style="margin-top:16px;">Product Description</div>', unsafe_allow_html=True)
        st.text_area("", result.get("description", ""), key=f"desc_{url}", height=180, label_visibility="collapsed")

    st.markdown('<div class="section-header" style="margin-top:12px;">FAQs</div>', unsafe_allow_html=True)
    faqs = result.get("faqs", [])
    faq_text = ""
    for i, faq in enumerate(faqs, 1):
        faq_text += f"Q{i}: {faq.get('question', '')}\nA{i}: {faq.get('answer', '')}\n\n"
    st.text_area("", faq_text.strip(), key=f"faqs_{url}", height=200, label_visibility="collapsed")

    # Export button for this result
    export_data = {
        "url": url,
        "meta_title": result.get("meta_title", ""),
        "meta_description": result.get("meta_description", ""),
        "h1": result.get("h1", ""),
        "bullets": bullets,
        "description": result.get("description", ""),
        "faqs": faqs
    }
    st.download_button(
        label="⬇ Download JSON",
        data=json.dumps(export_data, indent=2),
        file_name=f"pdp_content_{int(time.time())}.json",
        mime="application/json",
        key=f"dl_{url}"
    )
    st.divider()


# --- Header ---
st.title("🛒 PDP Content Optimiser")
st.markdown("Paste product page URLs to generate benefit-led, SEO-optimised content using Gemini AI.")

# --- API Key check ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ No Gemini API key found. Add `GEMINI_API_KEY` to your Streamlit secrets.")
    st.stop()

# --- Sidebar settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    tone = st.selectbox(
        "Content tone",
        ["Professional", "Friendly & conversational", "Technical", "Luxury / premium"],
        index=0
    )
    audience = st.text_input("Target audience (optional)", placeholder="e.g. homeowners, DIY enthusiasts")
    brand_guidelines = st.text_area("Brand notes (optional)", placeholder="e.g. avoid 'cheap', always mention warranty", height=100)
    num_bullets = st.slider("Number of bullets", 3, 8, 5)
    num_faqs = st.slider("Number of FAQs", 3, 8, 5)
    st.divider()
    st.markdown("**About**")
    st.markdown("Built for Summit. Powered by Gemini.")

# --- Mode tabs ---
tab_single, tab_bulk = st.tabs(["Single URL", "Bulk URLs"])

settings = {
    "tone": tone,
    "audience": audience,
    "brand_guidelines": brand_guidelines,
    "num_bullets": num_bullets,
    "num_faqs": num_faqs,
}

# =====================
# SINGLE URL TAB
# =====================
with tab_single:
    url_input = st.text_input("Product page URL", placeholder="https://www.example.com/product-name")
    run_single = st.button("Generate content", type="primary", key="run_single")

    if run_single and url_input:
        with st.spinner("Scraping page..."):
            page_data, scrape_error = scrape_page(url_input)

        if scrape_error:
            st.warning(f"Scrape issue: {scrape_error}. Continuing with partial data.")

        with st.spinner("Generating optimised content with Gemini..."):
            result, gen_error = generate_optimised_content(page_data, settings, api_key)

        if gen_error:
            st.error(f"Generation failed: {gen_error}")
        else:
            st.success("Content generated!")
            render_result(result, url_input)

    elif run_single and not url_input:
        st.warning("Please enter a URL.")

# =====================
# BULK URL TAB
# =====================
with tab_bulk:
    st.markdown("Enter one URL per line, or upload a CSV with a `url` column.")

    bulk_method = st.radio("Input method", ["Paste URLs", "Upload CSV"], horizontal=True)

    urls = []
    if bulk_method == "Paste URLs":
        bulk_text = st.text_area("URLs (one per line)", height=150, placeholder="https://example.com/product-1\nhttps://example.com/product-2")
        if bulk_text:
            urls = [u.strip() for u in bulk_text.strip().split("\n") if u.strip()]
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)
            if "url" in df.columns:
                urls = df["url"].dropna().tolist()
                st.success(f"Found {len(urls)} URLs in CSV.")
            else:
                st.error("CSV must have a `url` column.")

    if urls:
        st.markdown(f"**{len(urls)} URL(s) ready to process.**")

    run_bulk = st.button("Generate all", type="primary", key="run_bulk", disabled=not urls)

    if run_bulk and urls:
        all_results = []
        progress = st.progress(0, text="Starting...")

        for i, url in enumerate(urls):
            progress.progress((i) / len(urls), text=f"Processing {i+1}/{len(urls)}: {url}")

            with st.expander(f"Result: {url}", expanded=True):
                with st.spinner("Scraping..."):
                    page_data, scrape_error = scrape_page(url)

                if scrape_error:
                    st.warning(f"Scrape issue: {scrape_error}")

                with st.spinner("Generating content..."):
                    result, gen_error = generate_optimised_content(page_data, settings, api_key)

                if gen_error:
                    st.error(f"Failed: {gen_error}")
                else:
                    render_result(result, url)
                    all_results.append({"url": url, **result})

            time.sleep(1)  # polite delay between requests

        progress.progress(1.0, text="Complete!")
        st.success(f"Done! {len(all_results)} pages processed.")

        if all_results:
            st.download_button(
                label="⬇ Download all results (JSON)",
                data=json.dumps(all_results, indent=2),
                file_name=f"pdp_bulk_export_{int(time.time())}.json",
                mime="application/json"
            )
