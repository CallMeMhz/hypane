"""
预置抓取能力

提供三种抓取方式：
1. API - 简单 HTTP 请求
2. Webpage - 静态页面 + CSS 选择器
3. Browser - Playwright 动态渲染
"""

import json
import httpx
from typing import Any, Optional
from bs4 import BeautifulSoup


async def fetch_api(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    body: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """
    API 抓取
    
    Returns:
        {"success": bool, "data": Any, "error": str}
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body if method in ("POST", "PUT", "PATCH") else None,
                timeout=timeout,
            )
            response.raise_for_status()
            
            # 尝试解析 JSON
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
            else:
                data = response.text
            
            return {"success": True, "data": data, "status": response.status_code}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}", "status": e.response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def fetch_webpage(
    url: str,
    selectors: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """
    网页抓取 (静态)
    
    Args:
        url: 页面 URL
        selectors: CSS 选择器映射 {"title": "h1", "items": ".item"}
        headers: 自定义 headers
    
    Returns:
        {"success": bool, "data": dict, "error": str}
    """
    try:
        async with httpx.AsyncClient() as client:
            default_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            if headers:
                default_headers.update(headers)
            
            response = await client.get(url, headers=default_headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            if selectors:
                data = {}
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    if len(elements) == 1:
                        data[key] = elements[0].get_text(strip=True)
                    else:
                        data[key] = [el.get_text(strip=True) for el in elements]
                return {"success": True, "data": data}
            else:
                # 返回整个页面文本
                return {"success": True, "data": {"text": soup.get_text(separator="\n", strip=True)}}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def fetch_browser(
    url: str,
    script: Optional[str] = None,
    wait_selector: Optional[str] = None,
    timeout: int = 30000,
) -> dict:
    """
    浏览器抓取 (Playwright)
    
    Args:
        url: 页面 URL
        script: 要执行的 JS 脚本，返回值作为数据
        wait_selector: 等待某个元素出现
        timeout: 超时时间 (毫秒)
    
    Returns:
        {"success": bool, "data": Any, "error": str}
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"success": False, "error": "Playwright not installed. Run: pip install playwright && playwright install"}
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, timeout=timeout)
            
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            
            if script:
                data = await page.evaluate(script)
            else:
                data = await page.content()
            
            await browser.close()
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 同步版本（供采集器脚本使用）
def fetch_api_sync(url: str, **kwargs) -> dict:
    """同步版 API 抓取"""
    import asyncio
    return asyncio.run(fetch_api(url, **kwargs))


def fetch_webpage_sync(url: str, **kwargs) -> dict:
    """同步版网页抓取"""
    import asyncio
    return asyncio.run(fetch_webpage(url, **kwargs))


def fetch_browser_sync(url: str, **kwargs) -> dict:
    """同步版浏览器抓取"""
    import asyncio
    return asyncio.run(fetch_browser(url, **kwargs))
