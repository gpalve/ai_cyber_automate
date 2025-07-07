from flask import Flask, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__)

# --- CyberExpress Scraper ---
def scrape_cyberexpress():
    url = "https://thecyberexpress.com/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="jeg_post")
    results = []
    for article in articles:
        title_tag = article.select_one(".jeg_post_title a")
        title = title_tag.get_text(strip=True) if title_tag else None
        desc_tag = article.select_one(".jeg_post_excerpt p")
        short_desc = desc_tag.get_text(strip=True) if desc_tag else None
        img_tag = article.select_one(".jeg_thumb img")
        image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None
        date_tag = article.select_one(".jeg_meta_date")
        timestamp = date_tag.get_text(strip=True) if date_tag else None
        results.append({
            "title": title,
            "short_description": short_desc,
            "image_url": image_url,
            "timestamp": timestamp,
            "source": url,
            "published": False
        })
    return results

def save_to_csv(data, csv_path, columns=None):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_new = pd.DataFrame(data)
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df = pd.concat([df_existing, df_new], ignore_index=True)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None
    else:
        df = df_new
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None
    df.drop_duplicates(inplace=True)
    df.to_csv(csv_path, index=False)

@app.route('/cyberexpress')
def cyberexpress_endpoint():
    data = scrape_cyberexpress()
    save_to_csv(data, "assets/csv/cyberexpress.csv", columns=["title", "short_description", "image_url", "timestamp", "source", "published"])
    return jsonify(data)

# --- ArsTechnica Scraper ---
def scrape_arstechnica():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    url = "https://arstechnica.com/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    grid_div = soup.find("div", class_="mx-auto grid grid-cols-1 gap-5 sm:max-w-6xl sm:grid-cols-2 sm:px-5 lg:grid-cols-3 xl:px-0")
    if grid_div:
        for article in grid_div.find_all("article"):
            title_tag = article.find(["h2", "h3", "a"])
            title = title_tag.get_text(strip=True) if title_tag else None
            desc_tag = article.find("p")
            short_desc = desc_tag.get_text(strip=True) if desc_tag else None
            img_tag = article.find("img")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None
            time_tag = article.find("time")
            timestamp = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None
            anchor_tag = article.find("a", href=True)
            anchor_link = anchor_tag["href"] if anchor_tag else None
            if anchor_link and not anchor_link.startswith("http"):
                anchor_link = "https://arstechnica.com" + anchor_link
            long_desc = None
            if anchor_link:
                try:
                    article_resp = requests.get(anchor_link, headers=headers)
                    article_soup = BeautifulSoup(article_resp.text, "html.parser")
                    content_div = article_soup.find("div", class_="article-content")
                    if content_div:
                        long_desc = content_div.get_text(separator=" ", strip=True)
                except Exception:
                    pass
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
    return results

@app.route('/arstechnica')
def arstechnica_endpoint():
    data = scrape_arstechnica()
    save_to_csv(data, "assets/csv/arstechnica.csv", columns=["title", "short_desc", "image_url", "timestamp", "source", "published", "anchor_link", "long_desc"])
    return jsonify(data)

# --- InfoSecurity Scraper ---
def scrape_infosecurity():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    base_url = "https://www.infosecurity-magazine.com"
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    # Find all columns with news items
    col_divs = soup.find_all("div", class_="col-1-3")
    seen_urls = set()
    for col in col_divs:
        content_items = col.find_all("div", class_="content-item")
        for item in content_items:
            if len(articles) >= 8:
                break
            info_div = item.find("div", class_="content-info")
            if not info_div:
                continue
            headline_tag = info_div.find("h3", class_="content-headline")
            a_tag = headline_tag.find("a") if headline_tag else None
            title = a_tag.get_text(strip=True) if a_tag else None
            article_url = a_tag["href"] if a_tag and a_tag.has_attr("href") else None
            if article_url and not article_url.startswith("http"):
                article_url = base_url + article_url
            # Skip duplicates by article_url
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)
            # Timestamp using carbon for formatting
            meta_div = info_div.find("div", class_="content-meta")
            timestamp = None
            if meta_div:
                time_tag = meta_div.find("time")
                if time_tag and time_tag.has_attr("datetime"):
                    try:
                        import carbon
                        dt = carbon.Carbon.parse(time_tag["datetime"])
                        timestamp = dt.format("j M Y, H:i")
                    except Exception:
                        timestamp = time_tag["datetime"]
                elif time_tag:
                    timestamp = time_tag.get_text(strip=True)
            # Image
            img_tag = item.find("img", class_="content-thumb")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None
            # Summary/teaser
            teaser_tag = item.find("p", class_="content-teaser")
            summary = teaser_tag.get_text(strip=True) if teaser_tag else None
            articles.append({
                "title": title,
                "summary": summary,
                "image_url": image_url,
                "timestamp": timestamp,
                "article_url": article_url
            })
        if len(articles) >= 8:
            break
    return articles

@app.route('/infosecurity')
def infosecurity_endpoint():
    csv_path = "assets/csv/infosecurity.csv"
    data = scrape_infosecurity()
    save_to_csv(data, csv_path, columns=["title", "summary", "image_url", "timestamp", "article_url"])
    # Only return the first 8 articles for frontend compatibility
    return jsonify(data[:8])

# --- CyberScoop Scraper ---
def scrape_cyberscoop():
    url = "https://cyberscoop.com/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    latest_posts_div = soup.find('div', class_='latest-posts__items')
    posts = []
    if latest_posts_div:
        articles = latest_posts_div.find_all('article', class_='post-item')
        for article in articles:
            # Title
            title_tag = article.find('h3', class_='post-item__title')
            link_tag = title_tag.find('a') if title_tag else None
            title = link_tag.get_text(strip=True) if link_tag else (title_tag.get_text(strip=True) if title_tag else None)
            link = link_tag['href'] if link_tag and link_tag.has_attr('href') else None
            # Image
            img_tag = article.find('img')
            img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
            # Timestamp (fetch from article page)
            timestamp = None
            if link:
                try:
                    link_full = link if link.startswith('http') else 'https://cyberscoop.com' + link
                    art_resp = requests.get(link_full, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                    date_p = art_soup.find('p', class_='single-article__date')
                    if date_p:
                        time_tag = date_p.find('time')
                        if time_tag and time_tag.has_attr('datetime'):
                            timestamp = time_tag['datetime']
                        elif time_tag:
                            timestamp = time_tag.get_text(strip=True)
                except Exception:
                    pass
            posts.append({
                'title': title,
                'link': link,
                'image_url': img_url,
                'timestamp': timestamp
            })
    return posts

@app.route('/cyberscoop')
def cyberscoop_endpoint():
    data = scrape_cyberscoop()
    save_to_csv(data, "assets/csv/cyberscoop.csv", columns=["title", "link", "image_url", "timestamp"])
    return jsonify(data)

# --- GBHackers Scraper ---
def scrape_gbhackers():
    url = "https://gbhackers.com/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception:
        return []
    results = []
    articles = soup.select('div.td_module_10.td_module_wrap.td-animation-stack')
    for article in articles:
        title_tag = article.select_one('h3.entry-title.td-module-title a')
        anchor_link = title_tag.get("href") if title_tag else None
        title = title_tag.get("title") if title_tag else None
        # Fetch image from the correct <img> tag inside <a class="td-image-wrap">
        img_tag = article.select_one('a.td-image-wrap img')
        image_url = None
        if img_tag:
            # Prefer data-img-url if present, else src
            image_url = img_tag.get("data-img-url") or img_tag.get("src")
        date_tag = article.select_one('span.td-post-date time')
        timestamp = date_tag.get_text(strip=True) if date_tag else None
        author_tag = article.select_one('span.td-post-author-name a')
        author = author_tag.get_text(strip=True) if author_tag else None
        desc_tag = article.select_one('div.td-excerpt')
        short_desc = desc_tag.get_text(strip=True) if desc_tag else None
        long_desc = None
        if anchor_link:
            try:
                article_resp = requests.get(anchor_link, headers=headers, timeout=10)
                article_resp.raise_for_status()
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = article_soup.find("div", class_="td-post-content")
                if not content_div:
                    divs = article_soup.find_all("div")
                    if divs:
                        content_div = max(divs, key=lambda d: len(d.get_text(strip=True)))
                if content_div:
                    long_desc = content_div.get_text(separator=" ", strip=True)
            except Exception:
                pass
        results.append({
            "title": title,
            "short_desc": short_desc,
            "image_url": image_url,
            "timestamp": timestamp,
            "source": url,
            "published": False,
            "anchor_link": anchor_link,
            "long_desc": long_desc,
            "author": author
        })
    return results

@app.route('/gbhackers')
def gbhackers_endpoint():
    data = scrape_gbhackers()
    save_to_csv(data, "assets/csv/gbhackers.csv", columns=["title", "short_desc", "image_url", "timestamp", "source", "published", "anchor_link", "long_desc", "author"])
    return jsonify(data)

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cyber News Scraper</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex flex-col items-center justify-start py-10">
    <h1 class="text-3xl font-bold mb-8">Cyber News Scraper</h1>
    <div class="flex flex-wrap gap-4 mb-8" id="button-group">
        {% for endpoint, label in endpoints %}
        <button id="btn-{{ endpoint }}" onclick="fetchNews('{{ endpoint }}')" class="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold">
            {{ label }}
        </button>
        {% endfor %}
    </div>
    <div id="news-container" class="w-full max-w-3xl space-y-6"></div>
    <script>
        let activeBtn = null;
        function setActiveButton(endpoint) {
            if (activeBtn) {
                activeBtn.classList.remove('bg-blue-800', 'ring-4', 'ring-blue-300');
                activeBtn.classList.add('bg-blue-600');
            }
            const btn = document.getElementById('btn-' + endpoint);
            if (btn) {
                btn.classList.remove('bg-blue-600');
                btn.classList.add('bg-blue-800', 'ring-4', 'ring-blue-300');
                activeBtn = btn;
            }
        }
        function fetchNews(endpoint) {
            setActiveButton(endpoint);
            const container = document.getElementById('news-container');
            container.innerHTML = '<div class="text-center text-gray-500">Loading...</div>';
            fetch('/' + endpoint)
                .then(resp => resp.json())
                .then(data => {
                    if (!Array.isArray(data)) {
                        container.innerHTML = '<div class="text-red-500">Error loading news.</div>';
                        return;
                    }
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
                })
                .catch(() => {
                    container.innerHTML = '<div class="text-red-500">Failed to load news.</div>';
                });
        }
    </script>
</body>
</html>
    """, endpoints=[
        ("cyberexpress", "CyberExpress"),
        ("arstechnica", "ArsTechnica"),
        ("infosecurity", "InfoSecurity"),
        ("cyberscoop", "CyberScoop"),
        ("gbhackers", "GBHackers"),
    ])

if __name__ == "__main__":
    app.run(debug=True, port=5001)
