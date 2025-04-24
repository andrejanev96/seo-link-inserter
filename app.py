from flask import Flask, request, render_template_string
from bs4 import BeautifulSoup, NavigableString
import re
import random

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Internal Tool</title>
    <style>
        body {
            max-width: 1100px;
            margin: auto;
            font-family: 'Segoe UI', sans-serif;
            padding: 30px;
            background: #f7f8fa;
            color: #333;
        }
        h1, h2 {
            text-align: center;
            color: #222;
        }
        textarea, input[type=text], input[type=number], select {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
        }
        input[type=number] { width: 100%; }
        .form-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .form-row label {
            flex: 1;
            min-width: 180px;
            font-weight: bold;
        }
        .form-row input, .form-row select {
            width: 100%;
            font-weight: normal;
        }
        .remove-btn {
            background-color: #ff4d4d;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 14px;
            align-self: flex-start;
            margin-top: 22px;
        }
        .remove-btn:hover { background-color: #cc0000; }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin-top: 10px;
            cursor: pointer;
        }
        .output-box {
            border: 1px solid #ccc;
            padding: 20px;
            margin-top: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .highlight { background-color: #ffff99; }
        .rendered-html {
            border: 1px solid #ccc;
            padding: 15px;
            background: #fff;
            border-radius: 5px;
        }
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        footer {
            text-align: center;
            font-size: 14px;
            color: #777;
            margin-top: 50px;
        }
    </style>
    <script>
        function addRow(keyword = "") {
            const container = document.getElementById('link-rows');
            const row = document.createElement('div');
            row.className = 'form-row';
            row.innerHTML = `
                <label>Keyword:<br><input name="keywords" type="text" value="${keyword}" required autocomplete="off"></label>
                <button type="button" class="remove-btn" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(row);
        }

        function copyHTML() {
            const html = document.getElementById("html-output").value;
            const clean = html.replace(/<mark class="highlight">/g, "").replace(/<\/mark>/g, "");
            navigator.clipboard.writeText(clean);
            alert("HTML copied without highlights!");
        }

        function clearForm() {
            window.location.href = "/";
        }

        function clearHTML() {
            document.querySelector('textarea[name="html_input"]').value = "";
        }
    </script>
</head>
<body>
    <div style="text-align:center; margin-bottom: 10px;">
        <h1 style="margin: 0;">Link Enrichment</h1>
    </div>

    <form method="post" autocomplete="off">
        <input type="text" name="fake_autofill" style="display:none;" autocomplete="off">

        <h3>Paste Your Article HTML:</h3>
        <textarea name="html_input" required autocomplete="off">{{ html_input or '' }}</textarea>

        <h3>Keywords:</h3>
        <div id="link-rows">
            {% for pair in keyword_url_pairs %}
            <div class="form-row">
                <label>Keyword:<br><input name="keywords" type="text" value="{{ pair.keyword }}" required autocomplete="off"></label>
                {% if action == "analyze" or action == "insert" %}
                    <label>URL:<br><input name="urls" type="text" value="{{ pair.url }}" autocomplete="off"></label>
                    <label>Target:<br>
                        <select name="targets" autocomplete="off">
                            <option value="_self" {% if pair.target == "_self" %}selected{% endif %}>_self</option>
                            <option value="_blank" {% if pair.target == "_blank" %}selected{% endif %}>_blank</option>
                        </select>
                    </label>
                    <label>Title Format:<br><input name="titles" type="text" value="{{ pair.title }}" autocomplete="off"></label>
                    <label>Rel:<br>
                        <select name="rels" autocomplete="off">
                            <option value="" {% if pair.rel == "" %}selected{% endif %}>None</option>
                            <option value="nofollow" {% if pair.rel == "nofollow" %}selected{% endif %}>nofollow</option>
                            <option value="noopener" {% if pair.rel == "noopener" %}selected{% endif %}>noopener</option>
                            <option value="nofollow noopener" {% if pair.rel == "nofollow noopener" %}selected{% endif %}>nofollow noopener</option>
                            <option value="sponsored" {% if pair.rel == "sponsored" %}selected{% endif %}>sponsored</option>
                            <option value="ugc" {% if pair.rel == "ugc" %}selected{% endif %}>ugc</option>
                        </select>
                    </label>
                    <label>Max Links (up to {{ keyword_counts[pair.keyword] }}):<br>
                        <input name="max_links" type="number" value="{{ pair.max_links }}" min="1" autocomplete="off">
                    </label>
                {% endif %}
                <button type="button" class="remove-btn" onclick="this.parentElement.remove()">Remove</button>
            </div>
            {% endfor %}
        </div>

        <button type="button" onclick="addRow()">+ Add Another</button>
        <br><br>
        <label><input type="checkbox" name="highlight" {% if highlight %}checked{% endif %}> Highlight Inserted Links</label>

        <div class="btn-group">
            <button name="action" value="analyze" type="submit">Analyze</button>
            {% if action == "analyze" or action == "insert" %}
            <button name="action" value="insert" type="submit">Insert Links</button>
            {% endif %}
            <button type="button" onclick="clearHTML()">Clear HTML</button>
            <button type="button" onclick="clearForm()">Clear All</button>
        </div>
    </form>

    {% if result %}
    <div class="output-box">
        <h2>🧾 Updated HTML</h2>
        <textarea readonly id="html-output">{{ result|safe }}</textarea>
        <br><button onclick="copyHTML()">📋 Copy Updated HTML (No Highlights)</button>
    </div>

    <div class="output-box">
        <h2>🌐 Rendered HTML</h2>
        <div class="rendered-html">{{ result|safe }}</div>
    </div>
    {% endif %}

    {% if changes %}
    <div class="output-box">
        <h2>✅ Changes Made ({{ total_insertions }} total):</h2>
        <ul>
            {% for change in changes %}
                <li>{{ change }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <footer>
        © 2025 Created by Andrej Janev
    </footer>
</body>
</html>
"""

def insert_links(html, link_data, highlight=True):
    soup = BeautifulSoup(html, "html.parser")
    changes = []
    total_insertions = 0
    all_tags = soup.find_all(["p", "li"])
    random.seed()

    for data in link_data:
        keyword_lower = data["keyword"].lower()
        url = data["url"]
        max_links = data["max_links"]
        count = 0

        eligible_tags = [
            tag for tag in all_tags
            if keyword_lower in tag.get_text().lower()
            and not tag.find("a", string=re.compile(re.escape(data["keyword"]), re.IGNORECASE))
        ]
        random.shuffle(eligible_tags)

        for tag in eligible_tags:
            if count >= max_links:
                break

            title = data["title"].replace("{keyword}", data["keyword"])
            rel = f' rel="{data["rel"]}"' if data["rel"] else ""
            anchor = f'<a href="{url}" title="{title}" target="{data["target"]}"{rel}>\\1</a>'
            if highlight:
                anchor = f'<mark class="highlight">{anchor}</mark>'
            pattern = re.compile(r'\b(' + re.escape(data["keyword"]) + r')\b', flags=re.IGNORECASE)
            new_html, subs = pattern.subn(anchor, str(tag), count=1)

            if subs:
                new_tag = BeautifulSoup(new_html, "html.parser")
                tag.replace_with(new_tag)
                count += 1
                total_insertions += 1
                snippet = re.search(r'>([^<]{0,100})<', new_html)
                snippet_text = snippet.group(1).strip() if snippet else '[No snippet]'
                changes.append(f'Inserted \"{data["keyword"]}\" → {url} in: “…{snippet_text}…”')

    return soup.prettify(), changes, total_insertions

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(
            TEMPLATE,
            html_input="",
            keyword_url_pairs=[{
                "keyword": "",
                "url": "",
                "max_links": 1,
                "target": "_self",
                "title": "{keyword} Ammo For Sale",
                "rel": ""
            }],
            keyword_counts={},
            changes=[],
            total_insertions=0,
            result="",
            highlight=True,
            action=""
        )

    # POST = analyze or insert
    html_input = request.form["html_input"]
    keywords = request.form.getlist("keywords")
    urls = request.form.getlist("urls")
    max_links_list = request.form.getlist("max_links")
    targets = request.form.getlist("targets")
    titles = request.form.getlist("titles")
    rels = request.form.getlist("rels")
    highlight = "highlight" in request.form
    action = request.form.get("action")

    keyword_url_pairs = []
    keyword_counts = {}
    changes = []
    total_insertions = 0
    result = ""

    for i, keyword in enumerate(keywords):
        keyword = keyword.strip()
        if not keyword:
            continue
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', html_input, re.IGNORECASE))
        keyword_counts[keyword] = count

        url = urls[i] if i < len(urls) else ""
        max_links = int(max_links_list[i]) if i < len(max_links_list) and max_links_list[i].isdigit() else count
        target = targets[i] if i < len(targets) else "_self"
        title = titles[i] if i < len(titles) else "{keyword} Ammo For Sale"
        rel = rels[i] if i < len(rels) else ""

        keyword_url_pairs.append({
            "keyword": keyword,
            "url": url,
            "max_links": max_links,
            "target": target,
            "title": title,
            "rel": rel
        })

    if action == "insert":
        result, changes, total_insertions = insert_links(html_input, keyword_url_pairs, highlight)

    return render_template_string(
        TEMPLATE,
        html_input=html_input,
        keyword_url_pairs=keyword_url_pairs,
        keyword_counts=keyword_counts,
        changes=changes,
        total_insertions=total_insertions,
        result=result,
        highlight=highlight,
        action=action
    )

if __name__ == "__main__":
    app.run(debug=True)