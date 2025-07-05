# ttb-cola-search
A Basic Web Application to Search TTB COLA Images & Characteristics

## Setup

### Prerequisites

- Python 3.13+ 
- [uv](https://docs.astral.sh/uv/) package manager
- MotherDuck account and database

### MotherDuck Configuration

This application connects to a MotherDuck hosted DuckDB database. You'll need to set up environment variables for authentication:

1. **Get your MotherDuck token** from [https://app.motherduck.com/](https://app.motherduck.com/)
   - Go to Settings → API Tokens
   - Create a new token or copy an existing one

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your configuration:**
   ```env
   MOTHERDUCK_TOKEN=your_actual_token_here
   MOTHERDUCK_DATABASE=md:your_database_name
   ```

### Installation and Testing

```bash
# Install dependencies
uv sync

# Test your MotherDuck connection
uv run python test_motherduck.py

# Run the Streamlit app
uv run streamlit run cola_streamlit_app.py
```

### Environment Variables

- `MOTHERDUCK_TOKEN`: Your MotherDuck authentication token (required)
- `MOTHERDUCK_DATABASE`: Database connection string (default: `md:ttb_public_data`)
  - Format: `md:database_name` or `md:database_name.schema_name`

### Database Schema

The MotherDuck database should contain the following tables:

- **`colas`** - Main COLA data with fields like:
  - `cola_id`, `brand_name`, `fanciful_name`, `origin`, `class_type`
  - `permit_num`, `serial_num`, `completed_date`
  - `publicformdisplay_url`

- **`cola_images`** - Image metadata:
  - `cola_id`, `file_name`, `local_path`, `img_type`, `dimensions_txt`

- **`cola_image_analysis`** - Image analysis results:
  - `cola_id`, `file_name`, `metadata`

- **`image_analysis_items`** - Detailed analysis items:
  - `cola_id`, `file_name`, `analysis_item_type`
  - `text`, `model_confidence`, `bounding_box`
  - Types: `dense_caption`, `tag`, `object`, `text_block`

### Image Handling

The application supports both:
- **Local images**: Stored in `data/` directory (legacy)
- **URL-based images**: HTTP/HTTPS URLs stored in the `local_path` field

#### Diagnostic Tools:

- **Connection Test:** `uv run python test_motherduck.py`
- **MotherDuck Console:** https://app.motherduck.com/
