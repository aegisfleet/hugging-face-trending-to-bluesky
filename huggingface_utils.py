import requests
from bs4 import BeautifulSoup, Comment

def get_trending_hf_models(url="https://huggingface.co/models", count=5):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    model_elements = soup.find_all("article", class_="overview-card-wrapper group/repo")[:count]

    models = []
    for model_element in model_elements:
        a_tag = model_element.find("a")
        href = a_tag["href"]
        title = a_tag.find("h4").text.strip()
        full_url = f"https://huggingface.co{href}"
        models.append((full_url, href, title))

    return models

def get_readme_text(href):
    readme_url = f"https://huggingface.co{href}/raw/main/README.md"
    tree_main_url = f"https://huggingface.co{href}"

    response = requests.get(readme_url)
    if response.status_code == 200:
        return response.text[:4000]

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
            return extracted_text[:4000]
        else:
            return ''
    return ''
