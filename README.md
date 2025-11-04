# Creative Automation Pipeline

> **AI-powered social media campaign generation system leveraging Google Cloud Vertex AI for automated, scalable, and brand-compliant creative asset production.**

This pipeline automates the end-to-end process of generating localized social media campaigns across multiple aspect ratios, with built-in brand compliance validation and legal content screening.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Input & Output Examples](#input--output-examples)
- [Key Design Decisions](#key-design-decisions)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Assumptions & Limitations](#assumptions--limitations)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

The Creative Automation Pipeline is a proof-of-concept system designed to demonstrate scalable, AI-driven creative production for social media advertising. It takes a campaign brief as input and produces ready-to-use campaign assets in multiple formats, with automated quality checks.

**Core Capabilities:**
- Generate product images from text descriptions using Imagen 3
- Compose social media ads with product images, text overlays, and brand elements
- Translate campaign messages to native languages (9+ supported regions)
- Validate brand compliance (logo presence, color usage)
- Screen for prohibited content (medical claims, profanity, etc.)
- Upload assets to Dropbox cloud storage with shared links
- Produce comprehensive execution reports

---

## Features

### ✅ Core Features (Implemented)

| Feature | Description | Technology |
|---------|-------------|------------|
| **Product Asset Generation** | AI-generated product photos from text descriptions | Vertex AI Imagen 3 |
| **Campaign Composition** | Social media ads with text overlays and branding | Gemini 2.5 Flash Image |
| **Multi-Aspect Ratio** | Square (1:1), Story (9:16), Banner (16:9) formats | Automated composition |
| **Localization** | Native language translation for 9+ regions | Gemini 2.5 Flash |
| **Asset Reuse** | Smart caching to avoid regenerating existing assets | Local file system |

### 🎯 Bonus Features (Implemented)

| Feature | Description | Status |
|---------|-------------|--------|
| **Brand Compliance Checks** | Logo detection (OpenCV) + Brand color validation (K-means) | ✅ Implemented |
| **Legal Content Screening** | Configurable prohibited word detection with severity levels | ✅ Implemented |
| **Comprehensive Reporting** | JSON reports with execution metrics and compliance results | ✅ Implemented |
| **Dropbox Cloud Storage** | Automatic upload with shared links and folder management | ✅ Implemented |
| **Rate Limiting** | Smart throttling for API quota management | ✅ Implemented |

### 🚀 Extra Features (Added Value)

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Configurable AI Prompts** | External text files for easy customization | No code changes needed |
| **Pydantic Validation** | Type-safe input validation with helpful error messages | Prevents runtime errors |
| **Logo Overlay** | Programmatic logo placement (PIL) | Consistent branding |
| **Color Shade Matching** | Checks 11 color variations (5 lighter + 5 darker) | More lenient compliance |
| **Detailed Logging** | Progress tracking with aspect ratio visibility | Better debugging |
| **Retry Logic** | Exponential backoff for rate limit errors | Resilient execution |

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Google Cloud Platform account** with Vertex AI API enabled
- **Dropbox account** with API access token
- **Brand assets**: Logo file (PNG format)

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd creative-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up Google Cloud authentication
gcloud auth application-default login

# 4. Configure environment
cp .env.example .env
# Above command will create the .env file and fill in the required configurations.
#   - GCP_PROJECT_ID
#   - DROPBOX_ACCESS_TOKEN 
```

### Run Your First Campaign

```bash
# Prepare brand logo
mkdir -p assets/brands
cp /path/to/your/logo.png assets/brands/logo.png

# Run the pipeline
python main.py data/campaign_brief.json
```

**Output:**
```
INFO: Campaign: spring_beauty_2025 | Products: 1 | Region: Quebec
INFO: Processing: Hydrating Rose Lotion
INFO: Generating: Hydrating Rose Lotion | Aspect: 1:1 | Output: 1x1.png
INFO: Generating: Hydrating Rose Lotion | Aspect: 9:16 | Output: 9x16.png
INFO: Generating: Hydrating Rose Lotion | Aspect: 16:9 | Output: 16x9.png
============================================================
CAMPAIGN EXECUTION REPORT: spring_beauty_2025
============================================================
Campaigns Generated:    3
Products:               1
Assets Generated:       1
Compliance Passed:      3
Total Time:             45.23s
============================================================
```

---

## How It Works

### Process Flow

```
┌─────────────────┐
│ Campaign Brief  │
│   (JSON Input)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  1. Load & Validate Brief   │
│     (Pydantic validation)   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  2. Legal Content Check     │
│     (Prohibited words)      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  3. Translation             │
│     (Gemini 2.5 Flash)      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  For Each Product:          │
│                             │
│  4a. Check Asset Cache      │
│      ├─ Exists? → Reuse     │
│      └─ Missing? → Generate │
│         (Imagen 3)          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  4b. Compose Campaigns      │
│      (3 Aspect Ratios)      │
│      ├─ 1:1  (Square)       │
│      ├─ 9:16 (Story)        │
│      └─ 16:9 (Banner)       │
│   (Gemini 2.5 Flash Image + │
│    PIL Logo Overlay)        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  4c. Brand Compliance Check │
│      ├─ Logo Detection      │
│      │   (OpenCV)           │
│      └─ Color Validation    │
│          (K-means + Shades) │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  5. Upload to Dropbox       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  6. Generate Report         │
│     (JSON + Console)        │
└─────────────────────────────┘
```

### Detailed Execution Steps

1. **Input Validation**
   - Parse campaign brief JSON
   - Validate all fields with Pydantic schemas
   - Check brand assets exist

2. **Legal Screening**
   - Scan campaign message for prohibited words
   - Apply severity levels (ERROR blocks, WARNING flags)
   - Check both original and translated messages

3. **Localization**
   - Detect target language from region
   - Translate campaign message using Gemini
   - Preserve brand voice and tone

4. **Asset Generation** (Per Product)
   - **Check Cache**: Look for existing product asset
   - **Generate if Needed**: Create product photo with Imagen 3
   - **Compose Campaigns**: Generate 3 variations using product image + prompt
   - **Add Logo**: Overlay brand logo programmatically (PIL)

5. **Quality Validation**
   - **Logo Detection**: Template matching with confidence score
   - **Color Validation**: K-means clustering + shade range checking
   - **Report Violations**: Log compliance failures with details

6. **Cloud Upload** 
   - Upload assets to Dropbox
   - Organize by campaign ID and product name
   - Generate shared links

7. **Reporting**
   - Generate JSON report with metrics
   - Display console summary
   - Save execution logs

---

## Input & Output Examples

### Input: Campaign Brief

**File:** `data/campaign_brief.json`

```json
{
  "campaign_id": "spring_fmcg_2025",
  "products": [
    {
      "name": "Crest Whitening toothpaste",
      "description": "Advanced whitening toothpaste with enamel protection",
      "asset_path": ""
    }
  ],
  "region": "India",
  "target_audience": "Adults 25-45, health-conscious",
  "campaign_message": "Brighten your smile naturally",
  "brand": {
    "logo_path": "assets/brands/logo.png",
    "primary_color": "#0A3D62",
    "secondary_color": "#FFFFFF",
    "font_name": "Roboto",
    "theme": "fresh and clean",
    "domain": "Personal Care"
  }
}
```

### Output Structure

```
outputs/spring_fmcg_2025/Crest_Whitening_toothpaste/
├── 1x1.png      # Square (Instagram Feed)
├── 9x16.png     # Vertical (Stories)
└── 16x9.png     # Horizontal (Banners)

assets/products/
└── Crest_Whitening_toothpaste.png  # Generated once, cached

reports/
└── campaign_spring_fmcg_2025_*.json

Dropbox:
└── /creative-automation/spring_fmcg_2025/
    ├── Crest_Whitening_toothpaste/
    │   ├── Crest_Whitening_toothpaste.png
    │   ├── 1x1.png
    │   ├── 9x16.png
    │   └── 16x9.png
    └── reports/
        └── report.json
```

### More Examples

Explore additional test cases in `data/test_cases/`:

```bash
# 1. Success case (KitKat chocolate)
python main.py data/test_cases/01_success_kitkat.json

# 2. Warning case (unsubstantiated claims)
python main.py data/test_cases/02_warning_coffee.json

# 3. Blocked case (medical claims - ERROR)
python main.py data/test_cases/03_error_blocked_shampoo.json

# 4. Multi-product success (3 products)
python main.py data/test_cases/04_multi_product_lotion.json

# See data/test_cases/TEST_CASES_GUIDE.md for full documentation
```

**Each test case demonstrates:**
- Different product categories (food, beverage, personal care)
- Different regions/languages (Japan, Brazil, France)
- Success vs. warning vs. error scenarios
- Single vs. multi-product campaigns

---

## Key Design Decisions

### 1. **Google Cloud Vertex AI for Image Generation**

We chose Vertex AI with Imagen 3 for product asset generation because it delivers enterprise-grade reliability and consistent quality. The built-in safety filters and scalable infrastructure make it production-ready, though it does come with API costs (~$0.02 per image) and rate limits (60 requests/minute).

### 2. **Gemini 2.5 Flash Image for Campaign Composition**

Instead of traditional text-to-image generation, we use Gemini's multimodal model that accepts both the product image and text prompt. This gives better context understanding and more consistent branding since the AI can actually see the product it's working with.

### 3. **Smart Asset Caching**

The pipeline checks if a product asset already exists before generating a new one. This simple optimization reduces API calls, cuts costs, and ensures products look consistent across multiple campaigns. For repeat campaigns, this can save 80% of execution time.

### 4. **Programmatic Logo Overlay**

Rather than asking the AI to add the logo (which often produces inconsistent results), we overlay it programmatically using PIL after generation. This gives us precise control over placement (top-right corner, 10% width, 20px padding) and ensures every creative has the logo exactly where it should be.

### 5. **External Prompt Files**

All AI prompts live in separate text files under `prompts/`, not hardcoded in Python. This means anyone can tune prompts without touching code, making it easy to A/B test messaging or adapt for different brand voices. Non-technical team members can iterate on prompts independently.

### 6. **Pydantic for Type Safety**

Using Pydantic v2 for input validation catches errors before they hit the API. Invalid campaign briefs fail fast with helpful error messages, and developers get IDE autocomplete when working with campaign data structures.

### 7. **OpenCV for Logo Detection**

For brand compliance, we use OpenCV's template matching instead of training a deep learning model. It's fast (<100ms), requires no training data, and works well enough for POC validation. The trade-off is sensitivity to rotation and scale changes, but for consistent logo files this isn't an issue.

### 8. **Color Shade Matching**

Rather than exact hex code matching (which almost always fails with AI-generated images), we check 11 color variations: 5 darker shades, the target color, and 5 lighter shades. This accounts for lighting and shadows while still validating that brand colors are present. It dramatically reduces false negatives.

### 9. **Severity-Based Legal Screening**

Legal compliance uses a two-tier system: ERROR-level words (medical claims, profanity) block the entire pipeline, while WARNING-level words (superlatives, unsubstantiated claims) flag the content but allow execution. This gives flexibility—hard regulatory violations stop immediately, while softer best practices get flagged for human review.

### 10. **Dropbox Cloud Storage**

Every generated asset automatically uploads to Dropbox with shared links for easy distribution. The system manages folder organization by campaign ID and product name, automatically cleaning up old versions before uploading fresh assets. This ensures stakeholders always have immediate cloud access to the latest campaign creatives without manual file transfers.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                  │
│  - Pipeline coordination                                    │
│  - Error handling                                           │
│  - Logging configuration                                    │
└──────────┬──────────────────────────────────────────────────┘
           │
           ├──┬── VertexAIService (modules/vertex_ai_service.py)
           │  │    - Product asset generation (Imagen 3)
           │  │    - Message translation (Gemini 2.5 Flash)
           │  │    - Campaign composition (Gemini 2.5 Flash Image)
           │  │    - Logo overlay (PIL)
           │  │    - Rate limiting
           │  │    - Safety filter handling
           │  │
           │  ├── AssetManager (modules/asset_manager.py)
           │  │    - Asset caching
           │  │    - File path management
           │  │
           │  ├── CampaignComposer (modules/campaign_composer.py)
           │  │    - Multi-aspect ratio generation
           │  │    - Output directory management
           │  │
           │  ├── BrandComplianceChecker (modules/brand_compliance.py)
           │  │    - Logo detection (OpenCV)
           │  │    - Color validation (K-means)
           │  │
           │  ├── LegalChecker (modules/legal_checker.py)
           │  │    - Prohibited word scanning
           │  │    - Severity-based blocking
           │  │
           │  ├── Reporter (modules/reporter.py)
           │  │    - JSON report generation
           │  │    - Console summary
           │  │
           │  ├── DropboxUploader (modules/dropbox_uploader.py)
           │  │    - Cloud storage upload
           │  │    - Shared link generation
           │  │
           │  └── PromptLoader (modules/prompt_loader.py)
           │       - External prompt file loading
           │       - Template formatting
           │
           └── Data Models (schemas/campaign.py)
                - Pydantic validation
                - Type definitions
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI/ML** | Google Cloud Vertex AI | Image generation (Imagen 3) |
| | Google Gemini 2.5 Flash | Text generation & translation |
| | Google Gemini 2.5 Flash Image | Multimodal campaign composition |
| **Image Processing** | Pillow (PIL) | Logo overlay, image manipulation |
| | OpenCV | Template matching for logo detection |
| | scikit-learn | K-means clustering for color analysis |
| **Validation** | Pydantic v2 | Input validation, type safety |
| **Cloud Storage** | Dropbox SDK | Asset upload |
| **Language** | Python 3.10+ | Core implementation |

### Directory Structure

```
creative-automation/
├── main.py                          # Pipeline orchestrator
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not committed)
│
├── schemas/                         # Data models
│   └── campaign.py                  # Pydantic schemas
│
├── modules/                         # Core modules
│   ├── vertex_ai_service.py         # AI service integration
│   ├── asset_manager.py             # Asset caching
│   ├── campaign_composer.py         # Campaign generation
│   ├── brand_compliance.py          # Compliance checking
│   ├── legal_checker.py             # Content screening
│   ├── reporter.py                  # Report generation
│   ├── dropbox_uploader.py          # Cloud upload
│   └── prompt_loader.py             # Prompt management
│
├── prompts/                         # AI prompt templates
│   ├── product_image_generation.txt
│   ├── message_translation.txt
│   └── campaign_composition.txt
│
├── data/                            # Input data
│   ├── campaign_brief.json          # Example campaign brief
│   └── prohibited_words.json        # Legal compliance rules
│
├── assets/                          # Static assets
│   ├── products/                    # Generated product images (cached)
│   ├── brands/                      # Brand logos
│   └── fonts/                       # Font files (future use)
│
├── outputs/                         # Generated campaigns
│   └── [campaign_id]/
│       └── [product_name]/
│           ├── 1x1.png
│           ├── 9x16.png
│           └── 16x9.png
│
├── reports/                         # Execution reports
│   └── campaign_*.json
│
└── docs/                            # Documentation
    ├── README.md                    # This file
    ├── ARCHITECTURE.md              # Detailed architecture
    ├── SYSTEM_FLOW.md               # Visual flow diagrams
```

---

## Configuration

### Environment Variables

**File:** `.env`

```env
# Google Cloud / Vertex AI Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1

# AI Models
IMAGEN_MODEL=imagen-3.0-generate-002
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your-gemini-api-key                        

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Rate Limiting
IMAGEN_RPM_LIMIT=60

# Output Directories
OUTPUT_DIR=outputs
REPORTS_DIR=reports
ASSETS_DIR=assets

# Dropbox Configuration
DROPBOX_ACCESS_TOKEN=your_dropbox_token  # Get from https://www.dropbox.com/developers/apps
DROPBOX_UPLOAD_ENABLED=true              # Must be true for pipeline to work
DROPBOX_BASE_PATH=/creative-automation   # Base folder in Dropbox
```

### Dropbox Configuration

To configure Dropbox cloud storage:

1. **Create Dropbox App**
   - Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Click "Create app"
   - Choose "Scoped access"
   - Choose "Full Dropbox" access
   - Name your app (e.g., "Creative Automation Pipeline")

2. **Generate Access Token**
   - In app settings, go to "OAuth 2" section
   - Click "Generate" under "Generated access token"
   - Copy the token

3. **Configure Environment**
   - Update `.env`:
     ```env
     DROPBOX_ACCESS_TOKEN=your_generated_token_here
     DROPBOX_UPLOAD_ENABLED=true
     ```

4. **Test Configuration**
   ```bash
   python test_dropbox.py
   ```

**What gets uploaded:**
- Product assets: `/creative-automation/{campaign_id}/{product_name}/{product}.png`
- Campaign images: `/creative-automation/{campaign_id}/{product_name}/{aspect_ratio}.png`
- Reports: `/creative-automation/{campaign_id}/reports/report.json`

**Features:**
- Automatic folder cleanup (deletes old campaign folders before upload)
- Shared link generation for all uploaded files
- Detailed upload logging with success/failure tracking
- Organized folder structure by campaign and product

### Supported Regions & Languages

| Region | Language |
|--------|----------|
| Quebec | French (Canadian) |
| France | French |
| Mexico | Spanish (Mexican) |
| Spain | Spanish |
| India | Hindi |
| Japan | Japanese |
| China | Chinese (Simplified) |
| Germany | German |
| Brazil | Portuguese (Brazilian) |

### AI Prompts

The pipeline uses three customizable prompts stored in `prompts/` directory:

#### 1. Product Image Generation (`product_image_generation.txt`)

**Prompt:**
```
Professional product photo of {product_name}.
{product_description}.
Style: {brand_theme}.
Studio lighting, white background, high quality, centered composition
```

**Input Example:**
- Product: "Crest Whitening toothpaste"
- Description: "Advanced whitening toothpaste with enamel protection"
- Theme: "fresh and clean"

**Output:** High-quality product photo on white background, centered, studio-lit

---

#### 2. Message Translation (`message_translation.txt`)

**Prompt:**
```
Translate the following marketing message to {target_language}.
Maintain marketing tone, cultural appropriateness for {region}, and appeal to {target_audience}.
Preserve brand names and product names without translation.
Output only the translated text without explanations.

Message: {message}
```

**Input Example:**
- Message: "Brighten your smile naturally"
- Target Language: "Hindi"
- Region: "India"
- Audience: "Adults 25-45, health-conscious"

**Output:** "अपनी मुस्कान को प्राकृतिक रूप से निखारें"

---

#### 3. Campaign Composition (`campaign_composition.txt`)

**Prompt:**
```
Transform this product into a professional photo shoot for social media advertisement for {brand_domain}.
Keep the product centered and prominent.
Replace background with: {primary_color} gradient scene.
Add bold text overlay: '{original_message}' in {brand_font} vacant area / outside the main object.
Add second text overlay in another language: '{translated_message}' in {brand_font} vacant area / outside the main object.
Text color: {secondary_color} for maximum contrast and readability.
Style: Eye-catching Instagram/TikTok story aesthetic, modern and clean.
Leave empty space at the top-right corner area (clear space for logo).
Professional marketing photography with studio-quality lighting.
```

**Input Example:**
- Product Image: Toothpaste product photo
- Original Message: "Brighten your smile naturally"
- Translated Message: "अपनी मुस्कान को प्राकृतिक रूप से निखारें"
- Brand Domain: "Personal Care"
- Primary Color: "#0A3D62"
- Secondary Color: "#FFFFFF"
- Brand Font: "Roboto"

**Output:** Social media creative with product, dual-language text, gradient background, logo space reserved

---

**Built with ❤️ for scalable creative automation**
