from flask import Flask, render_template_string, redirect, url_for
import sys

app = Flask(__name__)

@app.route('/')
def landing():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>News Aggregator</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex flex-col items-center justify-center py-10">
        <h1 class="text-3xl font-bold mb-8">Select News Type</h1>
        <div class="flex gap-8">
            <a href="/ainews" class="px-8 py-4 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold text-xl">AI News</a>
            <a href="/cybernews" class="px-8 py-4 bg-green-600 text-white rounded-lg shadow hover:bg-green-700 transition font-semibold text-xl">Cyber News</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/ainews')
def ainews_page():
    # Render the AI News HTML directly
    return render_template_string("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>AI News Scraper</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
</head>
<body class=\"bg-gray-100 min-h-screen flex flex-col items-center justify-start py-10\">
    <h1 class=\"text-3xl font-bold mb-8\">AI News Scraper</h1>
    <div class=\"flex flex-wrap gap-4 mb-8\" id=\"button-group\">
        <button id=\"btn-deepmind\" onclick=\"fetchNews('deepmind')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">DeepMind</button>
        <button id=\"btn-wired\" onclick=\"fetchNews('wired')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">Wired</button>
        <button id=\"btn-zdnet\" onclick=\"fetchNews('zdnet')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">ZDNet</button>
        <button id=\"btn-nvidia\" onclick=\"fetchNews('nvidia')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">Nvidia</button>
        <button id=\"btn-forbes\" onclick=\"fetchNews('forbes')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">Forbes</button>
        <button id=\"btn-thegradient\" onclick=\"fetchNews('thegradient')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">The Gradient</button>
        <button id=\"btn-ainews\" onclick=\"fetchNews('ainews')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">AI News</button>
        <button id=\"btn-marktechpost\" onclick=\"fetchNews('marktechpost')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">Marktechpost</button>
        <button id=\"btn-datascience\" onclick=\"fetchNews('datascience')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">Towards Data Science</button>
    </div>
    <div id=\"news-container\" class=\"w-full max-w-3xl space-y-6\"></div>
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
        function showSpinner() {
            return `<div class='flex justify-center items-center py-8'><svg class='animate-spin h-8 w-8 text-blue-600' xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24'><circle class='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' stroke-width='4'></circle><path class='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z'></path></svg></div>`;
        }
        function fetchNews(endpoint) {
            setActiveButton(endpoint);
            const container = document.getElementById('news-container');
            container.innerHTML = showSpinner();
            fetch('/' + endpoint)
                .then(resp => resp.json())
                .then(data => {
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
    """)

@app.route('/cybernews')
def cybernews_page():
    # Render the Cyber News HTML directly
    return render_template_string("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Cyber News Scraper</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
</head>
<body class=\"bg-gray-100 min-h-screen flex flex-col items-center justify-start py-10\">
    <h1 class=\"text-3xl font-bold mb-8\">Cyber News Scraper</h1>
    <div class=\"flex flex-wrap gap-4 mb-8\" id=\"button-group\">
        <button id=\"btn-cyberexpress\" onclick=\"fetchNews('cyberexpress')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">CyberExpress</button>
        <button id=\"btn-arstechnica\" onclick=\"fetchNews('arstechnica')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">ArsTechnica</button>
        <button id=\"btn-infosecurity\" onclick=\"fetchNews('infosecurity')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">InfoSecurity</button>
        <button id=\"btn-cyberscoop\" onclick=\"fetchNews('cyberscoop')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">CyberScoop</button>
        <button id=\"btn-gbhackers\" onclick=\"fetchNews('gbhackers')\" class=\"px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition font-semibold\">GBHackers</button>
    </div>
    <div id=\"news-container\" class=\"w-full max-w-3xl space-y-6\"></div>
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
    """)

import ainews_scraper
import cybernews_scraper

# --- AI News Endpoints ---
@app.route('/deepmind')
def deepmind_api():
    return ainews_scraper.deepmind_api()

@app.route('/wired')
def wired_api():
    return ainews_scraper.wired_api()

@app.route('/zdnet')
def zdnet_api():
    return ainews_scraper.zdnet_api()

@app.route('/nvidia')
def nvidia_api():
    return ainews_scraper.nvidia_api()

@app.route('/forbes')
def forbes_api():
    return ainews_scraper.forbes_api()

@app.route('/thegradient')
def thegradient_api():
    return ainews_scraper.thegradient_api()

@app.route('/ainews')
def ainews_api():
    return ainews_scraper.ainews_api()

@app.route('/marktechpost')
def marktechpost_api():
    return ainews_scraper.marktechpost_api()

@app.route('/datascience')
def datascience_api():
    return ainews_scraper.datascience_api()

# --- Cyber News Endpoints ---
@app.route('/cyberexpress')
def cyberexpress_api():
    return cybernews_scraper.cyberexpress_endpoint()

@app.route('/arstechnica')
def arstechnica_api():
    return cybernews_scraper.arstechnica_endpoint()

@app.route('/infosecurity')
def infosecurity_api():
    return cybernews_scraper.infosecurity_endpoint()

@app.route('/cyberscoop')
def cyberscoop_api():
    return cybernews_scraper.cyberscoop_endpoint()

@app.route('/gbhackers')
def gbhackers_api():
    return cybernews_scraper.gbhackers_endpoint()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
