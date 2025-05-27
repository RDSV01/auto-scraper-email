import re
import argparse
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import time
from duckduckgo_search import DDGS
import multiprocessing

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
MAX_EMAILS = 10
REQUEST_DELAY = 2

excluded_domains = [
    'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com',
    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
    'youtube.com', 'wikipedia.org', 'pages-jaunes.fr', 'pagesjaunes.fr',
    'yelp.com', 'tripadvisor.com', 'booking.com', 'booking.fr',
    'microsoft.com', 'help.bing.microsoft.com', 'go.microsoft.com',
    'support.microsoft.com',
    'fr.kompass.com', 'pappers.fr', 'societe.com', 'sortlist.com',
    'pple.fr',
    'pointdecontact.net',
    'e-pro.fr', 'entreprises.lefigaro.fr', 'annuaire-mairie.fr',
    'hellowork.com', '118000.fr',
    'normandielovers.fr', 'petitfute.com', 'thefork.fr',
    'guide.michelin.com', 'restaurantguru.com',
    'linternaute.com', 'tripadvisor.fr', 'tripadvisor.ch'
]

def is_domain_excluded(url):
    domain = urlparse(url).netloc.lower()
    for excluded in excluded_domains:
        if domain.endswith(excluded):
            return True
    return False

def extract_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    raw_emails = re.findall(email_pattern, text, re.IGNORECASE)

    # Extensions valides (modifiable)
    valid_extensions = ['.fr', '.com', '.net', '.org', '.io', '.co']

    cleaned_emails = set()
    for email in raw_emails:
        # Enlever les résidus comme contact@domaine.frJob ou .frChat
        email = re.split(r'[^a-zA-Z0-9.@_-]', email)[0]

        # Vérifie l'extension valide
        if any(email.endswith(ext) for ext in valid_extensions):
            cleaned_emails.add(email.lower())  # Minuscule pour éviter les doublons

    return list(cleaned_emails)

def get_website_content(url):
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Erreur lors de l'accès à {url}: {e}")
        return None

def find_contact_page_url(main_url):
    content = get_website_content(main_url)
    if not content:
        return None

    soup = BeautifulSoup(content, 'html.parser')
    contact_keywords = ['contact', 'nous-contacter', 'about', 'about-us', 'contact-us', 'contactez-nous']

    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        if any(keyword in href for keyword in contact_keywords):
            return urljoin(main_url, link['href'])

    return None

def find_emails_in_website(url, check_contact_page=True):
    content = get_website_content(url)
    if not content:
        return []

    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    emails = extract_emails(text)

    # Ajout des mailto:
    mailto_links = soup.select('a[href^="mailto:"]')
    for link in mailto_links:
        href = link.get('href', '')
        email = href.replace('mailto:', '').strip().lower()
        if email:
            emails.append(email)

    # Nettoyage final
    emails = extract_emails(' '.join(emails))

    if not emails and check_contact_page:
        contact_url = find_contact_page_url(url)
        if contact_url and contact_url != url:
            print(f"Aucun email trouvé sur {url}, vérification de la page contact: {contact_url}")
            return find_emails_in_website(contact_url, check_contact_page=False)

    return list(set(emails))  # Supprimer les doublons

def run_with_timeout(func, args=(), timeout=10):
    """Exécute une fonction dans un processus séparé avec un timeout"""
    with multiprocessing.Pool(processes=1) as pool:
        result = pool.apply_async(func, args)
        try:
            return result.get(timeout)
        except multiprocessing.TimeoutError:
            return None

def search_and_scrape(query, max_emails):
    collected_emails = set()
    processed_domains = set()

    print(f"Recherche d'emails pour la requête: '{query}'...")

    with DDGS() as ddgs:
        search_results = [r for r in ddgs.text(query, region='fr-fr', max_results=50)]

    for result in search_results:
        if len(collected_emails) >= max_emails:
            break

        url = result['href']

        if is_domain_excluded(url):
            continue

        domain = urlparse(url).netloc.lower()
        if domain in processed_domains:
            continue

        print(f"Traitement de: {url}")
        emails = run_with_timeout(find_emails_in_website, args=(url,), timeout=10)

        if emails is None:
            print(f"Timeout ou échec du traitement de {url}")
            continue

        for email in emails:
            if len(collected_emails) >= max_emails:
                break
            if email not in collected_emails:
                collected_emails.add(email)
                print(f"Trouvé: {email} (domaine: {domain})")
                with open('emails.txt', 'a') as f:
                    f.write(f"{email}\n")

        processed_domains.add(domain)
        time.sleep(REQUEST_DELAY)

    return list(collected_emails)

def main():
    parser = argparse.ArgumentParser(description="Scraper d'emails à partir d'une requête de recherche")
    parser.add_argument("query", help="Requête de recherche pour trouver les sites web")
    parser.add_argument("--max", type=int, default=10, help="Nombre maximum d'emails à collecter (défaut: 10)")

    args = parser.parse_args()

    open('emails.txt', 'w').close()

    emails = search_and_scrape(args.query, args.max)

    print("\nRésultats finaux:")
    for email in emails:
        print(email)

    print(f"\n{len(emails)} emails trouvés et sauvegardés dans emails.txt")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
