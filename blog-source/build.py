# For every .md file in the blog-source directory, create a .html file in the blog directory
# The .md file contains a yaml header and markdown content

import os
import re
import uuid
import yaml
import markdown
import datetime
import json

import xml.etree.ElementTree as ET
import os
import json
from datetime import datetime

from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor
from markdown import Extension

from bs4 import BeautifulSoup, Comment

created_files = []
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
    def __init__(self, md, snippets_dir='blog-source/snippets'):
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
                    with open(snippet_path, 'r') as f:
                        snippet_content = f.read()
                    line = line[:match.start()] + snippet_content + line[match.end():]
                else:
                    line = line[:match.start()] + f"<p>Snippet '{snippet_filename}' not found.</p>" + line[match.end():]

                match = snippet_pattern.search(line)

            new_lines.append(line)

        return new_lines



from bs4 import BeautifulSoup, Comment

class CodeSnippetPostprocessor(Postprocessor):
    def run(self, text):
        soup = BeautifulSoup(text, 'html.parser')

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            # Check if comment contains language and id information
            if 'lang:' in comment and 'id:' in comment:
                parts = comment.split(',')
                lang = parts[0].split(':')[1]
                code_id = parts[1].split(':')[1].strip()

                # Find the next code block
                code_block = comment.find_next('div', class_='codehilite')

                if code_block:
                    # Add id to the pre tag
                    pre_tag = code_block.find('pre')
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
    """Get a list of files in the blog-source directory"""
    file_list = []
    for root, dirs, files in os.walk("blog-source"):
        for file in files:
            if file.endswith(".md"):
                file_list.append(os.path.join(root, file))
    return file_list


def get_yaml_header(file: str):
    """Parse the yaml header from the file"""

    # Example yaml header:
    # headline: Test Markdown Blog!
    # summary: Generating Blog Posts from Markdown
    # date: 12/11/2023
    # outputPath: /blog/test/newPost.html
    # tags: 
    #     - Python

    with open(file, "r") as f:
        yaml_header = f.read().split("---")[1]
        yaml_header = yaml.safe_load(yaml_header)
    return yaml_header


def get_html_content_and_esitamated_reading_time(file: str):
    """Parse the markdown content from the file"""
    with open(file, "r") as f:
        markdown_content = f.read().split("---")[2]
        html_content = markdown.markdown(markdown_content, extensions=[JoesExtension(), 'fenced_code', 'codehilite'])
    return html_content, estimate_reading_time(markdown_content)


def create_html_file(yaml_config, html_content, reading_time):
    """Create the html file"""
    output_path = yaml_config["outputPath"]
    social_image = yaml_config.get("socialImage", None)
    headline = yaml_config["headline"]
    summary = yaml_config["summary"]
    # Date is in the format: dd/mm/yyyy convert it to an epoch timestamp
    date = datetime.strptime(yaml_config["date"], "%d/%m/%Y").timestamp()
    # Tags is a list of tags
    tags = yaml_config["tags"]

    # Create the html file in the blog directory respecting the output path
    # Example: /blog/test/newPost.html
    # Create the directories if they don't exist

    # Read in template.html using beautiful soup
    with open("blog-source/template.html", "r") as f:
        template_html = f.read()
    soup = BeautifulSoup(template_html, 'html.parser')


    # Set the schema.org JSON-LD
    schema_json = {
        "@context": "http://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "description": summary,
        "datePublished": datetime.fromtimestamp(date).strftime("%Y-%m-%d"),
        "author": {
            "@type": "Person",
            "name": "Joe Pitts",
            "additionalName": "David",
            "affiliation": "TrueNorthIT",
            "jobTitle": "Solutions Developer",
            "url": "https://JoePitts.co.uk",
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
    
    # <meta name="twitter:card" content="summary" />
    # <meta name="twitter:site" content="@JoePittsy" />
    # <meta name="twitter:description" content="Day Five of Advent of Code 2020!" name="description" />
    # <meta name="twitter:title" content="Joe Pitts | Advent of Code Day 5" />
    # <meta name="twitter:creator" content="@JoePittsy" />    

    # Add the twitter card meta tags
    soup.find("meta", {"name": "twitter:description"})["content"] = summary
    soup.find("meta", {"name": "twitter:title"})["content"] = f"Joe Pitts | {headline}"


    # <meta property="og:title" content="Advent of Code Day 5" />
    # <meta property="og:description" content="Day Five of Advent of Code 2020!" />
    # <meta property="og:url" content="https://joepitts.co.uk/blog/advent-of-code-day-05.html" />

    # Add the open graph meta tags
    soup.find("meta", {"property": "og:title"})["content"] = headline
    soup.find("meta", {"property": "og:description"})["content"] = summary
    soup.find("meta", {"property": "og:url"})["content"] = f"https://joepitts.co.uk{output_path}"
    
    if social_image:
        soup.find("meta", {"property": "og:image"})["content"] = f"https://joepitts.co.uk{social_image}"
        soup.find("meta", {"name": "twitter:image"})["content"] =  f"https://joepitts.co.uk{social_image}"



    # Set the title blogPostTitle
    soup.title.string = headline
    soup.find("h1", {"id": "blogPostTitle"}).string = headline

    # Set the headline
    soup.find("meta", {"name": "description"})["content"] = summary

    # <span id="titleAndReadingTime">
    #     <h1 id="blogPostTitle"></h1>
    #     <span id="readingTime">
    #         <date id="publicationDate">3rd of August 2022</date> |
    #         <p id="estimatedReadingTime">2-3 minutes</p>
    #     </span>
    # </span>
    # Set the reading time
    soup.find("p", {"id": "estimatedReadingTime"}).string = reading_time
    # Set the publication date
    soup.find("date", {"id": "publicationDate"}).string = datetime.fromtimestamp(date).strftime("%d %B %Y")

    # Set the article content
    soup.find("article", {"id": "blogPostContent"}).append(BeautifulSoup(html_content, 'html.parser'))
    
    # Need to add the code snippet copy functionality to the bottom of the page using the code snippet IDs (codeSnippetIds)
    # <script defer>
    #     (function () {
    #         // This should include all of the code snippets
    #         new ClipboardJS("#dataCopy, #flowCopy, #twoCopy");
    #     })();
    # </script>
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
        script_path = os.path.join('blog-source', 'snippets', script_file)
        if os.path.exists(script_path):
            with open(script_path, 'r') as f:
                script_content = f.read()
            script_tag = soup.new_tag('script', type='text/javascript')
            script_tag.string = script_content
            soup.find('head').append(script_tag)
            print(f"Added snippet script: {script_file}")
        else:
            print(f"Warning: Snippet script '{script_file}' not found.")

    # Strip the filename from the output path
    output_folder_path = os.path.abspath(os.path.dirname(output_path))
    # Create the directories if they don't exist
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path, exist_ok=True)
    
    # Create the html file using the soup with indentation and formatting
    with open(output_path, "w") as f:
        f.write(soup.prettify())
        created_files.append(output_path)
        
   
    
    # OK now add an entry to the /blog/articles.json file
    # Example articles.json entry:
    # {
    #     "headline": "Extract URL Query Paramters to Key:Value JSON in Power Automate (MS Flow)",
    #     "summary": "A Flow to extract Query Params form URLs",
    #     "link": "/blog/power-automate/url-query-params.html",
    #     "date": 1659520635,
    #     "tags": [
    #         "Power Automate",
    #         "MS Flow",
    #         "Power Platform"
    #     ]
    # }

    # Create the articles.json file if it doesn't exist
    if not os.path.exists("blog/articles.json"):
        with open("blog/articles.json", "w") as f:
            f.write('{"articles": []}')

    # Read the articles.json file
    with open("blog/articles.json", "r") as f:
        articles_json = json.load(f)

    # We need to check if the article already exists in the articles.json file
    # If it does, we need to update it
    # If it doesn't, we need to add it

    # Check if the article already exists
    article_exists = False
    for article in articles_json['articles']:
        if article["link"] == output_path[1:]:
            article_exists = True
            article["headline"] = headline
            article["summary"] = summary
            article["date"] = date
            article["tags"] = tags
            break
    # If the article doesn't exist, add it
    if not article_exists:
        articles_json['articles'].append({
            "headline": headline,
            "summary": summary,
            "link": output_path[1:],
            "date": date,
            "tags": tags
        })

    # Sort the articles by date
    articles_json['articles'] = sorted(articles_json['articles'], key=lambda x: x['date'], reverse=True)

    # Write the articles.json file
    with open("blog/articles.json", "w") as f:
        f.write(json.dumps(articles_json, indent=4))


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

def update_sitemap(sitemap_file="sitemap.xml", articles_json="blog/articles.json"):
    # Register the default namespace
    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Parse the existing sitemap with namespace
    tree = ET.parse(sitemap_file)
    root = tree.getroot()

    # Remove old blog entries
    root[:] = [elem for elem in root if elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc') is not None and '/blog/' not in elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text]

    # Load the articles.json file to get the lastmod date
    with open(articles_json, "r") as f:
        articles = json.load(f)['articles']

    # Add new blog entries
    for article in articles:
        url_elem = ET.SubElement(root, "url")
        ET.SubElement(url_elem, "loc").text = "https://www.joepitts.co.uk" + article["link"]
        date_str = datetime.fromtimestamp(article["date"]).strftime('%Y-%m-%d')
        ET.SubElement(url_elem, "lastmod").text = date_str
        ET.SubElement(url_elem, "changefreq").text = "monthly"
        ET.SubElement(url_elem, "priority").text = "0.8"

    # Pretty-print the XML
    prettify(root)

    # Write the updated sitemap back
    tree.write(sitemap_file, xml_declaration=True, encoding='utf-8')
    
if __name__ == "__main__":
    file_list = get_file_list()
    for file in file_list:
        yaml_config = get_yaml_header(file)
        html_content, reading_time = get_html_content_and_esitamated_reading_time(file)
        create_html_file(yaml_config, html_content, reading_time)
    update_sitemap()
    for file in created_files:
        print(os.path.abspath(file))
