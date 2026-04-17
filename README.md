# PDP Content Optimiser

A Streamlit tool for generating SEO-optimised, benefit-led product page content from any product URL. Built for Summit.

## What it does

Paste one URL or a list of product page URLs and the tool will:

- Scrape the live page content
- Send it to Gemini AI with copywriting instructions
- Return optimised content ready to review and publish:
  - **Meta title** (with character count guidance)
  - **Meta description** (with character count guidance)
  - **H1 / page title**
  - **Benefit-led bullet points**
  - **Product description** (2-3 paragraphs)
  - **FAQs**

Results can be downloaded as JSON per page, or as a full bulk export.

## File structure

```
pdp-optimiser/
├── app.py                        # Main Streamlit app
├── scraper.py                    # Page scraping logic
├── gemini_helper.py              # Gemini API integration
├── requirements.txt              # Python dependencies
├── .gitignore
├── .streamlit/
│   ├── config.toml               # Theme and server config
│   └── secrets.toml.example      # Template (do not commit real secrets)
└── README.md
```

## Setup

### 1. Fork or clone this repo to your GitHub account

### 2. Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repo, branch (`main`), and set the main file to `app.py`
5. Click **Deploy**

### 3. Add your Gemini API key as a secret

In Streamlit Cloud:

1. Go to your app > **Settings** > **Secrets**
2. Add the following:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
```

3. Save and the app will restart automatically.

### Getting a Gemini API key

Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate a free Gemini API key.

## Sidebar settings

| Setting | Description |
|---|---|
| Tone | Content style: Professional, Friendly, Technical, or Luxury |
| Target audience | Optional: informs the copywriting angle |
| Brand notes | Optional: include/exclude phrases, highlight USPs |
| Number of bullets | 3 to 8 |
| Number of FAQs | 3 to 8 |

## Bulk mode

In the **Bulk URLs** tab you can either:
- Paste multiple URLs (one per line)
- Upload a CSV file with a `url` column

Results are processed one at a time with a short delay between requests to be polite to the target servers.

## Notes

- Some product pages may block scraping (Cloudflare-protected sites, JavaScript-rendered content). In these cases the tool will attempt to generate content from whatever it can retrieve.
- For JavaScript-heavy sites (e.g. SPAs), content quality may be lower due to limited scraping of client-rendered content.
- Rate limits on the free Gemini tier may apply for large bulk runs.
