import re
import requests
from bs4 import BeautifulSoup, Comment, Tag, NavigableString

import artifact_utils

def get_trending_hf_models(url="https://huggingface.co/models", count=5):
    previous_models = artifact_utils.load_previous_results()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    model_elements = soup.find_all("article", class_="overview-card-wrapper group/repo")

    models = []
    for model_element in model_elements[:10]:
        if len(models) >= count:
            break
        a_tag = model_element.find("a")
        if a_tag and isinstance(a_tag, Tag):
            href = a_tag.get("href")
            if href:
                full_url = f"https://huggingface.co{href}"
                if full_url not in previous_models:
                    name = href[1:]
                    models.append((full_url, name))

    artifact_utils.save_results(models)
    return models

def remove_html_tags_and_lists(text):
    clean_text = re.sub('<.*?>', '', text)
    clean_text = re.sub('^[ \t]*[-*+][ \t].*$', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
    return clean_text

def get_readme_text(repo_name):
    """
    リポジトリのREADMEテキストを取得する。
    まず raw README を試し、失敗した場合は HTML から抽出を試みる。
    """
    text = _fetch_readme_from_raw(repo_name)
    if text:
        return text

    return _fetch_readme_from_html(repo_name)

def _fetch_readme_from_raw(repo_name):
    readme_url = f"https://huggingface.co/{repo_name}/raw/main/README.md"
    try:
        response = requests.get(readme_url, timeout=10)
        if response.status_code == 200:
            return remove_html_tags_and_lists(response.text)[:2000]
    except requests.RequestException:
        pass
    return None

def _fetch_readme_from_html(repo_name):
    url = f"https://huggingface.co/{repo_name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            extracted_text = _extract_text_from_comments(soup)
            if extracted_text:
                return remove_html_tags_and_lists(extracted_text)[:2000]
    except requests.RequestException:
        pass
    return ''

def _extract_text_from_comments(soup):
    text_segments = []
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if 'HTML_TAG_START' in comment:
            text_segments.extend(_parse_comment_block(comment))
    return ' '.join(text_segments).strip()

def _parse_comment_block(start_comment):
    segments = []
    sibling = start_comment.next_element
    while sibling:
        if isinstance(sibling, Comment) and 'HTML_TAG_END' in sibling:
            break
        if isinstance(sibling, NavigableString):
            text = sibling.strip()
            if text:
                segments.append(text)
        sibling = sibling.next_element
    return segments
