import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import re
from datetime import datetime
import csv
from pathlib import Path

class WebScraperForLLM:
    def __init__(self, base_url: str, delay: float = 1.0):
        """
        Initialize the web scraper for LLM training data collection
        
        Args:
            base_url: The base URL of the website to scrape
            delay: Delay between requests to be respectful to the server
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Storage for scraped data
        self.scraped_data = []
        
    def scrape_page(self, url: str) -> Optional[Dict]:
        """
        Scrape a single page and extract relevant data for LLM training
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing extracted data or None if failed
        """
        try:
            self.logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract various types of content
            data = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'headings': self._extract_headings(soup),
                'main_content': self._extract_main_content(soup),
                'links': self._extract_links(soup, url),
                'faq_content': self._extract_faq_content(soup),
                'product_info': self._extract_product_info(soup),
                'contact_info': self._extract_contact_info(soup),
                'navigation_text': self._extract_navigation_text(soup),
                'clean_text': self._extract_clean_text(soup)
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '').strip() if meta_desc else ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings (h1-h6)"""
        headings = {}
        for i in range(1, 7):
            heading_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [h.get_text().strip() for h in heading_tags]
        return headings
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from common content containers"""
        # Try to find main content areas
        content_selectors = [
            'main', 'article', '[role="main"]', '.content', 
            '.main-content', '#content', '.post-content',
            '.entry-content', '.article-body'
        ]
        
        content_text = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Only include substantial content
                    content_text.append(text)
        
        return ' '.join(content_text)
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links with their anchor text"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            if text and href:
                full_url = urljoin(base_url, href)
                links.append({'url': full_url, 'anchor_text': text})
        return links[:50]  # Limit to first 50 links to avoid too much data
    
    def _extract_faq_content(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract FAQ content (questions and answers)"""
        faqs = []
        
        # Look for common FAQ patterns
        faq_selectors = [
            '.faq', '.faqs', '.qa', '.question-answer',
            '[class*="faq"]', '[class*="question"]'
        ]
        
        for selector in faq_selectors:
            faq_sections = soup.select(selector)
            for section in faq_sections:
                # Look for question-answer pairs
                questions = section.find_all(['h3', 'h4', 'h5', '.question', '[class*="question"]'])
                for q in questions:
                    question_text = q.get_text().strip()
                    if question_text:
                        # Try to find the answer (usually the next sibling or parent's next element)
                        answer_element = q.find_next_sibling(['p', 'div', '.answer'])
                        if not answer_element:
                            parent = q.parent
                            if parent:
                                answer_element = parent.find_next_sibling(['p', 'div'])
                        
                        answer_text = answer_element.get_text().strip() if answer_element else ""
                        
                        if question_text and answer_text:
                            faqs.append({
                                'question': question_text,
                                'answer': answer_text
                            })
        
        return faqs
    
    def _extract_product_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product/service information"""
        product_info = {}
        
        # Look for product descriptions, features, prices
        selectors = {
            'description': ['.product-description', '.description', '.summary'],
            'features': ['.features', '.product-features', '.benefits'],
            'price': ['.price', '.cost', '.pricing'],
            'specifications': ['.specs', '.specifications', '.details']
        }
        
        for key, selector_list in selectors.items():
            for selector in selector_list:
                elements = soup.select(selector)
                if elements:
                    text = ' '.join([el.get_text().strip() for el in elements])
                    if text:
                        product_info[key] = text
                        break
        
        return product_info
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information"""
        contact_info = {}
        
        # Look for contact information
        contact_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        }
        
        page_text = soup.get_text()
        for info_type, pattern in contact_patterns.items():
            matches = re.findall(pattern, page_text)
            if matches:
                contact_info[info_type] = matches[:3]  # Limit to first 3 matches
        
        return contact_info
    
    def _extract_navigation_text(self, soup: BeautifulSoup) -> List[str]:
        """Extract navigation menu text"""
        nav_text = []
        nav_selectors = ['nav', '.navigation', '.menu', '.navbar', 'header ul']
        
        for selector in nav_selectors:
            nav_elements = soup.select(selector)
            for nav in nav_elements:
                links = nav.find_all('a')
                nav_text.extend([link.get_text().strip() for link in links if link.get_text().strip()])
        
        return list(set(nav_text))  # Remove duplicates
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content for general LLM training"""
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Get clean text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped data dictionaries
        """
        for url in urls:
            data = self.scrape_page(url)
            if data:
                self.scraped_data.append(data)
            
            # Be respectful to the server
            time.sleep(self.delay)
        
        return self.scraped_data
    
    def discover_urls(self, start_url: str, max_depth: int = 2) -> List[str]:
        """
        Discover URLs by following internal links
        
        Args:
            start_url: Starting URL
            max_depth: Maximum depth to crawl
            
        Returns:
            List of discovered URLs
        """
        discovered_urls = set()
        to_visit = [(start_url, 0)]
        visited = set()
        
        while to_visit:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
                
            visited.add(url)
            discovered_urls.add(url)
            
            if depth < max_depth:
                try:
                    response = self.session.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        # Only follow internal links
                        if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                            to_visit.append((full_url, depth + 1))
                
                except Exception as e:
                    self.logger.error(f"Error discovering URLs from {url}: {str(e)}")
                
                time.sleep(self.delay)
        
        return list(discovered_urls)
    
    def save_to_json(self, filename: str = 'scraped_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Data saved to {filename}")
    
    def save_to_csv(self, filename: str = 'scraped_data.csv'):
        """Save scraped data to CSV file"""
        if not self.scraped_data:
            return
        
        # Flatten the data for CSV
        flattened_data = []
        for item in self.scraped_data:
            flat_item = {
                'url': item['url'],
                'timestamp': item['timestamp'],
                'title': item['title'],
                'meta_description': item['meta_description'],
                'main_content': item['main_content'],
                'clean_text': item['clean_text'],
                'h1_headings': '; '.join(item['headings'].get('h1', [])),
                'h2_headings': '; '.join(item['headings'].get('h2', [])),
                'faq_count': len(item['faq_content']),
                'links_count': len(item['links'])
            }
            flattened_data.append(flat_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        self.logger.info(f"Data saved to {filename}")
    
    def create_llm_training_format(self, filename: str = 'llm_training_data.jsonl'):
        """
        Create training data in JSONL format suitable for LLM training
        """
        training_data = []
        
        for item in self.scraped_data:
            # Create different types of training examples
            
            # 1. Q&A from FAQ content
            for faq in item['faq_content']:
                training_data.append({
                    'input': faq['question'],
                    'output': faq['answer'],
                    'source_url': item['url'],
                    'type': 'faq'
                })
            
            # 2. Page summary
            if item['title'] and item['main_content']:
                training_data.append({
                    'input': f"What can you tell me about {item['title']}?",
                    'output': item['main_content'][:500] + "..." if len(item['main_content']) > 500 else item['main_content'],
                    'source_url': item['url'],
                    'type': 'page_summary'
                })
            
            # 3. Product information
            for key, value in item['product_info'].items():
                if value:
                    training_data.append({
                        'input': f"Tell me about the {key} of this product/service",
                        'output': value,
                        'source_url': item['url'],
                        'type': 'product_info'
                    })
        
        # Save as JSONL
        with open(filename, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        self.logger.info(f"LLM training data saved to {filename} ({len(training_data)} examples)")

# Example usage
if __name__ == "__main__":
    # Initialize scraper
    scraper = WebScraperForLLM("https://www.teambuilding-paris.com/", delay=1.0)
    
    # Method 1: Scrape specific URLs
    urls_to_scrape = [
"https://www.teambuilding-paris.com/Team-Building_r6.html"
"https://www.teambuilding-paris.com/Team-Learning_r7.html"
"https://www.teambuilding-paris.com/Venues_r8.html"
"https://www.teambuilding-paris.com/Reveal-Eagles-team-Building_r10.html"
"https://www.teambuilding-paris.com/forms/Quote_f1.html"
"https://www.teambuilding-paris.com/photos/"
"https://www.teambuilding-paris.com/photos/"

    ]
    
    
    print("Scraping specific URLs...")
    scraper.scrape_multiple_urls(urls_to_scrape)
    
    # Method 2: Auto-discover URLs and scrape
    print("Discovering URLs...")
    discovered_urls = scraper.discover_urls("https://your-website.com", max_depth=2)
    print(f"Found {len(discovered_urls)} URLs")
    
    print("Scraping discovered URLs...")
    scraper.scrape_multiple_urls(discovered_urls[:20])  # Limit to first 20 URLs
    
    # Save data in different formats
    scraper.save_to_json('website_data.json')
    scraper.save_to_csv('website_data.csv') 
    scraper.create_llm_training_format('llm_training_data.jsonl')
    
    print(f"Scraping completed! Collected data from {len(scraper.scraped_data)} pages.")