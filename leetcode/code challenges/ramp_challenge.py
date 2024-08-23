import requests
from bs4 import BeautifulSoup
import re

# Function to fetch and parse the DOM from a URL
def fetch_dom_from_url(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        print(f"Failed to retrieve the URL: {url}")
        return None

# Function to extract valid characters
def extract_valid_characters(soup):
    # Compile regex patterns to match the wildcard attributes
    code_pattern = re.compile(r'^23.*')
    div_pattern = re.compile(r'.*93$')
    span_pattern = re.compile(r'^.*21.*$')

    # Find all matching code tags
    valid_characters = []

    for code in soup.find_all('code', attrs={'data-class': code_pattern}):
        div = code.find('div', attrs={'data-tag': div_pattern})
        if div:
            span = div.find('span', attrs={'data-id': span_pattern})
            if span:
                char_tag = span.find('i', class_='char')
                if char_tag:
                    valid_character = char_tag.get('value')
                    if valid_character:
                        valid_characters.append(valid_character)

    return valid_characters

# Fetch the DOM from the URL
soup = fetch_dom_from_url('https://tns4lpgmziiypnxxzel5ss5nyu0nftol.lambda-url.us-east-1.on.aws/challenge')

if soup:
    # Extract valid characters
    valid_characters = extract_valid_characters(soup)
    print(valid_characters)
    s = ''.join(valid_characters)
    print(s)
