import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import sys
import time

# Add Flask for web API
from flask import Flask, jsonify, render_template_string  # add render_template_string

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def scrape_deepmind(return_results=False):
    url = "https://deepmind.google/discover/blog/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Status Code: {response.status_code}")

    results = []
    cards = soup.select('a.glue-card.card')
    print(f"Found {len(cards)} cards")
    for card in cards:
        anchor_link = card.get("href")
        if anchor_link and not anchor_link.startswith("http"):
            anchor_link = "https://deepmind.google/discover/blog/" + anchor_link

        title_tag = card.select_one("p.glue-headline.glue-headline--headline-5")
        title = title_tag.get_text(strip=True) if title_tag else None

        desc_tag = card.select_one("p.glue-card__description")
        short_desc = desc_tag.get_text(strip=True) if desc_tag else None

        img_tag = card.select_one("img.picture__image")
        image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

        time_tag = card.find("time")
        timestamp = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

        long_desc = None
        if anchor_link:
            try:
                article_resp = requests.get(anchor_link, headers=headers)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = (
                    article_soup.find("div", class_="post-body") or
                    article_soup.find("article")
                )
                if not content_div:
                    divs = article_soup.find_all("div")
                    if divs:
                        content_div = max(divs, key=lambda d: len(d.get_text(strip=True)))
                if content_div:
                    long_desc = content_div.get_text(separator=" ", strip=True)
            except Exception as e:
                print(f"Failed to fetch long_desc for {anchor_link}: {e}")

       
        results.append({
            "title": title,
            "short_desc": short_desc,
            "image_url": image_url,
            "timestamp": timestamp,
            "source": url,
            "published": False,
            "anchor_link": anchor_link,
            "long_desc": long_desc
        })

    if return_results:
        return results

    csv_path = "assets/csv/deepmind.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        if "anchor_link" not in df_existing.columns:
            df_existing["anchor_link"] = None
        if "long_desc" not in df_existing.columns:
            df_existing["long_desc"] = None
    else:
        df_existing = pd.DataFrame(columns=["title", "short_desc", "image_url", "timestamp", "source", "published", "anchor_link", "long_desc"])

    new_df = pd.DataFrame(results)
    combined_df = pd.concat([df_existing, new_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["title", "timestamp"], inplace=True)
    combined_df.to_csv(csv_path, index=False)
    print(f"Saved {len(combined_df)} unique news items to {csv_path}")

def scrape_wired(return_results=False):
    url = "https://www.wired.com/tag/artificial-intelligence/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Status Code: {response.status_code}")

    results = []
    articles = soup.find_all("div", class_=lambda x: x and "summary-item" in x)
    for article in articles:
        anchor_tag = article.find("a", class_=lambda x: x and "summary-item__hed-link" in x, href=True)
        anchor_link = None
        title = None
        if anchor_tag:
            anchor_link = anchor_tag["href"]
            if anchor_link and not anchor_link.startswith("http"):
                anchor_link = "https://www.wired.com" + anchor_link
            title_tag = anchor_tag.find("h3", class_=lambda x: x and "summary-item__hed" in x)
            title = title_tag.get_text(strip=True) if title_tag else None

        img_tag = article.find("img", class_=lambda x: x and "responsive-image__image" in x)
        if not img_tag:
            img_tag = article.find("img", class_=lambda x: x and "responsive-image__image" in x)
        image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

        time_tag = article.find("time", class_=lambda x: x and "ContentHeaderTitleBlockPublishDate" in x)
        if not time_tag:
            time_tag = article.find("time")
        timestamp = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

        author = None
        byline_preamble = article.find("span", class_=lambda x: x and "byline__preamble" in x)
        if byline_preamble:
            next_sibling = byline_preamble.find_next_sibling("span")
            if next_sibling:
                author = next_sibling.get_text(strip=True)
        if not author:
            author_tag = article.find("span", class_=lambda x: x and "byline__name" in x)
            author = author_tag.get_text(strip=True) if author_tag else None

        long_desc = None
        if anchor_link:
            try:
                article_resp = requests.get(anchor_link, headers=headers)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = article_soup.find("div", class_=lambda x: x and "body__inner-container" in x)
                if content_div:
                    long_desc = content_div.get_text(separator=" ", strip=True)
            except Exception as e:
                print(f"Failed to fetch long_desc for {anchor_link}: {e}")

        results.append({
            "title": title,
            "image_url": image_url,
            "timestamp": timestamp,
            "author": author,
            "source": url,
            "published": False,
            "anchor_link": anchor_link,
            "long_desc": long_desc
        })

    if return_results:
        return results

    csv_path = "assets/csv/wired.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        for col in ["anchor_link", "long_desc", "author"]:
            if col not in df_existing.columns:
                df_existing[col] = None
    else:
        df_existing = pd.DataFrame(columns=["title", "image_url", "timestamp", "author", "source", "published", "anchor_link", "long_desc"])

    new_df = pd.DataFrame(results)
    combined_df = pd.concat([df_existing, new_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["title", "timestamp"], inplace=True)
    combined_df.to_csv(csv_path, index=False)
    print(f"Saved {len(combined_df)} unique news items to {csv_path}")

def scrape_zdnet_ai_carousels(return_results=False, save_csv=False, image_dir="assets/images/img"):
    url = "https://www.zdnet.com/topic/artificial-intelligence/"
    headers_zdnet = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers_zdnet)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    carousels = soup.find_all("div", class_="c-dynamicCarousel")
    results = []

    for carousel in carousels:
        section_title = carousel.find("h4", class_="c-sectionHeading")
        if not section_title:
            continue
        section_title = section_title.get_text(strip=True)
        items = []
        for item in carousel.select(".c-listingCarouselHorizontal_item a"):
            title = item.get("title") or item.get_text(strip=True)
            link = "https://www.zdnet.com" + item.get("href")
            img_tag = item.find("img")
            img_url = img_tag["src"] if img_tag and img_tag.get("src") else None
            items.append({
                "title": title,
                "url": link,
                "image": img_url
            })
        if items:
            results.append({
                "section": section_title,
                "articles": items
            })

    if save_csv:
        rows = []
        os.makedirs(image_dir, exist_ok=True)
        for section in results:
            for idx, article in enumerate(section["articles"]):
                image_url = article["image"]
                image_filename = f"{section['section'].replace(' ', '_')}_{idx+1}"
                local_image_path = None
                if image_url:
                    try:
                        resp = requests.get(image_url, stream=True, timeout=10)
                        resp.raise_for_status()
                        ext = os.path.splitext(image_url)[1].split('?')[0]
                        if not ext or len(ext) > 5:
                            ext = '.jpg'
                        filepath = os.path.join(image_dir, image_filename + ext)
                        with open(filepath, 'wb') as f:
                            for chunk in resp.iter_content(1024):
                                f.write(chunk)
                        local_image_path = filepath
                    except Exception:
                        local_image_path = None
                rows.append({
                    "section": section["section"],
                    "title": article["title"],
                    "url": article["url"],
                    "image": local_image_path if local_image_path else image_url
                })
        df = pd.DataFrame(rows)
        csv_path = "assets/csv/zdnet_ai_carousels.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} rows to {csv_path}")

    if return_results:
        return results

def scrape_nvidia(return_results=False, save_csv=False):
    url = "https://developer.nvidia.com/blog/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Status Code: {response.status_code}")

    results = []
    for div in soup.find_all("div", class_="carousel-row-slide__inner"):
        img_tag = div.find("div", class_="carousel-row-slide__thumbnail")
        img_url = None
        if img_tag:
            img = img_tag.find("img")
            if img and img.get("src"):
                img_url = img["src"]

        date_span = div.find("span", class_="post-published-date")
        timestamp = date_span.get_text(strip=True) if date_span else None

        title_div = div.find("div", class_="carousel-row-slide__title")
        title = None
        if title_div:
            h3 = title_div.find("h3")
            if h3:
                title = h3.get_text(strip=True)

        excerpt_div = div.find("div", class_="carousel-row-slide__excerpt")
        short_desc = None
        if excerpt_div:
            content = excerpt_div.find("div", class_="content-m")
            if content:
                short_desc = content.get_text(strip=True)

        results.append({
            "title": title,
            "short_description": short_desc,
            "image_url": img_url,
            "timestamp": timestamp,
            "source": url,
            "published": False
        })

    if save_csv:
        csv_path = os.path.join("assets", "csv", "nvidia_blogs.csv")
        df_new = pd.DataFrame(results)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        if os.path.exists(csv_path):
            df_old = pd.read_csv(csv_path)
            df = pd.concat([df_old, df_new], ignore_index=True)
            df.drop_duplicates(subset=["title", "image_url"], inplace=True)
        else:
            df = df_new
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} unique news items to {csv_path}")

    if return_results:
        return results



def scrape_thegradient(return_results=False, save_csv=False):
    import re
    base_url = "https://thegradient.pub"
    headers_gradient = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    response = requests.get(base_url, headers=headers_gradient)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    articles = soup.find_all("div", class_=lambda x: x and "c-post-card-wrap" in x)
    for article in articles:
        title_tag = article.find("h2") or article.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else None

        desc_tag = article.find("p")
        short_desc = desc_tag.get_text(strip=True) if desc_tag else None

        a_tag = article.find("a", href=True)
        anchor_link = base_url + a_tag["href"] if a_tag else None

        date_text = None
        meta = article.find("time")
        if meta and meta.has_attr("datetime"):
            date_text = meta["datetime"]

        long_desc = None

        img_tag = article.find("img", class_="c-post-card__image")
        image_url = None
        if img_tag and img_tag.has_attr("src"):
            image_url = img_tag["src"]
            if not image_url.startswith("http"):
                image_url = base_url + image_url

        if anchor_link:
            try:
                article_resp = requests.get(anchor_link, headers=headers_gradient)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                article_tag = article_soup.find("article", class_=lambda x: x and "c-post" in x)
                if article_tag:
                    long_desc = article_tag.get_text(separator=" ", strip=True)
                else:
                    content_div = article_soup.find("div", class_="c-content")
                    if content_div:
                        long_desc = content_div.get_text(separator=" ", strip=True)
                if long_desc:
                    match = re.match(r'(.+?[.!?])(\s|$)', long_desc)
                    short_desc = match.group(1).strip() if match else long_desc[:120].strip()
                else:
                    short_desc = None
                time.sleep(1)
            except Exception as e:
                print(f"Failed to fetch article at {anchor_link}: {e}")

        results.append({
            "title": title,
            "short_desc": short_desc,
            "image_url": image_url,
            "timestamp": date_text,
            "source": base_url,
            "published": False,
            "anchor_link": anchor_link,
            "long_desc": long_desc
        })

    if save_csv:
        os.makedirs("assets/csv", exist_ok=True)
        main_csv_path = "assets/csv/thegradient.csv"
        if os.path.exists(main_csv_path):
            df_existing = pd.read_csv(main_csv_path)
        else:
            df_existing = pd.DataFrame(columns=[
                "title", "short_desc", "image_url", "timestamp", "source",
                "published", "anchor_link", "long_desc"
            ])
        new_df = pd.DataFrame(results)
        combined_df = pd.concat([df_existing, new_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["title", "timestamp"], inplace=True)
        combined_df.to_csv(main_csv_path, index=False)

        desc_df = combined_df[["title", "long_desc"]].dropna(subset=["long_desc"]).drop_duplicates()
        desc_csv_path = "assets/csv/thegradient_descriptions.csv"
        desc_df.to_csv(desc_csv_path, index=False)

        print(f"✅ Found and saved {len(combined_df)} unique articles to: {main_csv_path}")
        print(f"📝 Saved {len(desc_df)} full descriptions to: {desc_csv_path}")

    if return_results:
        return results

def scrape_forbes_ai(return_results=False, save_csv=False):
    import re
    headers_forbes = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    url = "https://www.forbes.com/ai/"
    base_url = url
    results = []
    try:
        response = requests.get(url, headers=headers_forbes, timeout=10)
        print(f"[DEBUG] Forbes status code: {response.status_code}")
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch Forbes page, status code: {response.status_code}")
            if return_results:
                return {"error": f"Failed to fetch Forbes page, status code: {response.status_code}"}
            return
        soup = BeautifulSoup(response.text, "html.parser")
        grid_div = soup.find("div", class_="ZQt9W")
        if not grid_div:
            snippet = response.text[:500]
            print(f"[ERROR] Could not find grid_div. HTML snippet: {snippet}")
            if return_results:
                return {"error": "Could not find main news grid on Forbes page.", "html_snippet": snippet}
            return
        for div in grid_div.find_all("div", class_="TNWax51Q T3-IGTjJ jiKZAfWh"):
            title_tag = div.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else None

            author_tag = div.find("p", class_="ujvJmzbB")
            author = author_tag.get_text(strip=True) if author_tag else None

            img_tag = div.find("img", class_="tBA7tnId")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") and img_tag["src"] else None
            # Try to get image from parent <a> tag if <img> src is missing
            if not image_url:
                a_tag = div.find("a", href=True)
                if a_tag and a_tag.has_attr("data-ga-track"):
                    import re
                    # Try to extract image URL from data-ga-track if present
                    match = re.search(r'(https?://[^\s"\']+\.(?:jpg|jpeg|png|webp|gif))', a_tag["data-ga-track"])
                    if match:
                        image_url = match.group(1)

            time_tag = div.find("div", class_="IE8ecQMQ")
            timestamp = None
            if time_tag:
                span = time_tag.find("span")
                if span:
                    timestamp = span.get_text(strip=True)

            anchor_link = None
            spacey_div = div.find("div", class_="WjVFB823")
            if spacey_div:
                anchor_tag = spacey_div.find("a", href=True)
                if anchor_tag:
                    anchor_link = anchor_tag["href"]
                    if anchor_link and not anchor_link.startswith("http"):
                        anchor_link = base_url + anchor_link

            long_desc = None
            short_desc = None
            if anchor_link:
                try:
                    article_resp = requests.get(anchor_link, headers=headers_forbes, timeout=10)
                    article_soup = BeautifulSoup(article_resp.text, "html.parser")
                    content_div = article_soup.find("div", class_="p5_3X")
                    if content_div:
                        long_desc = content_div.get_text(separator=" ", strip=True)
                        match = re.match(r'(.+?[.!?])(\s|$)', long_desc)
                        short_desc = match.group(1).strip() if match else long_desc[:120].strip()
                    else:
                        short_desc = None
                except Exception as e:
                    print(f"Failed to fetch long_desc for {anchor_link}: {e}")

            results.append({
                "title": title,
                "short_desc": short_desc,
                "author": author,
                "image_url": image_url,
                "timestamp": timestamp,
                "source": url,
                "published": False,
                "anchor_link": anchor_link,
                "long_desc": long_desc
            })
        print(f"[DEBUG] Number of results found: {len(results)}")
        if not results:
            print("[ERROR] No news items found. The selector may be wrong or the page structure has changed.")
        if save_csv:
            csv_path = "assets/csv/forbes_ai.csv"
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            if os.path.exists(csv_path):
                df_existing = pd.read_csv(csv_path)
                if "anchor_link" not in df_existing.columns:
                    df_existing["anchor_link"] = None
                if "long_desc" not in df_existing.columns:
                    df_existing["long_desc"] = None
                if "short_desc" not in df_existing.columns:
                    df_existing["short_desc"] = None
            else:
                df_existing = pd.DataFrame(columns=["title", "short_desc", "author", "image_url", "timestamp", "source", "published", "anchor_link", "long_desc"])
            new_df = pd.DataFrame(results)
            new_df.drop_duplicates(subset=["title"], inplace=True)
            if not df_existing.empty:
                existing_titles = set(df_existing['title'].dropna().str.strip().str.lower())
                new_df = new_df[~new_df['title'].str.strip().str.lower().isin(existing_titles)]
            combined_df = pd.concat([df_existing, new_df], ignore_index=True)
            combined_df.drop_duplicates(subset=["title"], inplace=True, keep='first')
            combined_df.to_csv(csv_path, index=False)
            print(f"[DEBUG] Saved {len(combined_df)} unique news items to {csv_path}")
        if return_results:
            return results
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        if return_results:
            return {"error": str(e)}

def scrape_ainews(return_results=False, save_csv=True):
    url = "https://www.ainews.com/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Status Code: {response.status_code}")

    results = []
    grid_div = soup.find("div", class_="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3")
    if grid_div:
        for div in grid_div.find_all("div", class_="transparent h-full cursor-pointer overflow-hidden rounded-lg flex flex-col border"):
            title_tag = div.find("h2")
            title = title_tag.get_text(strip=True) if title_tag else None

            desc_tag = div.find("p")
            short_desc = desc_tag.get_text(strip=True) if desc_tag else None

            img_tag = div.find("img", class_="absolute inset-0 h-full w-full object-cover")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

            time_tag = div.find("time")
            timestamp = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

            anchor_link = None
            spacey_div = div.find("div", class_="space-y-3")
            if spacey_div:
                anchor_tag = spacey_div.find("a", href=True)
                if anchor_tag:
                    anchor_link = anchor_tag["href"]
                    if anchor_link and not anchor_link.startswith("http"):
                        anchor_link = "https://www.ainews.com" + anchor_link

            long_desc = None
            if anchor_link:
                try:
                    article_resp = requests.get(anchor_link, headers=headers)
                    article_soup = BeautifulSoup(article_resp.text, "html.parser")
                    content_div = article_soup.find("div", id="content-blocks")
                    if content_div:
                        long_desc = content_div.get_text(separator=" ", strip=True)
                except Exception as e:
                    print(f"Failed to fetch long_desc for {anchor_link}: {e}")
            results.append({
                "title": title,
                "short_desc": short_desc,
                "image_url": image_url,
                "timestamp": timestamp,
                "source": url,
                "published": False,
                "anchor_link": anchor_link,
                "long_desc": long_desc
            })

    if save_csv:
        csv_path = "assets/csv/ainews.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
            if "anchor_link" not in df_existing.columns:
                df_existing["anchor_link"] = None
            if "long_desc" not in df_existing.columns:
                df_existing["long_desc"] = None
        else:
            df_existing = pd.DataFrame(columns=["title", "short_desc", "image_url", "timestamp", "source", "published", "anchor_link", "long_desc"])
        new_df = pd.DataFrame(results)
        combined_df = pd.concat([df_existing, new_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["title", "timestamp"], inplace=True)
        combined_df.to_csv(csv_path, index=False)
        print(f"Saved {len(combined_df)} unique news items to {csv_path}")

    if return_results:
        return results

# --- Flask web server ---
app = Flask(__name__)

@app.route("/deepmind")
def deepmind_api():
    results = scrape_deepmind(return_results=True)  # No save_csv param, always saves in function
    return jsonify(results)

@app.route("/wired")
def wired_api():
    results = scrape_wired(return_results=True)  # No save_csv param, always saves in function
    return jsonify(results)

@app.route("/zdnet")
def zdnet_api():
    results = scrape_zdnet_ai_carousels(return_results=True, save_csv=True)
    return jsonify(results)

@app.route("/nvidia")
def nvidia_api():
    results = scrape_nvidia(return_results=True, save_csv=True)
    return jsonify(results)

@app.route("/forbes")
def forbes_api():
    results = scrape_forbes_ai(return_results=True, save_csv=True)
    return jsonify(results)

@app.route("/thegradient")
def thegradient_api():
    results = scrape_thegradient(return_results=True, save_csv=True)
    return jsonify(results)

@app.route("/ainews")
def ainews_api():
    results = scrape_ainews(return_results=True, save_csv=True)
    return jsonify(results)

@app.route("/")
def index():
    # Simple HTML with Tailwind CDN and JS to fetch news on button click
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI News Scraper</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex flex-col items-center justify-start py-10">
    <h1 class="text-3xl font-bold mb-8">AI News Scraper</h1>
    <div class="flex flex-wrap gap-4 mb-8">
        {% for endpoint, label in endpoints %}
        <button onclick="fetchNews('{{ endpoint }}')" class="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold">
            {{ label }}
        </button>
        {% endfor %}
    </div>
    <div id="news-container" class="w-full max-w-3xl space-y-6"></div>
    <script>
        function fetchNews(endpoint) {
            const container = document.getElementById('news-container');
            container.innerHTML = '<div class="text-center text-gray-500">Loading...</div>';
            fetch('/' + endpoint)
                .then(resp => resp.json())
                .then(data => {
                    // Support both list and dict (for endpoints with error)
                    if (Array.isArray(data)) {
                        if (data.length === 0) {
                            container.innerHTML = '<div class="text-gray-500">No news found.</div>';
                            return;
                        }
                        container.innerHTML = data.map(item => `
                            <div class="bg-white rounded-lg shadow p-5">
                                <div class="flex flex-col md:flex-row gap-4">
                                    ${item.image_url ? `<img src="${item.image_url}" alt="image" class="w-32 h-32 object-cover rounded-md border">` : ''}
                                    <div>
                                        <h2 class="text-xl font-bold mb-2">${item.title || item.short_description || item.summary || ''}</h2>
                                        <p class="text-gray-700 mb-2">${item.short_desc || item.short_description || item.summary || item.long_desc || ''}</p>
                                        <div class="text-sm text-gray-500 mb-1">${item.timestamp || item.date || ''}</div>
                                        ${item.anchor_link ? `<a href="${item.anchor_link}" target="_blank" class="text-blue-600 hover:underline">Read more</a>` : ''}
                                        ${item.article_url ? `<a href="${item.article_url}" target="_blank" class="text-blue-600 hover:underline">Read more</a>` : ''}
                                        ${item.link ? `<a href="${item.link}" target="_blank" class="text-blue-600 hover:underline">Read more</a>` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('');
                    } else if (data && data.endpoints) {
                        container.innerHTML = '<pre class="bg-gray-200 p-4 rounded">' + JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        container.innerHTML = '<div class="text-red-500">Error loading news.</div>';
                    }
                })
                .catch(() => {
                    container.innerHTML = '<div class="text-red-500">Failed to load news.</div>';
                });
        }
    </script>
</body>
</html>
    """, endpoints=[
        ("deepmind", "DeepMind"),
        ("wired", "Wired"),
        ("zdnet", "ZDNet"),
        ("nvidia", "Nvidia"),
        ("forbes", "Forbes"),
        ("thegradient", "The Gradient"),
        ("ainews", "AI News"),
        ("cyberexpress", "CyberExpress"),
        ("arstechnica", "ArsTechnica"),
        ("infosecurity", "InfoSecurity"),
        ("cyberscoop", "CyberScoop"),
        ("gbhackers", "GBHackers"),
    ])

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments, run Flask web server
        app.run(debug=True, port=5000)
    elif len(sys.argv) >= 2:
        endpoint = sys.argv[1].lower()
        if endpoint == "deepmind":
            scrape_deepmind()
        elif endpoint == "wired":
            scrape_wired()
        elif endpoint == "zdnet":
            scrape_zdnet_ai_carousels(save_csv=True)
        elif endpoint == "nvidia":
            scrape_nvidia(save_csv=True)
        elif endpoint == "forbes":
            scrape_forbes_ai(save_csv=True)
        elif endpoint == "thegradient":
            scrape_thegradient(save_csv=True)
        elif endpoint == "ainews":
            scrape_ainews(save_csv=True)
        else:
            print("Unknown endpoint. Use 'deepmind', 'wired', 'zdnet', 'nvidia', 'forbes', 'thegradient', or 'ainews'.")