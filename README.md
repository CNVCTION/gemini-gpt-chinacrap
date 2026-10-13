# DealScout: Temu & AliExpress Price Comparison Middleware

Backend FastAPI proxy service designed to run as an Action backend for custom ChatGPT / GPT Pro instances. It fetches items from AliExpress and Temu concurrently, ranks them by absolute lowest total cost (Price + Shipping), and returns normalized JSON.

## Included Files
- `main.py`: FastAPI server handling parallel execution and response normalization.
- `requirements.txt`: Python package dependencies.
- `Dockerfile`: Container build file for deployment platforms like Render, Fly.io, or Railway.
- `openapi.yaml`: OpenAPI schema specification for ChatGPT Custom GPT Actions.
- `.gitignore`: Common Python runtime ignores.

## Quickstart (Local Development)

```bash
pip install -r requirements.txt
export RAPIDAPI_KEY="your_ali_express_rapidapi_key"
export APIFY_TOKEN="your_temu_apify_token"
uvicorn main:app --reload --port 8000
```

## Deployment
1. Push these repository files to GitHub.
2. Deploy as a Web Service on **Render** (select Docker runtime).
3. Set environment variables `RAPIDAPI_KEY` and `APIFY_TOKEN` in host settings.
4. Update `servers.url` in `openapi.yaml` to point to your live deployment URL.
