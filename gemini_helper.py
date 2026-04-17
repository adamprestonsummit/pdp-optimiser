import google.generativeai as genai
import json
import re


def build_prompt(page_data: dict, settings: dict) -> str:
    tone = settings.get("tone", "Professional")
    audience = settings.get("audience", "")
    brand_notes = settings.get("brand_guidelines", "")
    num_bullets = settings.get("num_bullets", 5)
    num_faqs = settings.get("num_faqs", 5)

    audience_line = f"Target audience: {audience}" if audience else ""
    brand_line = f"Brand notes: {brand_notes}" if brand_notes else ""

    prompt = f"""You are an expert ecommerce copywriter specialising in SEO-optimised, conversion-focused product page content.

TASK:
Analyse the scraped product page data below and generate optimised content for the product page.

SCRAPED PAGE DATA:
- URL: {page_data.get('url', '')}
- Product name / H1: {page_data.get('product_name') or page_data.get('h1', '')}
- Page title: {page_data.get('page_title', '')}
- Existing meta description: {page_data.get('meta_description', '')}
- Price: {page_data.get('price', '')}
- H2 headings: {', '.join(page_data.get('h2s', []))}
- Existing bullets/features: {'; '.join(page_data.get('bullets', [])[:10])}
- Breadcrumb / category: {page_data.get('breadcrumb', '')}
- Body text (excerpt): {page_data.get('body_text', '')[:3000]}
- Structured data: {page_data.get('structured_data', '')[:500]}

CONTENT SETTINGS:
- Tone: {tone}
{audience_line}
{brand_line}

OUTPUT REQUIREMENTS:
Generate {num_bullets} benefit-led bullets and {num_faqs} FAQs.

All content must:
- Lead with customer benefits, not just features
- Be written in British English
- Include natural primary and secondary keywords where appropriate
- Avoid keyword stuffing
- Be ready to publish (no placeholders)

Respond ONLY with a valid JSON object using exactly this structure (no markdown, no extra text):

{{
  "meta_title": "SEO meta title, 50-60 characters",
  "meta_description": "Compelling meta description, 140-160 characters, includes a CTA",
  "h1": "Optimised H1 / page title",
  "bullets": [
    "Benefit-led bullet 1",
    "Benefit-led bullet 2",
    "Benefit-led bullet 3"
  ],
  "description": "2-3 paragraph benefit-led product description. First paragraph hooks the reader. Second covers key features framed as benefits. Third includes a soft CTA.",
  "faqs": [
    {{"question": "Question one?", "answer": "Answer one."}},
    {{"question": "Question two?", "answer": "Answer two."}}
  ]
}}
"""
    return prompt


def generate_optimised_content(page_data: dict, settings: dict, api_key: str) -> tuple[dict, str | None]:
    """
    Call the Gemini API and return structured content.
    Returns (result dict, error message or None).
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = build_prompt(page_data, settings)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        result = json.loads(raw)

        # Validate expected keys
        required_keys = ["meta_title", "meta_description", "h1", "bullets", "description", "faqs"]
        for key in required_keys:
            if key not in result:
                result[key] = "" if key not in ["bullets", "faqs"] else []

        return result, None

    except json.JSONDecodeError as e:
        return {}, f"Could not parse Gemini response as JSON: {str(e)}"
    except Exception as e:
        return {}, f"Gemini API error: {str(e)}"
