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


def repair_truncated_json(raw: str) -> dict:
    """
    Attempt to salvage a truncated JSON response by extracting
    whatever fields were completed before the cut-off.
    """
    result = {}

    patterns = {
        "meta_title": r'"meta_title"\s*:\s*"((?:[^"\\]|\\.)*)"',
        "meta_description": r'"meta_description"\s*:\s*"((?:[^"\\]|\\.)*)"',
        "h1": r'"h1"\s*:\s*"((?:[^"\\]|\\.)*)"',
        "description": r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            result[key] = match.group(1).replace("\\n", "\n").replace('\\"', '"')

    bullets_match = re.search(r'"bullets"\s*:\s*\[(.*?)(?:\]|$)', raw, re.DOTALL)
    if bullets_match:
        bullet_items = re.findall(r'"((?:[^"\\]|\\.)*)"', bullets_match.group(1))
        result["bullets"] = bullet_items

    faqs_match = re.search(r'"faqs"\s*:\s*\[(.*?)(?:\]|\Z)', raw, re.DOTALL)
    if faqs_match:
        faq_block = faqs_match.group(1)
        questions = re.findall(r'"question"\s*:\s*"((?:[^"\\]|\\.)*)"', faq_block)
        answers = re.findall(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', faq_block)
        result["faqs"] = [
            {"question": q, "answer": a}
            for q, a in zip(questions, answers)
        ]

    return result


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
                max_output_tokens=8192,
            )
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        # First attempt: clean parse
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            # Second attempt: extract fields individually from truncated response
            result = repair_truncated_json(raw)
            if not result:
                return {}, "Gemini returned an incomplete response. Try again or reduce the number of FAQs/bullets."

        # Ensure all required keys exist
        required_keys = ["meta_title", "meta_description", "h1", "bullets", "description", "faqs"]
        for key in required_keys:
            if key not in result:
                result[key] = "" if key not in ["bullets", "faqs"] else []

        return result, None

    except Exception as e:
        return {}, f"Gemini API error: {str(e)}"
