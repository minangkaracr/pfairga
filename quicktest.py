import os, httpx, asyncio
proxy = os.getenv("HTTPS_PROXY") or "http://proxy.pythonanywhere.com:3128"
async def test():
    transport = httpx.AsyncHTTPTransport(proxy=proxy)
    async with httpx.AsyncClient(transport=transport) as client:
        r = await client.get("https://api.telegram.org")
        print("status:", r.status_code)
asyncio.run(test())
