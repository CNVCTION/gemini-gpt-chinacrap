import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Temu & AliExpress Deal Finder",
    version="1.0.0"
)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

class ProductDeal(BaseModel):
    title: str = Field(..., description="Product title")
    platform: str = Field(..., description="Source platform")
    price: float = Field(..., description="Base product price in USD")
    shipping_cost: float = Field(..., description="Shipping cost in USD")
    total_price: float = Field(..., description="Total cost")
    currency: str = Field("USD", description="Currency code")
    rating: float | None = Field(None, description="Average rating out of 5")
    units_sold: int | None = Field(None, description="Total units sold")
    product_url: str = Field(..., description="Direct link")
    image_url: str = Field(..., description="Image thumbnail link")

async def search_aliexpress(client: httpx.AsyncClient, query: str) -> list[ProductDeal]:
    deals = []
    if not RAPIDAPI_KEY:
        return deals
    try:
        url = "https://aliexpress-datahub.p.rapidapi.com/item_search"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "aliexpress-datahub.p.rapidapi.com"
        }
        res = await client.get(url, headers=headers, params={"q": query, "page": "1", "sort": "price_asc"}, timeout=15.0)
        
        if res.status_code == 200:
            data = res.json()
            items = data.get("result", {}).get("resultList", [])
            for item in items[:10]:
                i = item.get("item", {})
                price = float(i.get("sku", {}).get("def", {}).get("promotionPrice", 0) or i.get("sku", {}).get("def", {}).get("price", 0) or 0)
                shipping = float(i.get("delivery", {}).get("shippingFee", 0) or 0)
                item_id = i.get("itemId")
                
                if price > 0 and item_id:
                    deals.append(ProductDeal(
                        title=i.get("title", "AliExpress Item"),
                        platform="AliExpress",
                        price=round(price, 2),
                        shipping_cost=round(shipping, 2),
                        total_price=round(price + shipping, 2),
                        currency="USD",
                        rating=float(i.get("averageStarRate", 0)) if i.get("averageStarRate") else None,
                        units_sold=int(i.get("sales", 0)) if i.get("sales") else None,
                        product_url=f"https://www.aliexpress.com/item/{item_id}.html",
                        image_url=i.get("image", "")
                    ))
    except Exception as e:
        print(f"AliExpress Error: {e}")
    return deals

async def search_temu(client: httpx.AsyncClient, query: str) -> list[ProductDeal]:
    deals = []
    if not APIFY_TOKEN:
        return deals
    try:
        url = f"https://api.apify.com/v2/acts/piotrv1001~temu-listings-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
        payload = {"searchUrls": [f"https://www.temu.com/search_result.html?search_key={query}"]}
        
        res = await client.post(url, json=payload, timeout=25.0)
        if res.status_code in (200, 201):
            items = res.json()
            for item in items[:10]:
                price = float(item.get("price", 0) or 0)
                shipping = float(item.get("shipping_cost", 0) or 0)
                if price > 0:
                    deals.append(ProductDeal(
                        title=item.get("title", "Temu Item"),
                        platform="Temu",
                        price=round(price, 2),
                        shipping_cost=round(shipping, 2),
                        total_price=round(price + shipping, 2),
                        currency="USD",
                        rating=float(item.get("rating", 0)) if item.get("rating") else None,
                        units_sold=int(item.get("sales_count", 0)) if item.get("sales_count") else None,
                        product_url=item.get("url", ""),
                        image_url=item.get("image_url", "")
                    ))
    except Exception as e:
        print(f"Temu Error: {e}")
    return deals

@app.get("/search", response_model=list[ProductDeal])
async def compare_prices(query: str = Query(..., description="Product keyword")):
    async with httpx.AsyncClient() as client:
        ali_task = search_aliexpress(client, query)
        temu_task = search_temu(client, query)
        results = await asyncio.gather(ali_task, temu_task)
        
    combined = results[0] + results[1]
    if not combined:
        raise HTTPException(status_code=404, detail="No products found on Temu or AliExpress.")
    
    combined.sort(key=lambda x: x.total_price)
    return combined

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return "<html><body><h1>Privacy Policy</h1><p>This service queries public marketplaces without storing user personal data.</p></body></html>"
