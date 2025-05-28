import re
import argparse
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import time
from duckduckgo_search import DDGS
import multiprocessing
import os
from datetime import datetime
import sys

# Configuration des couleurs ANSI
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Couleurs de base
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Couleurs vives
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Couleurs de fond
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def supports_color():
    """Vérifie si le terminal supporte les couleurs"""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def colorize(text, color_code):
    """Applique une couleur au texte si le terminal le supporte"""
    if supports_color():
        return f"{color_code}{text}{Colors.RESET}"
    return text

def print_colored(text, color_code=Colors.WHITE):
    """Affiche du texte coloré"""
    print(colorize(text, color_code))

def create_gradient_text(text, start_color, end_color):
    """Crée un effet dégradé sur le texte (simulation simple)"""
    if not supports_color():
        return text
    return f"{start_color}{text}{Colors.RESET}"

def print_box(text, color=Colors.CYAN, width=70):
    """Affiche un texte dans une boîte colorée"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    box_width = max(width, max_len + 4)
    
    # Ligne du haut
    print_colored("╔" + "═" * (box_width - 2) + "╗", color)
    
    # Contenu
    for line in lines:
        padding = box_width - len(line) - 3
        print_colored(f"║ {line}" + " " * padding + "║", color)
    
    # Ligne du bas
    print_colored("╚" + "═" * (box_width - 2) + "╝", color)

def print_progress_bar(current, total, width=50, color=Colors.GREEN):
    """Affiche une barre de progression colorée"""
    if total == 0:
        percentage = 0
    else:
        percentage = current / total
    
    filled = int(width * percentage)
    bar = "█" * filled + "░" * (width - filled)
    
    percentage_text = f"{percentage:.1%}"
    progress_text = f"[{colorize(bar, color)}] {current}/{total} ({percentage_text})"
    
    print(f"\r{progress_text}", end="", flush=True)

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
MAX_EMAILS = 10
REQUEST_DELAY = 1

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
    'linternaute.com', 'tripadvisor.fr', 'tripadvisor.ch', 'ovh.com', 'test.fr'
]

excluded_email_domains = [
    'ovh.com', 'test.fr', 'example.com', 'exemple.fr', 'sample.com',
    'noreply.com', 'no-reply.com', 'donotreply.com', 'nospam.com'
]

def print_header():
    """Affiche un en-tête stylé et coloré pour l'application"""
    os.system('cls' if os.name == 'nt' else 'clear')  # Nettoie l'écran
    
    print()
    header_text = """
███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
███████║╚██████╗██║  ██║██║  ██║██║     ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
    """
    
    print_colored(header_text, Colors.RED)
    
    subtitle = "COLLECTE INTELLIGENTE D'ADRESSES EMAILS DEPUIS LE WEB - V1.0 - By RDSV01"
    print_colored(f"{subtitle.center(0)}", Colors.BRIGHT_YELLOW)
    print()
    

def print_separator(char="═", length=80, color=Colors.CYAN):
    """Affiche un séparateur visuel coloré"""
    print_colored(char * length, color)

def print_status(message, status_type="info"):
    """Affiche un message de statut avec des couleurs appropriées"""
    icons = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️",
        "search": "🔍",
        "email": "📧",
        "save": "💾",
        "progress": "📊",
        "skip": "⏭️",
        "timeout": "⏰",
        "rocket": "🚀"
    }
    
    colors = {
        "success": Colors.BRIGHT_GREEN,
        "error": Colors.BRIGHT_RED,
        "warning": Colors.BRIGHT_YELLOW,
        "info": Colors.BRIGHT_BLUE,
        "search": Colors.BRIGHT_MAGENTA,
        "email": Colors.BRIGHT_CYAN,
        "save": Colors.GREEN,
        "progress": Colors.YELLOW,
        "skip": Colors.DIM,
        "timeout": Colors.YELLOW,
        "rocket": Colors.BRIGHT_MAGENTA
    }
    
    icon = icons.get(status_type, "•")
    color = colors.get(status_type, Colors.WHITE)
    
    print_colored(f"{icon} {message}", color)

def is_domain_excluded(url):
    """Vérifie si le domaine du site web est exclu"""
    domain = urlparse(url).netloc.lower()
    for excluded in excluded_domains:
        if domain.endswith(excluded):
            return True
    return False

def is_email_domain_excluded(email):
    """Vérifie si le domaine de l'email est exclu"""
    email_domain = email.split('@')[-1].lower()
    return email_domain in excluded_email_domains

def extract_emails(text):
    """Extrait les emails du texte avec filtrage des domaines exclus"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    raw_emails = re.findall(email_pattern, text, re.IGNORECASE)

    valid_extensions = ['.fr', '.com', '.net', '.org', '.io', '.co']

    cleaned_emails = set()
    for email in raw_emails:
        email = re.split(r'[^a-zA-Z0-9.@_-]', email)[0]

        if any(email.endswith(ext) for ext in valid_extensions):
            email = email.lower()
            if not is_email_domain_excluded(email):
                cleaned_emails.add(email)

    return list(cleaned_emails)

def get_website_content(url):
    """Récupère le contenu d'un site web"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print_status(f"Erreur lors de l'accès à {url}: {e}", "error")
        return None

def find_contact_page_url(main_url):
    """Trouve l'URL de la page de contact"""
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
    """Trouve les emails dans un site web"""
    content = get_website_content(url)
    if not content:
        return []

    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    emails = extract_emails(text)

    mailto_links = soup.select('a[href^="mailto:"]')
    for link in mailto_links:
        href = link.get('href', '')
        email = href.replace('mailto:', '').strip().lower()
        if email and not is_email_domain_excluded(email):
            emails.append(email)

    emails = extract_emails(' '.join(emails))

    if not emails and check_contact_page:
        contact_url = find_contact_page_url(url)
        if contact_url and contact_url != url:
            print_status(f"Vérification de la page contact: {contact_url}", "search")
            return find_emails_in_website(contact_url, check_contact_page=False)

    return list(set(emails))

def run_with_timeout(func, args=(), timeout=10):
    """Exécute une fonction dans un processus séparé avec un timeout"""
    with multiprocessing.Pool(processes=1) as pool:
        result = pool.apply_async(func, args)
        try:
            return result.get(timeout)
        except multiprocessing.TimeoutError:
            return None

def get_user_input():
    """Interface interactive colorée pour obtenir les paramètres de l'utilisateur"""
    print_header()
    
    # Demander la requête de recherche
    print_colored("🔍 CONFIGURATION DE LA RECHERCHE", Colors.BRIGHT_YELLOW + Colors.BOLD)
    print_separator("─", 50, Colors.YELLOW)
    
    while True:
        query = input(colorize("🔍 Entrez votre requête de recherche : ", Colors.BRIGHT_CYAN)).strip()
        if query:
            break
        print_status("La requête ne peut pas être vide. Veuillez réessayer.", "error")
    
    print()
    
    # Demander le nombre d'emails
    while True:
        try:
            max_emails_input = input(colorize(f"📧 Nombre maximum d'emails à collecter (défaut: {MAX_EMAILS}): ", Colors.BRIGHT_CYAN)).strip()
            if not max_emails_input:
                max_emails = MAX_EMAILS
                break
            max_emails = int(max_emails_input)
            if max_emails > 0:
                break
            else:
                print_status("Le nombre doit être supérieur à 0.", "error")
        except ValueError:
            print_status("Veuillez entrer un nombre valide.", "error")
    
    print()
    print_separator("═", 80, Colors.GREEN)
    
    # Affichage de la configuration
    config_text = f"""✅ CONFIGURATION VALIDÉE

🎯 Requête de recherche: '{query}'
📊 Maximum d'emails: {max_emails}"""
    
    print_box(config_text, Colors.BRIGHT_GREEN)
    
    input(colorize("\n🚀 Appuyez sur Entrée pour commencer la recherche...", Colors.BRIGHT_YELLOW))
    
    return query, max_emails

def search_and_scrape(query, max_emails):
    """Recherche et collecte les emails avec interface améliorée"""
    collected_emails = []
    processed_domains = set()
    used_email_domains = set()

    print_status("Démarrage de la recherche...", "rocket")
    print()

    try:
        with DDGS() as ddgs:
            search_results = [r for r in ddgs.text(query, region='fr-fr', max_results=1000)]
    except Exception as e:
        print_status(f"Erreur lors de la recherche: {e}", "error")
        return []

    print_status(f"{len(search_results)} sites trouvés à analyser", "info")
    print_separator("─", 60, Colors.BLUE)
    print()

    for i, result in enumerate(search_results, 1):
        if len(collected_emails) >= max_emails:
            break

        url = result['href']

        if is_domain_excluded(url):
            print_status(f"Site {i}: Domaine exclu - {urlparse(url).netloc}", "skip")
            continue

        domain = urlparse(url).netloc.lower()
        if domain in processed_domains:
            print_status(f"Site {i}: Domaine déjà traité - {domain}", "skip")
            continue

        print_status(f"Site {i}: Analyse de {url}", "search")
        emails = run_with_timeout(find_emails_in_website, args=(url,), timeout=10)

        if emails is None:
            print_status(f"Timeout pour {url}", "timeout")
            continue

        site_emails_added = 0
        for email in emails:
            email_domain = email.split('@')[-1]
            if email_domain in used_email_domains:
                continue

            collected_emails.append(email)
            used_email_domains.add(email_domain)
            processed_domains.add(domain)
            site_emails_added += 1
            print_status(f"Email trouvé: {email}", "success")
            
            # Sauvegarde immédiate
            with open('emails.txt', 'a', encoding='utf-8') as f:
                f.write(f"{email}\n")
            
            break

        if site_emails_added == 0:
            print_status("Aucun email affiché sur le site", "warning")
        
        # Barre de progression
        print_progress_bar(len(collected_emails), max_emails)
        print()  # Nouvelle ligne après la barre de progression
        print()

        if len(collected_emails) < max_emails:
            time.sleep(REQUEST_DELAY)

    return collected_emails

def save_results(emails, query):
    """Sauvegarde les résultats avec horodatage"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"emails_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Emails collectés le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        f.write(f"# Requête: {query}\n")
        f.write(f"# Nombre d'emails: {len(emails)}\n")
        for email in emails:
            f.write(f"{email}\n")
    
    return filename

def display_results(emails, query):
    """Affiche les résultats finaux avec style"""
    print()
    print_separator("═", 80, Colors.BRIGHT_MAGENTA)
    
    result_header = "🎉 RÉSULTATS DE LA COLLECTE 🎉"
    print_colored(f"{result_header.center(80)}", Colors.BRIGHT_MAGENTA + Colors.BOLD)
    
    print_separator("═", 80, Colors.BRIGHT_MAGENTA)
    print()
    
    if emails:
        summary_text = f"""📊 RÉSUMÉ DE LA COLLECTE

📧 Nombre d'emails collectés: {len(emails)}
🎯 Requête utilisée: '{query}'
⏰ Collecte terminée le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"""
        
        print_box(summary_text, Colors.BRIGHT_GREEN)
        print()
        
        print_colored("📋 LISTE DES EMAILS COLLECTÉS:", Colors.BRIGHT_CYAN + Colors.BOLD)
        print_separator("─", 50, Colors.CYAN)
        
        for i, email in enumerate(emails, 1):
            print_colored(f"   {i:2d}. {email}", Colors.WHITE)
        
        print()
        
        # Sauvegarde avec horodatage
        filename = save_results(emails, query)
        
        save_text = f"""💾 SAUVEGARDE RÉUSSIE

📁 Fichier principal: {filename}
📁 Sauvegarde simple: emails.txt"""
        
        print_box(save_text, Colors.BRIGHT_BLUE)
        
    else:
        print_box("❌ AUCUN EMAIL TROUVÉ", Colors.BRIGHT_RED)
        
        suggestions_text = """💡 SUGGESTIONS POUR AMÉLIORER VOS RÉSULTATS:

• Essayez une requête plus spécifique
• Utilisez des mots-clés liés à votre secteur d'activité
• Vérifiez que les sites ciblés ne sont pas dans la liste d'exclusion
• Augmentez le nombre maximum d'emails à collecter
• Essayez des variantes de votre requête de recherche"""
        
        print_box(suggestions_text, Colors.BRIGHT_YELLOW)
    
    print()
    print_separator("═", 80, Colors.BRIGHT_MAGENTA)
    print_status("Merci d'avoir utilisé ScrapForge ! 🚀", "success")

def main():
    """Fonction principale avec interface interactive ou arguments"""
    parser = argparse.ArgumentParser(description="Scraper d'emails à partir d'une requête de recherche")
    parser.add_argument("--query", help="Requête de recherche pour trouver les sites web")
    parser.add_argument("--max", type=int, help="Nombre maximum d'emails à collecter")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")

    args = parser.parse_args()

    # Mode interactif par défaut si aucun argument n'est fourni
    if not any([args.query, args.interactive]) or args.interactive:
        query, max_emails = get_user_input()
    else:
        query = args.query
        max_emails = args.max if args.max else MAX_EMAILS
        print_header()
        
        config_text = f"""🔍 MODE LIGNE DE COMMANDE

🎯 Requête: {query}
📧 Maximum d'emails: {max_emails}"""
        
        print_box(config_text, Colors.BRIGHT_BLUE)

    # Initialiser le fichier de sauvegarde
    open('emails.txt', 'w', encoding='utf-8').close()

    # Lancer la recherche
    emails = search_and_scrape(query, max_emails)

    # Afficher les résultats
    display_results(emails, query)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()