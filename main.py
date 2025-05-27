import re
import argparse
from googlesearch import search
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import time

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
MAX_EMAILS = 10  # Valeur par défaut, modifiable via l'argument --max
REQUEST_DELAY = 2  # Délai entre les requêtes pour éviter le rate limiting

excluded_domains = [
    # Moteurs de recherche
    'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com',
    
    # Réseaux sociaux
    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
    
    # Plateformes génériques
    'youtube.com', 'wikipedia.org', 'pages-jaunes.fr', 'pagesjaunes.fr',
    'yelp.com', 'tripadvisor.com', 'booking.com', 'booking.fr',
    
    # Microsoft et services associés
    'microsoft.com', 'help.bing.microsoft.com', 'go.microsoft.com', 
    'support.microsoft.com',
    
    # Annuaires d'entreprises généralistes (souvent protégés)
    'fr.kompass.com', 'pappers.fr', 'societe.com', 'sortlist.com',
    
    # Sites avec problèmes SSL/certificats
    'pple.fr',
    
    # Sites de signalement/contact généralistes
    'pointdecontact.net',
    
    # Autres annuaires généralistes
    'e-pro.fr', 'entreprises.lefigaro.fr', 'annuaire-mairie.fr',
    'hellowork.com', '118000.fr',
    
    # Sites de restaurants/guide touristique (peu pertinents pour emails B2B)
    'normandielovers.fr', 'petitfute.com', 'thefork.fr', 
    'guide.michelin.com', 'restaurantguru.com', 
    'linternaute.com', 'tripadvisor.fr', 'tripadvisor.ch'
]

def is_domain_excluded(url):
    """Vérifie si le domaine est dans la liste des exclus"""
    domain = urlparse(url).netloc.lower()
    for excluded in excluded_domains:
        if domain.endswith(excluded):
            return True
    return False

def extract_emails(text):
    """Extrait les emails d'un texte"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text, re.IGNORECASE)

def get_website_content(url):
    """Récupère le contenu d'une URL"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Erreur lors de l'accès à {url}: {e}")
        return None

def find_contact_page_url(main_url):
    """Tente de trouver une page de contact sur le site"""
    content = get_website_content(main_url)
    if not content:
        return None
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Recherche des liens typiques de pages de contact
    contact_keywords = ['contact', 'nous-contacter', 'about', 'about-us', 'contact-us', 'contactez-nous']
    
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        if any(keyword in href for keyword in contact_keywords):
            # Construire l'URL absolue
            return urljoin(main_url, link['href'])
    
    return None

def find_emails_in_website(url, check_contact_page=True):
    """Trouve les emails sur un site web"""
    content = get_website_content(url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    emails = extract_emails(text)
    
    # Vérifier aussi les liens mailto
    mailto_links = soup.select('a[href^="mailto:"]')
    for link in mailto_links:
        href = link.get('href', '')
        email = href.replace('mailto:', '').strip()
        if email and email not in emails:
            emails.append(email)
    
    # Si aucun email trouvé et qu'on peut vérifier la page contact
    if not emails and check_contact_page:
        contact_url = find_contact_page_url(url)
        if contact_url and contact_url != url:  # Éviter les boucles infinies
            print(f"Aucun email trouvé sur {url}, vérification de la page contact: {contact_url}")
            return find_emails_in_website(contact_url, check_contact_page=False)
    
    return emails

def search_and_scrape(query, max_emails):
    """Effectue la recherche Google et scrape les emails"""
    collected_emails = []
    processed_domains = set()
    
    print(f"Recherche d'emails pour la requête: '{query}'...")
    
    # Effectuer la recherche Google
    search_results = search(query, num_results=50, lang='fr')  # Augmenter si nécessaire
    
    for url in search_results:
        if len(collected_emails) >= max_emails:
            break
            
        if is_domain_excluded(url):
            continue
            
        domain = urlparse(url).netloc.lower()
        if domain in processed_domains:
            continue
            
        print(f"Traitement de: {url}")
        emails = find_emails_in_website(url)
        
        if emails:
            # Prendre le premier email trouvé pour ce domaine
            email = emails[0]
            collected_emails.append(email)
            processed_domains.add(domain)
            print(f"Trouvé: {email} (domaine: {domain})")
            
            # Écrire immédiatement dans le fichier
            with open('emails.txt', 'a') as f:
                f.write(f"{email}\n")
        else:
            print(f"Aucun email trouvé sur {url} (domaine: {domain})")
        
        time.sleep(REQUEST_DELAY)  # Respecter un délai entre les requêtes
    
    return collected_emails

def main():
    parser = argparse.ArgumentParser(description="Scraper d'emails à partir d'une requête Google")
    parser.add_argument("query", help="Requête de recherche pour trouver les sites web")
    parser.add_argument("--max", type=int, default=10, help="Nombre maximum d'emails à collecter (défaut: 10)")
    
    args = parser.parse_args()
    
    # Effacer le fichier de sortie s'il existe
    open('emails.txt', 'w').close()
    
    emails = search_and_scrape(args.query, args.max)
    
    print("\nRésultats finaux:")
    for email in emails:
        print(email)
    
    print(f"\n{len(emails)} emails trouvés et sauvegardés dans emails.txt")

if __name__ == "__main__":
    main()