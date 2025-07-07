
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def scrape_marktechpost(return_results=False, save_csv=True):
    url = "https://www.marktechpost.com/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # Only scrape articles inside the main parent class (top news)
    parent = soup.find("div", id="tdi_86", class_="td_block_inner td-mc1-wrap")
    if parent:
        article_blocks = parent.find_all("div", class_="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post")
        for block in article_blocks:
            meta_info = block.find("div", class_="td-module-meta-info")
            if not meta_info:
                continue
            # Title and link
            h3 = meta_info.find("h3", class_="entry-title td-module-title")
            a_tag = h3.find("a") if h3 else None
            title = a_tag.get("title") if a_tag and a_tag.has_attr("title") else (a_tag.get_text(strip=True) if a_tag else None)
            anchor_link = a_tag.get("href") if a_tag and a_tag.has_attr("href") else None

            # Category
            editor_date = meta_info.find("div", class_="td-editor-date")
            category = None
            if editor_date:
                cat_tag = editor_date.find("a", class_="td-post-category")
                category = cat_tag.get_text(strip=True) if cat_tag else None

            # Timestamp
            timestamp = None
            if editor_date:
                time_tag = editor_date.find("time", class_="entry-date updated td-module-date")
                if time_tag and time_tag.has_attr("datetime"):
                    timestamp = time_tag["datetime"]
                elif time_tag:
                    timestamp = time_tag.get_text(strip=True)

            # Fetch long description, author, and image from article page
            long_desc = None
            author = None
            image_url = None
            if anchor_link:
                try:
                    article_resp = requests.get(anchor_link, headers=headers, timeout=10)
                    article_soup = BeautifulSoup(article_resp.text, "html.parser")
                    # Long desc: first <p> inside <div class="td-post-content tagdiv-type">
                    content_div = article_soup.find("div", class_="td-post-content tagdiv-type")
                    if content_div:
                        first_p = content_div.find("p")
                        if first_p:
                            long_desc = first_p.get_text(separator=" ", strip=True)
                        else:
                            long_desc = content_div.get_text(separator=" ", strip=True)
                        # Image: first <img> inside content_div
                        img_tag = content_div.find("img")
                        if img_tag and img_tag.has_attr("src"):
                            image_url = img_tag["src"]
                    else:
                        # fallback: get all paragraphs
                        paragraphs = article_soup.find_all("p")
                        long_desc = " ".join([p.get_text(strip=True) for p in paragraphs]) if paragraphs else None
                        # fallback: first <img> in article
                        img_tag = article_soup.find("img")
                        if img_tag and img_tag.has_attr("src"):
                            image_url = img_tag["src"]
                    # Author: <div class="td-post-author-name">, then <a>
                    author_div = article_soup.find("div", class_="td-post-author-name")
                    if author_div:
                        author_a = author_div.find("a")
                        if author_a:
                            author = author_a.get_text(strip=True)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[ERROR] Failed to fetch long_desc/author/image for {anchor_link}: {e}")

            results.append({
                "title": title,
                "anchor_link": anchor_link,
                "category": category,
                "timestamp": timestamp,
                "source": url,
                "author": author,
                "image_url": image_url,
                "long_desc": long_desc
            })



    if save_csv:
        csv_path = "assets/csv/marktechpost.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
        else:
            df_existing = pd.DataFrame(columns=["title", "anchor_link", "category", "timestamp", "source", "author", "image_url", "long_desc"])
        new_df = pd.DataFrame(results)
        combined_df = pd.concat([df_existing, new_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["title", "timestamp"], inplace=True)
        combined_df.to_csv(csv_path, index=False)
        print(f"Saved {len(combined_df)} unique news items to {csv_path}")

    if return_results:
        # Save as JSON for web viewing
        import json
        json_path = "assets/csv/marktechpost.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON to {json_path}")
        return results

if __name__ == "__main__":
    scrape_marktechpost(save_csv=True)
