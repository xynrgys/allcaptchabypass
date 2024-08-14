#import whisper
import warnings
#import requests
from time import sleep
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as bs
from selenium.common.exceptions import TimeoutException as SE_TimeoutExepction
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException
)
from time import sleep
from datetime import datetime,timezone

warnings.filterwarnings("ignore")
# model = whisper.load_model("base")

# def transcribe(url):
#     with open('.temp', 'wb') as f:
#         f.write(requests.get(url).content)
#     result = model.transcribe('.temp')
#     return result["text"].strip()

# def click_checkbox(driver):
#     driver.switch_to.default_content()
#     driver.switch_to.frame(driver.find_element(By.XPATH, ".//iframe[@title='reCAPTCHA']"))
#     driver.find_element(By.ID, "recaptcha-anchor-label").click()
#     driver.switch_to.default_content()

# def request_audio_version(driver):
#     driver.switch_to.default_content()
#     driver.switch_to.frame(driver.find_element(By.XPATH, ".//iframe[@title='recaptcha challenge expires in two minutes']"))
#     driver.find_element(By.ID, "recaptcha-audio-button").click()

# def solve_audio_captcha(driver):
#     text = transcribe(driver.find_element(By.ID, "audio-source").get_attribute('src'))
#     driver.find_element(By.ID, "audio-response").send_keys(text)
#     driver.find_element(By.ID, "recaptcha-verify-button").click()

# def captcha_solve(driver):
#     click_checkbox(driver)
#     sleep(1)
#     request_audio_version(driver)
#     sleep(1)
#     solve_audio_captcha(driver)
#     sleep(10)

# def is_captcha_present(driver):
#     captcha_identifiers = [
#         "recaptcha",
#         "g-recaptcha",
#         "captcha",
#         "cf-challenge-running"
#     ]
#     page_source = driver.page_source.lower()
#     return any(identifier in page_source for identifier in captcha_identifiers)

SEARCH_PREFIX = '/search'
SEARCH_PREFIX_LEN = len(SEARCH_PREFIX)

DOMAIN = 'https://www.google.com'
FEATURE_SNIPPET_PATH = '/html/body/div[7]/div/div[9]/div[1]/div/div[2]/div[2]/div/div/div[1]/div/div[1]/div/div[1]'
RELATED_SEARCH_BOX = '/html/body/div[7]/div[1]/div[10]/div[1]/div/div[4]/div/div[1]/div/div'

def get_chrome_options_args(is_headless):
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--lang=en-SG")
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})

    if is_headless:
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--disable-setuid-sandbox")
        # chrome_options.add_argument("--no-first-run")
        # chrome_options.add_argument("--no-zygote")
        # chrome_options.add_argument("--single-process")
        # chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    return chrome_options

def extract_questions(soup):
    related_questions = []
    for accordian_expanded in soup.findAll('g-accordion-expander'):

        question = accordian_expanded.find('div',{'role': 'button'}).text.strip()
        if accordian_expanded.find('cite') is None:
            continue
        display_link = accordian_expanded.find('cite').text.strip()
        link = accordian_expanded.find('a') # we assume the link should rank first
        if link is None:
            continue
        title = link.text.strip()
        link = link.get('href')
        snippet = accordian_expanded.find('div', {'data-attrid':"wa:/description"})
        if snippet:
            snippet = snippet.get_text(separator="\n")
        alt_search_link = None
        alt_search_query = None

        question = {
            'title': title,
            'displayed_link': display_link,
            'link': link,
            'snippet': snippet
        }
        for a in accordian_expanded.findAll('a'):
            if SEARCH_PREFIX == a.get('href')[:SEARCH_PREFIX_LEN]:
                alt_search_link = a.get('href')
                alt_search_query = a.text.strip()

                question['question'] = alt_search_query
                question['question_link'] = alt_search_link

        related_questions.append(question)
    return related_questions

def extract_knowledge_graph(elem, dom):
    outputs = {}
    knowledge_graph = {}
    kp_wholepage_elem = elem.find('div', {'class': 'kp-wholepage'})
    if kp_wholepage_elem:
        # ... (keep existing code)
        expandable_contents = []
        if kp_wholepage_elem.find('g-expandable-content'):
            for content in kp_wholepage_elem.findAll('g-expandable-content'):
                expandable_contents.append(content.get_text(separator="\n").strip())
        if len(expandable_contents) > 0:
            if 'knowledge_graph' not in outputs:
                outputs['knowledge_graph'] = {}
            outputs['knowledge_graph']['expanded_content'] = expandable_contents
        knowledge_graph = elem

        kg_title_elem = dom.select_one('.kp-wholepage > div:nth-child(2) > div:nth-child(2) > div > div > div > div:nth-child(2) > h2 > span')
        if kg_title_elem:
            kg_title = kg_title_elem.text.strip()
            outputs['title'] = kg_title

        # ... (keep existing code)
        # obtain accordion
        accordions = []
        accordions_ctx = []
        for g_accordion in kp_wholepage_elem.findAll('g-accordion-expander'):
            divs = g_accordion.findChildren('div', recursive=False)
            if len(divs) > 1:
                title = divs[0].text.strip()
                context = divs[1]
                data = {'title': title}
                if context.find('div', {'data-attrid':"wa:/description"}):
                    context_snippet = context.find('div', {'data-attrid':"wa:/description"}).get_text(separator="\n").strip()
                    data['snippet'] = context_snippet
                if context.find('div', {'data-tts':"answers"}):
                    context_title = context.find('div', {'data-tts':"answers"}).get_text(separator="\n").strip()
                    data['answer'] = context_title
                if context.find('cite'):
                    displayed_link = context.find('cite').text.strip()
                    data['displayed_link'] = displayed_link
                if context.find('a'):
                    data['link'] = context.find('a').get('href')
                if len(data) > 0:
                    accordions_ctx.append(data)
            accordions.append(g_accordion)

        if len(accordions) > 0:
            # set value
            if len(accordions_ctx) > 0:
                outputs['accordions'] = accordions_ctx

            # remove elements
            for g_accordion in kp_wholepage_elem.findAll('g-accordion-expander'):
                g_accordion.decompose()

        # build attributes
        data_attributes = kp_wholepage_elem.findAll('div', {'data-attrid': True})
        for attribute in data_attributes:
            attrid = attribute.get('data-attrid')
            if attrid is not None and attrid in ['description', 'subtitle']:
                continue
            spans = attribute.findAll('span')
            if len(spans) > 1:
                name, value = spans[0], spans[1]
                if value.find('span'):
                    outputs[name.text.strip()] = value.text.strip()
                elif len(value.findAll('a')) > 0:
                    name = name.text.strip()
                    outputs[name] = []
                    for a in value.findAll('a'):
                        link  = a.get('href')
                        outputs[name].append({
                            'value': a.text.strip(),
                            'link': DOMAIN+link if '/' == link[0] else link
                        })
                else:
                    outputs[name.text.strip()] = value.text.strip()

        kp_dom = bs(str(kp_wholepage_elem), 'html.parser')
        kg_summary = kp_dom.select_one('#kp-wp-tab-overview > div:nth-child(1) > div > div > div > div > div > div > div > div > span:nth-child(1)')
        if kg_summary:
            kg_summary_text = kg_summary.text.strip()
            outputs['description'] = kg_summary_text

        source_elem = kp_dom.select_one('#kp-wp-tab-overview > div:nth-child(1) > div > div > div > div > div > div > div > div > span:nth-child(2) > a')
        if source_elem:
            source_link = source_elem.get('href')
            data_source = source_elem.text.strip()
            outputs['source'] = {
                "name": data_source,
                'link': source_link
            }

        # ... (keep the rest of the function)
        people_also_search_for = []
        for t in knowledge_graph.findAll('div', {'data-reltype': 'sideways'}):
            data = {}
            if t.find('img'):
                data['image'] = t.find('img').get('src')
            if t.find('a'):
                data['link'] = t.find('a').get('href')
            data['name'] = t.text
            if len(data) > 1:
                people_also_search_for.append(data)

        if len(people_also_search_for) > 0:
            outputs['people_also_search_for'] = people_also_search_for

    return outputs

def extract_display_stats(full_dom, soup):
    data = {}
    time_stats = soup.select_one('#result-stats > nobr')
    if time_stats:
        time_to_finish = time_stats.text.strip()
        full_stats = soup.select_one('#result-stats')
        if full_stats:
            full_stats_text = full_stats.text.strip()
            total_result_text = full_stats_text.replace(time_to_finish, '')
            total_results = total_result_text.split(' ')[1]
            if 'result' in total_results:
                total_results = total_result_text.split(' ')[0]

            if ',' in total_results:
                total_results = total_results.replace(',','')
            total = int(total_results)
            time_to_finish_text = time_to_finish.replace('(','').split(' ')[0]
            time_taken_displayed = float(time_to_finish_text)
            data['total_results'] = total
            data['time_taken_displayed'] = time_taken_displayed

    # ... (keep the rest of the function)
    has_spelling_fix = soup.find('span', {'class': 'spell_orig'})
    if has_spelling_fix and soup.find('a', {'class': 'spell_orig'}):
        spelling_fix = has_spelling_fix.text.strip()
        query_displayed = soup.find('a', {'class': 'spell_orig'}).text.strip()
        parent_div = has_spelling_fix.parent
        data['showing_results_for'] = spelling_fix
        data['spelling_fix'] = spelling_fix
        data['query_displayed'] = query_displayed

    return data

def check_feature_snippet(raw_html):
    if 'websearch?p%3Dfeatured_snippets%2' in raw_html:
        return True
    return False

def extract_feature_snippet(soup):
    feature_snippet_block = soup.find('div', {'data-hveid': True, 'data-ved': True, 'lang': True})
    if feature_snippet_block:
        texts = [block.get_text(separator="\n") for block in feature_snippet_block.find_all('div', {'data-md': True})]
        result_block = feature_snippet_block.find('div', {'class': 'g'})

        if result_block:
            title_element = result_block.select_one('div > div:nth-child(1) > a > h3')
            title = title_element.text if title_element else ''
            
            link_element = result_block.find('a')
            link = link_element.get('href') if link_element else ''
            
            displayed_link_element = result_block.find('cite')
            displayed_link = displayed_link_element.text if displayed_link_element else ''

            return {
                'texts': texts,
                'link': link,
                'displayed_link': displayed_link,
                'title': title
            }, feature_snippet_block
    
    return {}, None

def extract(query_target, url, location=None):
    # ... (keep existing code)
    has_question = False

    driver = Driver(uc=True)

    params = {
        "latitude": 1.3627936,
        "longitude": 103.8737315,
        "accuracy": 100
    }
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)

    wait = WebDriverWait(driver, 30)
    driver.get(url)
    created_t = datetime.now(timezone.utc)

    # Check for CAPTCHA
    if is_captcha_present(driver):
        print("CAPTCHA detected. Attempting to solve...")
        try:
            captcha_solve(driver)
            print("CAPTCHA solved successfully.")
        except Exception as e:
            print(f"Failed to solve CAPTCHA: {str(e)}")
            driver.quit()
            return None

    # Rest of your existing extraction code...

    body = driver.find_element("xpath", "//body").text
    kg_expander = '/html/body/div[7]/div/div[9]/div[1]/div/div[2]/div[2]/div/div/div[1]/div/div/div[2]/div[4]/div/div/div/div[1]/div/div/div/div/div/div[2]/g-expandable-container/div/div[1]/div[1]/g-expandable-content[1]/span/div/g-text-expander/a'
    try:
        if driver.find_element("xpath", kg_expander):
            button = driver.find_element("xpath", kg_expander)
            text = button.get_attribute('jsaction')
            if text:
                button.click()
    except ( NoSuchElementException, ElementClickInterceptedException,
        StaleElementReferenceException, ElementNotInteractableException ):
        pass

    full_dom = bs(driver.page_source, 'html.parser')
    
    # Replace XPath queries with BeautifulSoup selectors
    question_elements = full_dom.select('div.g-accordion-expander > div:first-child')
    for idx, e in enumerate(question_elements):
        try:
            question_path = f'/html/body/div[7]/div/div[9]/div[1]/div/div[2]/div[2]/div/div/div[2]/div/div/div/div[1]/div/div[{idx+1}]/g-accordion-expander/div[1]'
            button = driver.find_element("xpath", question_path)
            text = button.get_attribute('jsaction')
            if text:
                has_question = True
                button.click()
        except (ElementClickInterceptedException, NoSuchElementException,
                StaleElementReferenceException, ElementNotInteractableException):
            continue

    # Replace the kg_accordion_expand XPath query
    kg_accordion_elements = full_dom.select('div.kp-wholepage div.g-accordion-expander > div:first-child')
    for idx, e in enumerate(kg_accordion_elements):
        try:
            kg_accordion = f'/html/body/div[7]/div/div[9]/div[2]/div[1]/div/div[2]/div[5]/div/div/div/div[1]/div/div/div/div/div[8]/div/div[{idx+1}]/div/div/div/g-accordion-expander/div[1]'
            button = driver.find_element("xpath", kg_accordion)
            text = button.get_attribute('jsaction')
            if text:
                has_question = True
                button.click()
        except (ElementClickInterceptedException,
                StaleElementReferenceException,
                ElementNotInteractableException):
            continue

    # ... (keep the rest of the function as is)
    raw_html = driver.page_source
    soup = bs(raw_html, 'html.parser')
    outputs = {}
    if check_feature_snippet(raw_html):
        featured_snippet, featured_snippet_block = extract_feature_snippet(soup)
        if len(featured_snippet) > 0:
            featured_snippet_block.decompose()
            outputs['featured_snippet'] = featured_snippet

    questions = extract_questions(soup)
    if len(questions) > 0:
        outputs['question'] = questions

    related_searches = []
    related_box = soup.find('div', {'data-abe': True})
    if related_box:
        for a in related_box.find_all('a'):
            if SEARCH_PREFIX == a.get('href')[:SEARCH_PREFIX_LEN]:
                query = a.text.strip()
                link = DOMAIN + a.get('href')
                related_searches.append({
                    'query': query,
                    'link': link
                })
        if len(related_searches) > 0:
            outputs['related_searches'] = related_searches

    search_information = extract_display_stats(soup, soup)  # Note: full_dom is now just soup
    if len(search_information) > 0:
        outputs['search_information'] = search_information
        outputs['search_information']['query'] = query_target
    else:
        outputs['search_information'] = {
            'query': query_target
        }

    results = list(soup.find_all('div', {'class': 'g'}))
    organic_results = []
    for r in results:
        if r.find('div', {'class': 'kp-wholepage'}):
            knowledge_graph = extract_knowledge_graph(soup, soup)  # Note: full_dom is now just soup
            if len(knowledge_graph) > 0:
                outputs['knowledge_graph'] = knowledge_graph
        else:
            title_elem = r.select_one('div > div:nth-child(1) > a > h3')
            snippet_elem = r.select_one('div > div:nth-child(2) > div > div')
            if title_elem and snippet_elem:
                title = title_elem.text
                link = r.find('a').get('href')
                snippet = snippet_elem.text
                if title and r.find('cite'):
                    displayed_link = r.find('cite').text
                    title = title.replace(displayed_link, '')
                    organic_results.append({
                        'title': title,
                        'snippet': snippet,
                        'displayed_link': displayed_link,
                        'link': link
                    })
    if len(organic_results) > 0:
        outputs['organic_results'] = organic_results

    processed_t = datetime.now(timezone.utc)

    outputs['search_metadata'] = {
        "status": "Success",
        "total_time_taken": (processed_t - created_t).total_seconds(),
        "created_at": created_t.strftime('%Y-%m-%dT%H:%M:%S +UTC'),
        "processed_at": processed_t.strftime('%Y-%m-%dT%H:%M:%S +UTC'),
        "google_url": url,
    }
    if location is not None:
        outputs['search_metadata']['location'] = location

    driver.quit()

    return outputs
