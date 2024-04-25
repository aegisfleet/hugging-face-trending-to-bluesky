import re
import requests
from bs4 import BeautifulSoup, Comment

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
        href = a_tag["href"]
        full_url = f"https://huggingface.co{href}"
        if full_url not in previous_models:
            name = href[1:]
            models.append((full_url, name))

    artifact_utils.save_results(models)
    return models

def remove_html_tags_and_lists(text):
    clean_text = re.sub('<.*?>', '', text)
    clean_text = re.sub('^[ \t]*[-*+][ \t].*$', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub('\n\s*\n', '\n', clean_text)
    return clean_text

def get_readme_text(repo_name):
    readme_url = f"https://huggingface.co/{repo_name}/raw/main/README.md"
    tree_main_url = f"https://huggingface.co/{repo_name}"

    response = requests.get(readme_url)
    if response.status_code == 200:
        return remove_html_tags_and_lists(response.text)[:2000]

    response = requests.get(tree_main_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        text_segments = []

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if 'HTML_TAG_START' in comment:
                sibling = comment.next_element
                while sibling and not (isinstance(sibling, Comment) and 'HTML_TAG_END' in sibling):
                    if sibling.name is None:
                        text_segments.append(sibling.strip())
                    sibling = sibling.next_element

        extracted_text = ' '.join(text_segments).strip()
        if extracted_text:
            return remove_html_tags_and_lists(extracted_text)[:2000]
        else:
            return ''
    return ''
