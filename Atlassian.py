import requests
import sys
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ANSI escape codes for colored output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Fixed URL template
URL_TEMPLATE = 'https://{}.atlassian.net/servicedesk/customer/user/login'

# Set up logging
logging.basicConfig(filename='url_checker.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def extract_domain(full_url):
    """Extract the main domain name from a full URL, ignoring subdomains like 'www'."""
    parsed_url = urlparse(full_url)
    domain = parsed_url.netloc
    domain_parts = domain.split('.')
    if len(domain_parts) > 2:
        return domain_parts[-2]
    return domain_parts[0]

def fetch_status(url, domain):
    """Fetch the status code of the URL."""
    try:
        response = requests.get(url)
        return (domain, response.status_code)
    except requests.RequestException as e:
        return (domain, f'Error: {e}')

def check_urls(dictionary_file):
    # Read and filter out blank lines
    with open(dictionary_file, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    
    total_words = len(urls)
    count_200 = 0
    count_404 = 0
    count_403 = 0
    results = {}
    successful_urls = []

    # Extract domains and prepare URLs
    domains = [extract_domain(url) for url in urls]
    request_urls = [URL_TEMPLATE.format(domain) for domain in domains]

    # Use ThreadPoolExecutor to handle requests concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_status, url, domain): url for url, domain in zip(request_urls, domains)}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            domain = extract_domain(url)
            try:
                domain, status_code = future.result()
                if status_code == 200:
                    print(f'{GREEN}{domain}: 200 - Jira handler found{RESET}')
                    count_200 += 1
                    successful_urls.append(url)
                elif status_code == 404:
                    count_404 += 1
                elif status_code == 403:
                    count_403 += 1
                # Do not print 503 or other errors during processing
                results[url] = status_code
                logging.info(f'{url}: {status_code}')
            except Exception as e:
                results[url] = f'Error: {e}'
                logging.error(f'{url}: Error: {e}')

    # Print the statistics
    print(f'\n{BLUE}Result{RESET}')
    print(f'{BLUE}Total URLs: {total_words}{RESET}')
    print(f'{GREEN}Total 200 Responses: {count_200}{RESET}')
    print(f'{RED}Total 404 Responses: {count_404}{RESET}')
    print(f'{RED}Total 403 Responses: {count_403}{RESET}')

    # Show 200 status results after process ends
    if successful_urls:
        print(f'\n{GREEN}URLs with 200 Status:{RESET}')
        for url in successful_urls:
            print(f'{GREEN}{url}{RESET}')

    return results

def main():
    print(f'\n{BLUE}Welcome to Jira Signup Page Checker by Haqtify{RESET}\n')
    if len(sys.argv) != 2:
        print("Usage: python check_urls.py <dictionary_file>")
        sys.exit(1)

    dictionary_file = sys.argv[1]
    check_urls(dictionary_file)

if __name__ == "__main__":
    main()
