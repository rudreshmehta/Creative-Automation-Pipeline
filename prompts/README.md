# Prompts Directory

This directory contains all Gemini API prompts used for image generation and text processing.

## Prompt Files

### `product_image_generation.txt`
Generates professional product photos when assets are missing.

**Variables:**
- `{product_name}` - Name of the product
- `{product_description}` - Product description
- `{brand_theme}` - Brand theme/style

### `message_translation.txt`
Translates campaign messages to native languages while preserving marketing tone.

**Variables:**
- `{target_language}` - Target language (e.g., "French (Canadian)")
- `{region}` - Target region (e.g., "Quebec")
- `{target_audience}` - Audience description
- `{message}` - Original campaign message

### `campaign_composition.txt`
Creates social media ad campaigns with branded elements.

**Variables:**
- `{dimensions}` - Image dimensions (e.g., "1080x1080 square")
- `{campaign_message}` - Translated campaign text
- `{brand_font}` - Font name
- `{primary_color}` - Brand primary color (hex)
- `{secondary_color}` - Brand secondary color (hex)
- `{brand_domain}` - Service industry domain

## Usage

Prompts are loaded via `PromptLoader` class in `modules/prompt_loader.py`.

```python
from modules.prompt_loader import PromptLoader

loader = PromptLoader()
prompt = loader.format("product_image_generation",
                      product_name="Shampoo",
                      product_description="Natural formula",
                      brand_theme="eco-friendly")
```

## Customization

Edit these files to modify AI generation behavior without changing code.
