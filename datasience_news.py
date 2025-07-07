import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def scrape_towardsdatascience(return_results=False, save_csv=True):
    url = "https://towardsdatascience.com/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    parent_ul = soup.find("ul", class_="wp-block-post-template is-layout-grid wp-container-core-post-template-is-layout-c37e0d04 wp-block-post-template-is-layout-grid is-entire-card-clickable")
    if not parent_ul:
        print("Could not find main news list.")
        return []

    for li in parent_ul.find_all("li", recursive=False):
        # Image
        image_url = None
        figure = li.find("figure", class_="wp-block-post-featured-image")
        if figure:
            img = figure.find("img")
            if img and img.has_attr("src"):
                image_url = img["src"]

        # Title, category
        title = None
        anchor_link = None
        category = None
        title_group = li.find("div", class_="wp-block-group is-reversed is-vertical is-layout-flex wp-container-core-group-is-layout-ea0cb840 wp-block-group-is-layout-flex")
        if title_group:
            h2 = title_group.find("h2")
            if h2:
                a_tag = h2.find("a")
                if a_tag:
                    title = a_tag.get_text(strip=True)
                    anchor_link = a_tag.get("href")
            cat_a = title_group.find("a", class_="is-taxonomy-category wp-elements-361e18664420f2745478f0373bcee025 wp-block-tenup-post-primary-term has-text-color has-text-secondary-color has-eyebrow-1-font-size")
            if cat_a:
                category = cat_a.get_text(strip=True)

        # Short desc
        short_desc = None
        excerpt_p = li.find("p", class_="wp-block-post-excerpt__excerpt")
        if excerpt_p:
            short_desc = excerpt_p.get_text(strip=True)

        # Author
        author = None
        author_a = li.find("a", class_="wp-block-post-author-name__link")
        if author_a:
            author = author_a.get_text(strip=True)

        # Timestamp
        timestamp = None
        time_tag = li.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            timestamp = time_tag["datetime"]

        # Long description: from article page, <div class="entry-content wp-block-post-content has-global-padding is-layout-constrained wp-block-post-content-is-layout-constrained">
        long_desc = None
        if anchor_link:
            try:
                article_resp = requests.get(anchor_link, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                content_div = article_soup.find("div", class_="entry-content wp-block-post-content has-global-padding is-layout-constrained wp-block-post-content-is-layout-constrained")
                if content_div:
                    # Get all paragraphs and list items for a more complete summary
                    ps = content_div.find_all(["p", "li"])
                    long_desc = " ".join([p.get_text(strip=True) for p in ps]) if ps else content_div.get_text(separator=" ", strip=True)
            except Exception as e:
                print(f"[ERROR] Failed to fetch long_desc for {anchor_link}: {e}")

        results.append({
            "title": title,
            "anchor_link": anchor_link,
            "category": category,
            "short_desc": short_desc,
            "author": author,
            "image_url": image_url,
            "timestamp": timestamp,
            "long_desc": long_desc,
            "source": url
        })

    if save_csv:
        csv_path = "assets/csv/towardsdatascience.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} news items to {csv_path}")

    if return_results:
        json_path = "assets/csv/towardsdatascience.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON to {json_path}")
        return results

if __name__ == "__main__":
    scrape_towardsdatascience(save_csv=True)
