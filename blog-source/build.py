# For every .md file in the blog-source directory, create a .html file in the blog directory
# The .md file contains a yaml header and markdown content

import os
import re
import uuid
import yaml
import markdown
import json

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor
from markdown import Extension

from bs4 import BeautifulSoup, Comment

# Resolve all paths relative to the repo root (parent of blog-source/) so the
# script works regardless of the current working directory.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_SOURCE_DIR = os.path.join(REPO_ROOT, "blog-source")
SNIPPETS_DIR = os.path.join(BLOG_SOURCE_DIR, "snippets")
TEMPLATE_PATH = os.path.join(BLOG_SOURCE_DIR, "template.html")
ARTICLES_JSON_PATH = os.path.join(REPO_ROOT, "blog", "articles.json")
RETIRED_ARTICLES_JSON_PATH = os.path.join(REPO_ROOT, "blog", "retired-articles.json")
SITEMAP_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

SITE_ORIGIN = "https://joepitts.co.uk"

created_files = []
# IDs of the code snippets in the post currently being processed. Reset per file
# (see main loop) so ClipboardJS selectors never leak across posts.
codeSnippetIds = []

class HeaderAnchorPreprocessor(Preprocessor):
     def run(self, lines):
        new_lines = []
        for line in lines:
            match = re.match(r'##\s+(.*)', line)  # Match level 2 headers
            if match:
                text = match.group(1)
                header_id = text.lower().replace(' ', '_')  # Create an ID from the header text
                # Format the header as specified
                new_line = f'<a class="anchor" href="#{header_id}">\n    <h2 id="{header_id}">{text}</h2>\n</a>'
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        return new_lines


class CodeBlockPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        code_block_started = False
        for line in lines:
            if line.startswith('```'):
                if not code_block_started:  # start of code block
                    code_block_started = True
                    lang = line.strip().replace("'","").replace("`","")
                    lang = lang if len(lang) > 0 else "code"
                    code_id = f"code-{uuid.uuid4().hex}"
                    # Add the language and ID as an HTML comment
                    new_lines.append(f"<!--lang:{lang},id:{code_id}-->")
                    codeSnippetIds.append(code_id)
                else:  # end of code block
                    code_block_started = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        return new_lines


class SnippetInjectionPreprocessor(Preprocessor):
    def __init__(self, md, snippets_dir=SNIPPETS_DIR):
        super().__init__(md)
        self.snippets_dir = snippets_dir

    def run(self, lines):
        new_lines = []
        snippet_pattern = re.compile(r'\{\{snippet:([^\}]+)\}\}')

        for line in lines:
            match = snippet_pattern.search(line)
            while match:
                snippet_filename = match.group(1).strip()
                snippet_path = os.path.join(self.snippets_dir, snippet_filename)

                if os.path.exists(snippet_path):
                    with open(snippet_path, 'r', encoding='utf-8') as f:
                        snippet_content = f.read()
                    line = line[:match.start()] + snippet_content + line[match.end():]
                else:
                    line = line[:match.start()] + f"<p>Snippet '{snippet_filename}' not found.</p>" + line[match.end():]

                match = snippet_pattern.search(line)

            new_lines.append(line)

        return new_lines



class CodeSnippetPostprocessor(Postprocessor):
    def run(self, text):
        soup = BeautifulSoup(text, 'html.parser')

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            # Check if comment contains language and id information
            if 'lang:' in comment and 'id:' in comment:
                parts = comment.split(',')
                lang = parts[0].split(':')[1]
                code_id = parts[1].split(':')[1].strip()

                # Find the next code block. With Pygments installed, codehilite
                # emits <div class="codehilite"><pre>; without it, a bare
                # <pre class="codehilite">. Handle both so the copy button always
                # renders.
                code_block = comment.find_next(['div', 'pre'], class_='codehilite')

                if code_block:
                    # Add id to the pre tag (the block itself if it's a bare <pre>)
                    pre_tag = code_block.find('pre') or (code_block if code_block.name == 'pre' else None)
                    if pre_tag:
                        pre_tag['id'] = code_id

                    # Construct the new HTML structure
                    new_code_html = BeautifulSoup(f"""
                        <div class="codeSnippet">
                            <div class="double-val-label">
                                <span class="{lang}">{lang.upper()}</span>
                                <span data-clipboard-target="#{code_id}" id="{code_id}-btn">Copy</span>
                            </div>
                            {str(code_block)}
                        </div>
                    """, 'html.parser')

                    code_block.replace_with(new_code_html)

                # Remove the comment
                comment.extract()

        return str(soup)



class JoesExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(HeaderAnchorPreprocessor(md), 'custom_header', 175)
        md.preprocessors.register(CodeBlockPreprocessor(md), 'code_block', 25)
        md.preprocessors.register(SnippetInjectionPreprocessor(md), 'snippet_injection', 20)
        md.postprocessors.register(CodeSnippetPostprocessor(md), 'code_snippet', 25)

def estimate_reading_time(markdown_content):
    # Strip unnecessary Markdown formatting
    text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_content)  # Remove image links
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove hyperlinks but keep link text
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with one

    # Calculate word count
    words = text.split()
    word_count = len(words)

    # Estimate reading time
    min_time = word_count // 120
    max_time = word_count // 70

    # Adjust for a more human-readable format
    if min_time == max_time:
        return f"{min_time}-{min_time+1} Minutes"
    else:
        return f"{min_time}-{max_time} Minutes"

def get_file_list():
    """Get a list of markdown files in the blog-source directory"""
    file_list = []
    for root, dirs, files in os.walk(BLOG_SOURCE_DIR):
        for file in files:
            if file.endswith(".md"):
                file_list.append(os.path.join(root, file))
    return file_list


# Matches a frontmatter delimiter line (a line containing only ---).
FRONTMATTER_DELIMITER = re.compile(r'^---\s*$', re.MULTILINE)


def parse_file(file: str):
    """Read a markdown file once and return (yaml_config, markdown_body).

    The frontmatter is split on delimiter *lines* (^---$) with a bounded
    max split, so a `---` thematic break or fenced-code content in the body no
    longer truncates the article or corrupts the YAML.
    """
    with open(file, "r", encoding="utf-8") as f:
        raw = f.read()

    parts = FRONTMATTER_DELIMITER.split(raw, maxsplit=2)
    if len(parts) < 3:
        raise ValueError(
            f"{file}: expected YAML frontmatter delimited by two '---' lines"
        )

    _before, frontmatter, body = parts
    try:
        yaml_config = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{file}: invalid YAML frontmatter: {exc}") from exc

    return yaml_config, body


REQUIRED_KEYS = ("outputPath", "headline", "summary", "date", "tags")


def validate_config(file: str, yaml_config: dict):
    """Ensure every required frontmatter key is present, naming the file on error."""
    missing = [key for key in REQUIRED_KEYS if key not in yaml_config]
    if missing:
        raise ValueError(f"{file}: missing required frontmatter key(s): {', '.join(missing)}")


def normalize_link(output_path: str) -> str:
    """Turn an outputPath (e.g. './blog/foo.html' or '/blog/foo.html') into a
    canonical site-absolute link '/blog/foo.html' with forward slashes."""
    link = output_path.replace("\\", "/").lstrip(".")
    if not link.startswith("/"):
        link = "/" + link
    return link


def parse_date(file: str, raw_date):
    """Parse a dd/mm/yyyy date into a UTC epoch timestamp (tz-independent)."""
    try:
        dt = datetime.strptime(str(raw_date), "%d/%m/%Y")
    except ValueError as exc:
        raise ValueError(
            f"{file}: date '{raw_date}' is not in the required dd/mm/yyyy format"
        ) from exc
    return dt.replace(tzinfo=timezone.utc).timestamp()


def create_html_file(file, yaml_config, html_content, reading_time):
    """Create the html file and return its articles.json entry dict."""
    output_path = yaml_config["outputPath"]
    link = normalize_link(output_path)
    social_image = yaml_config.get("socialImage", None)
    headline = yaml_config["headline"]
    summary = yaml_config["summary"]
    date = parse_date(file, yaml_config["date"])
    # Tags is a list of tags
    tags = yaml_config["tags"]

    # Read in template.html using beautiful soup
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_html = f.read()
    soup = BeautifulSoup(template_html, 'html.parser')


    # Set the schema.org JSON-LD
    schema_json = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "description": summary,
        "datePublished": datetime.fromtimestamp(date, tz=timezone.utc).strftime("%Y-%m-%d"),
        "author": {
            "@type": "Person",
            "name": "Joe Pitts",
            "additionalName": "David",
            "affiliation": "TrueNorthIT",
            "jobTitle": "Senior Solutions Developer",
            "url": "https://joepitts.co.uk",
            "sameAs": [
                "https://www.facebook.com/Joe.Pittsy",
                "https://www.linkedin.com/in/JoePittsy",
                "https://twitter.com/JoePittsy",
                "https://www.instagram.com/JoePittsy/",
            ]
        }
    }
    # Add the tags to the schema
    schema_json["keywords"] = ",".join(tags)
    # Add the schema to the soup as a script tag in the head
    script = soup.new_tag("script", type="application/ld+json")
    script.string = json.dumps(schema_json, indent=4)
    soup.find("head").append(script)

    # Add the twitter card meta tags
    soup.find("meta", {"name": "twitter:description"})["content"] = summary
    soup.find("meta", {"name": "twitter:title"})["content"] = f"Joe Pitts | {headline}"

    # Add the open graph meta tags
    canonical_url = f"{SITE_ORIGIN}{link}"
    soup.find("meta", {"property": "og:title"})["content"] = headline
    soup.find("meta", {"property": "og:description"})["content"] = summary
    soup.find("meta", {"property": "og:url"})["content"] = canonical_url

    # Add a canonical link
    canonical_tag = soup.new_tag("link", rel="canonical", href=canonical_url)
    soup.find("head").append(canonical_tag)

    if social_image:
        soup.find("meta", {"property": "og:image"})["content"] = f"{SITE_ORIGIN}{social_image}"
        soup.find("meta", {"name": "twitter:image"})["content"] =  f"{SITE_ORIGIN}{social_image}"



    # Set the title blogPostTitle
    soup.title.string = headline
    soup.find("h1", {"id": "blogPostTitle"}).string = headline

    # Set the headline
    soup.find("meta", {"name": "description"})["content"] = summary

    # Set the reading time
    soup.find("p", {"id": "estimatedReadingTime"}).string = reading_time
    # Set the publication date
    soup.find("date", {"id": "publicationDate"}).string = datetime.fromtimestamp(date, tz=timezone.utc).strftime("%d %B %Y")

    # Set the article content
    soup.find("article", {"id": "blogPostContent"}).append(BeautifulSoup(html_content, 'html.parser'))

    # Add the code snippet copy functionality for THIS post's snippets only.
    script = soup.new_tag("script", defer="")
    buttonIds = [f"#{codeSnippetId}-btn" for codeSnippetId in codeSnippetIds]
    buttonIdString = ",".join(buttonIds)
    script.string = f"""
        (function () {{
            // This should include all of the code snippets
            new ClipboardJS("{buttonIdString}");
        }})();
    """
    soup.find("body").append(script)

    # Add code snippet scripts to the head
    snippet_scripts = yaml_config.get('snippetScripts', [])
    print(f"Adding snippet scripts: {snippet_scripts}")
    for script_file in snippet_scripts:
        script_path = os.path.join(SNIPPETS_DIR, script_file)
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            script_tag = soup.new_tag('script', type='text/javascript')
            script_tag.string = script_content
            soup.find('head').append(script_tag)
            print(f"Added snippet script: {script_file}")
        else:
            print(f"Warning: Snippet script '{script_file}' not found.")

    # Resolve the output file under the repo root and create parent dirs
    output_file = os.path.join(REPO_ROOT, link.lstrip("/"))
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create the html file using the soup with indentation and formatting
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
        created_files.append(output_file)

    # Return this post's articles.json entry
    return {
        "headline": headline,
        "summary": summary,
        "link": link,
        "date": date,
        "tags": tags,
    }


def write_articles_json(generated):
    """Merge freshly-generated posts into articles.json.

    - Upsert every .md-generated post (add new / update existing by link).
    - Preserve legacy hand-authored posts that have no .md source but a live
      HTML file (e.g. the older MXChip / Power Automate posts).
    - Prune only true phantoms: entries whose target HTML file no longer exists
      (e.g. posts whose source and output were deleted).
    """
    by_link = {}
    for article in _load_articles(ARTICLES_JSON_PATH):
        by_link[article["link"]] = article
    for article in generated:
        by_link[article["link"]] = article

    articles = [
        a for a in by_link.values()
        if os.path.exists(os.path.join(REPO_ROOT, a["link"].lstrip("/")))
    ]
    articles = sorted(articles, key=lambda x: x['date'], reverse=True)

    os.makedirs(os.path.dirname(ARTICLES_JSON_PATH), exist_ok=True)
    with open(ARTICLES_JSON_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps({"articles": articles}, indent=4))


def prettify(element, indent='  '):
    """Function to add indentation and newlines for pretty-printing an XML element."""
    queue = [(0, element)]  # (level, element)
    while queue:
        level, element = queue.pop(0)
        children = list(element)
        if children:
            element.text = '\n' + indent * (level+1)  # for child open
        if queue:
            element.tail = '\n' + indent * queue[0][0]  # for sibling open
        else:
            element.tail = '\n' + indent * (level-1)  # for parent close
        queue[0:0] = [(level + 1, child) for child in children]

def _load_articles(path):
    """Load an articles-style JSON file, returning its list (empty if absent)."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("articles", [])


def _add_sitemap_entry(root, link, date, priority="0.8"):
    url_elem = ET.SubElement(root, "url")
    ET.SubElement(url_elem, "loc").text = SITE_ORIGIN + link
    date_str = datetime.fromtimestamp(date, tz=timezone.utc).strftime('%Y-%m-%d')
    ET.SubElement(url_elem, "lastmod").text = date_str
    ET.SubElement(url_elem, "changefreq").text = "monthly"
    ET.SubElement(url_elem, "priority").text = priority


def update_sitemap(sitemap_file=SITEMAP_PATH, articles_json=ARTICLES_JSON_PATH):
    # Register the default namespace
    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Parse the existing sitemap with namespace
    tree = ET.parse(sitemap_file)
    root = tree.getroot()

    # Remove old blog entries (everything under /blog/ is rebuilt below)
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    root[:] = [elem for elem in root
               if elem.find(f'{ns}loc') is not None
               and '/blog/' not in elem.find(f'{ns}loc').text]

    # Current posts (from build) + legacy/retired posts that still have a live
    # HTML file. Retired posts are otherwise orphaned from the sitemap, so
    # include them here to keep them indexable across rebuilds.
    current = _load_articles(articles_json)
    retired = _load_articles(RETIRED_ARTICLES_JSON_PATH)

    seen = set()
    for article in current + retired:
        link = article["link"]
        file_path = os.path.join(REPO_ROOT, link.lstrip("/"))
        if link in seen or not os.path.exists(file_path):
            continue
        seen.add(link)
        _add_sitemap_entry(root, link, article["date"])

    # Blog index page, dated to the newest current post
    if current:
        _add_sitemap_entry(root, "/blog/", max(a["date"] for a in current))

    # Pretty-print the XML
    prettify(root)

    # Write the updated sitemap back
    tree.write(sitemap_file, xml_declaration=True, encoding='utf-8')

if __name__ == "__main__":
    file_list = get_file_list()
    articles = []
    for file in file_list:
        # Reset per-post code snippet IDs so ClipboardJS selectors don't leak
        # from one post into the next.
        codeSnippetIds.clear()

        yaml_config, markdown_body = parse_file(file)
        validate_config(file, yaml_config)
        html_content = markdown.markdown(
            markdown_body, extensions=[JoesExtension(), 'fenced_code', 'codehilite']
        )
        reading_time = estimate_reading_time(markdown_body)
        articles.append(create_html_file(file, yaml_config, html_content, reading_time))

    # Rebuild articles.json from scratch (prunes entries for deleted sources)
    write_articles_json(articles)
    update_sitemap()
    for file in created_files:
        print(os.path.abspath(file))
