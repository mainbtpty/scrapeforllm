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

class CompleteTextWebScraper:
    def __init__(self, base_url: str, delay: float = 1.0):
        """
        Initialize the complete text web scraper
        
        Args:
            base_url: The base URL of the website to scrape
            delay: Delay between requests to be respectful to the server
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        Scrape ALL available text from a single page
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing ALL extracted text or None if failed
        """
        try:
            self.logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract EVERYTHING
            data = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'all_headings': self._extract_all_headings(soup),
                'complete_body_text': self._extract_complete_body_text(soup),
                'all_paragraph_text': self._extract_all_paragraphs(soup),
                'all_list_items': self._extract_all_lists(soup),
                'all_table_text': self._extract_all_tables(soup),
                'all_form_labels': self._extract_form_text(soup),
                'all_button_text': self._extract_button_text(soup),
                'all_link_text': self._extract_all_link_text(soup),
                'alt_text': self._extract_alt_text(soup),
                'title_attributes': self._extract_title_attributes(soup),
                'data_attributes': self._extract_data_attributes(soup),
                'complete_visible_text': self._extract_all_visible_text(soup),
                'structured_content': self._extract_structured_content(soup),
                'page_statistics': self._calculate_page_statistics(soup)
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
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        return meta_desc.get('content', '').strip() if meta_desc else ""
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        return meta_keywords.get('content', '').strip() if meta_keywords else ""
    
    def _extract_all_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract ALL headings with their levels and text"""
        headings = []
        for i in range(1, 7):
            heading_tags = soup.find_all(f'h{i}')
            for heading in heading_tags:
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': f'h{i}',
                        'text': text
                    })
        return headings
    
    def _extract_complete_body_text(self, soup: BeautifulSoup) -> str:
        """Extract ALL text from body, excluding only scripts and styles"""
        # Remove only scripts, styles, and comments
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.startswith('<!--')):
            comment.extract()
        
        # Get all text from body
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace but preserve structure
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_all_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract text from ALL paragraph tags"""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 10:  # Only substantial paragraphs
                paragraphs.append(text)
        return paragraphs
    
    def _extract_all_lists(self, soup: BeautifulSoup) -> List[Dict[str, any]]:
        """Extract ALL list items (ul, ol, dl)"""
        lists = []
        
        # Unordered and ordered lists
        for list_type in ['ul', 'ol']:
            for list_elem in soup.find_all(list_type):
                items = []
                for li in list_elem.find_all('li'):
                    text = li.get_text().strip()
                    if text:
                        items.append(text)
                if items:
                    lists.append({
                        'type': list_type,
                        'items': items
                    })
        
        # Definition lists
        for dl in soup.find_all('dl'):
            terms_and_defs = []
            for dt in dl.find_all('dt'):
                term = dt.get_text().strip()
                dd = dt.find_next_sibling('dd')
                definition = dd.get_text().strip() if dd else ""
                if term:
                    terms_and_defs.append({
                        'term': term,
                        'definition': definition
                    })
            if terms_and_defs:
                lists.append({
                    'type': 'dl',
                    'items': terms_and_defs
                })
        
        return lists
    
    def _extract_all_tables(self, soup: BeautifulSoup) -> List[Dict[str, any]]:
        """Extract ALL text from tables"""
        tables = []
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Extract headers
            headers = table.find_all('th')
            table_data['headers'] = [th.get_text().strip() for th in headers]
            
            # Extract all rows
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                if any(row_data):  # Only non-empty rows
                    table_data['rows'].append(row_data)
            
            if table_data['headers'] or table_data['rows']:
                tables.append(table_data)
        
        return tables
    
    def _extract_form_text(self, soup: BeautifulSoup) -> List[str]:
        """Extract ALL form-related text (labels, placeholders, values)"""
        form_text = []
        
        # Labels
        for label in soup.find_all('label'):
            text = label.get_text().strip()
            if text:
                form_text.append(text)
        
        # Input placeholders and values
        for input_elem in soup.find_all('input'):
            placeholder = input_elem.get('placeholder', '').strip()
            value = input_elem.get('value', '').strip()
            if placeholder:
                form_text.append(f"Placeholder: {placeholder}")
            if value and input_elem.get('type') not in ['password', 'hidden']:
                form_text.append(f"Value: {value}")
        
        # Textarea placeholders
        for textarea in soup.find_all('textarea'):
            placeholder = textarea.get('placeholder', '').strip()
            text = textarea.get_text().strip()
            if placeholder:
                form_text.append(f"Placeholder: {placeholder}")
            if text:
                form_text.append(f"Text: {text}")
        
        # Option text
        for option in soup.find_all('option'):
            text = option.get_text().strip()
            if text:
                form_text.append(text)
        
        return form_text
    
    def _extract_button_text(self, soup: BeautifulSoup) -> List[str]:
        """Extract ALL button text"""
        buttons = []
        for button in soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
                continue
            
            text = button.get_text().strip()
            value = button.get('value', '').strip()
            
            if text:
                buttons.append(text)
            elif value:
                buttons.append(value)
        
        return buttons
    
    def _extract_all_link_text(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract ALL link text and URLs"""
        links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip()
            href = link['href']
            title = link.get('title', '').strip()
            
            if text or title:
                full_url = urljoin(self.base_url, href)
                links.append({
                    'url': full_url,
                    'text': text,
                    'title': title
                })
        return links
    
    def _extract_alt_text(self, soup: BeautifulSoup) -> List[str]:
        """Extract ALL alt text from images"""
        alt_texts = []
        for img in soup.find_all('img'):
            alt = img.get('alt', '').strip()
            if alt:
                alt_texts.append(alt)
        return alt_texts
    
    def _extract_title_attributes(self, soup: BeautifulSoup) -> List[str]:
        """Extract ALL title attributes"""
        titles = []
        for elem in soup.find_all(attrs={'title': True}):
            title = elem.get('title', '').strip()
            if title:
                titles.append(title)
        return titles
    
    def _extract_data_attributes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract data attributes that might contain text"""
        data_attrs = []
        for elem in soup.find_all():
            for attr_name, attr_value in elem.attrs.items():
                if attr_name.startswith('data-') and isinstance(attr_value, str) and len(attr_value.strip()) > 3:
                    data_attrs.append({
                        'attribute': attr_name,
                        'value': attr_value.strip()
                    })
        return data_attrs
    
    def _extract_all_visible_text(self, soup: BeautifulSoup) -> str:
        """Extract ALL visible text using a comprehensive approach"""
        # Remove invisible elements
        invisible_elements = [
            'script', 'style', 'noscript', 'meta', 'link', 'title',
            '[style*="display:none"]', '[style*="visibility:hidden"]',
            '.sr-only', '.visually-hidden', '.screen-reader-text'
        ]
        
        for selector in invisible_elements:
            for elem in soup.select(selector):
                elem.decompose()
        
        # Get all remaining text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract content organized by HTML structure"""
        structured = {
            'nav_text': [],
            'header_text': [],
            'main_text': [],
            'aside_text': [],
            'footer_text': [],
            'article_text': [],
            'section_text': []
        }
        
        sections = {
            'nav': 'nav_text',
            'header': 'header_text',
            'main': 'main_text',
            'aside': 'aside_text',
            'footer': 'footer_text',
            'article': 'article_text',
            'section': 'section_text'
        }
        
        for tag, key in sections.items():
            elements = soup.find_all(tag)
            for elem in elements:
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    structured[key].append(text)
        
        return structured
    
    def _calculate_page_statistics(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Calculate statistics about the page content"""
        text = soup.get_text()
        return {
            'total_characters': len(text),
            'total_words': len(text.split()),
            'total_paragraphs': len(soup.find_all('p')),
            'total_headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'total_links': len(soup.find_all('a')),
            'total_images': len(soup.find_all('img')),
            'total_lists': len(soup.find_all(['ul', 'ol', 'dl'])),
            'total_tables': len(soup.find_all('table'))
        }
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs and extract ALL text from each"""
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            data = self.scrape_page(url)
            if data:
                self.scraped_data.append(data)
                self.logger.info(f"✅ Successfully scraped {data['page_statistics']['total_words']} words from {url}")
            else:
                self.logger.warning(f"❌ Failed to scrape {url}")
            
            # Be respectful to the server
            if i < len(urls):  # Don't wait after the last URL
                self.logger.info(f"Waiting {self.delay} seconds...")
                time.sleep(self.delay)
        
        return self.scraped_data
    
    def save_to_json(self, filename: str = 'complete_scraped_data.json'):
        """Save ALL scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        
        total_words = sum(item['page_statistics']['total_words'] for item in self.scraped_data)
        self.logger.info(f"✅ Complete data saved to {filename}")
        self.logger.info(f"📊 Total: {len(self.scraped_data)} pages, {total_words:,} words")
    
    def create_text_only_file(self, filename: str = 'all_text_content.txt'):
        """Create a simple text file with ALL extracted text"""
        with open(filename, 'w', encoding='utf-8') as f:
            for item in self.scraped_data:
                f.write(f"\n{'='*80}\n")
                f.write(f"URL: {item['url']}\n")
                f.write(f"TITLE: {item['title']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(item['complete_visible_text'])
                f.write(f"\n\n")
        
        self.logger.info(f"✅ Text-only file saved to {filename}")
    
    def discover_all_pages(self, start_url: str, max_pages: int = 50, max_depth: int = 3) -> List[str]:
        """
        Automatically discover ALL pages on the website starting from homepage
        
        Args:
            start_url: Starting URL (homepage)
            max_pages: Maximum number of pages to discover (safety limit)
            max_depth: Maximum depth to crawl from homepage
            
        Returns:
            List of all discovered page URLs
        """
        discovered_urls = set()
        to_visit = [(start_url, 0)]
        visited = set()
        base_domain = urlparse(self.base_url).netloc
        
        self.logger.info(f"🔍 Starting automatic page discovery from: {start_url}")
        self.logger.info(f"📊 Limits: {max_pages} pages max, {max_depth} levels deep")
        
        while to_visit and len(discovered_urls) < max_pages:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
            
            # Clean URL (remove fragments and normalize)
            clean_url = url.split('#')[0]  # Remove fragments
            if clean_url in visited:
                continue
                
            visited.add(clean_url)
            discovered_urls.add(clean_url)
            
            self.logger.info(f"📄 Discovered page {len(discovered_urls)}: {clean_url}")
            
            # Only follow links if we haven't reached max depth
            if depth < max_depth and len(discovered_urls) < max_pages:
                try:
                    response = self.session.get(clean_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all internal links
                    links_found = 0
                    for link in soup.find_all('a', href=True):
                        href = link['href'].strip()
                        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                            continue
                        
                        # Convert to absolute URL
                        full_url = urljoin(clean_url, href)
                        parsed_url = urlparse(full_url)
                        
                        # Only follow internal links (same domain)
                        if parsed_url.netloc == base_domain or parsed_url.netloc == '':
                            # Exclude common file extensions and admin paths
                            excluded_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx')
                            excluded_paths = ('/admin/', '/wp-admin/', '/login/', '/register/', '/api/')
                            
                            if (not any(full_url.lower().endswith(ext) for ext in excluded_extensions) and
                                not any(path in full_url.lower() for path in excluded_paths)):
                                
                                to_visit.append((full_url, depth + 1))
                                links_found += 1
                    
                    self.logger.info(f"   🔗 Found {links_found} internal links on this page")
                
                except Exception as e:
                    self.logger.warning(f"⚠️  Error discovering links from {clean_url}: {str(e)}")
                
                # Small delay between discovery requests
                time.sleep(0.5)
        
        final_urls = list(discovered_urls)
        self.logger.info(f"✅ Discovery complete! Found {len(final_urls)} unique pages")
        return final_urls
    
    def scrape_entire_website(self, start_url: str, max_pages: int = 50, max_depth: int = 3) -> List[Dict]:
        """
        Discover and scrape ALL pages on the website automatically
        
        Args:
            start_url: Starting URL (usually homepage)
            max_pages: Maximum number of pages to scrape
            max_depth: Maximum crawl depth from homepage
            
        Returns:
            List of all scraped page data
        """
        # Step 1: Discover all pages
        self.logger.info("🚀 PHASE 1: Discovering all website pages...")
        all_urls = self.discover_all_pages(start_url, max_pages, max_depth)
        
        if not all_urls:
            self.logger.error("❌ No pages discovered! Check the starting URL.")
            return []
        
        # Step 2: Scrape all discovered pages
        self.logger.info(f"🚀 PHASE 2: Scraping all {len(all_urls)} discovered pages...")
        successful_scrapes = 0
        
        for i, url in enumerate(all_urls, 1):
            self.logger.info(f"📄 Scraping page {i}/{len(all_urls)}: {url}")
            
            data = self.scrape_page(url)
            if data:
                self.scraped_data.append(data)
                successful_scrapes += 1
                self.logger.info(f"   ✅ Success! Extracted {data['page_statistics']['total_words']:,} words")
            else:
                self.logger.warning(f"   ❌ Failed to scrape {url}")
            
            # Progress update every 10 pages
            if i % 10 == 0:
                self.logger.info(f"📊 Progress: {i}/{len(all_urls)} pages processed ({successful_scrapes} successful)")
            
            # Be respectful - delay between requests
            if i < len(all_urls):
                time.sleep(self.delay)
        
        self.logger.info(f"✅ Website scraping complete!")
        self.logger.info(f"   📊 Total pages found: {len(all_urls)}")
        self.logger.info(f"   ✅ Successfully scraped: {successful_scrapes}")
        self.logger.info(f"   ❌ Failed to scrape: {len(all_urls) - successful_scrapes}")
        
        return self.scraped_data
    
    def get_summary_stats(self):
        """Get summary statistics of all scraped data"""
        if not self.scraped_data:
            return {}
        
        total_words = sum(item['page_statistics']['total_words'] for item in self.scraped_data)
        total_chars = sum(item['page_statistics']['total_characters'] for item in self.scraped_data)
        total_links = sum(item['page_statistics']['total_links'] for item in self.scraped_data)
        
        return {
            'total_pages': len(self.scraped_data),
            'total_words': total_words,
            'total_characters': total_chars,
            'total_links': total_links,
            'average_words_per_page': total_words // len(self.scraped_data) if self.scraped_data else 0,
            'urls_scraped': [item['url'] for item in self.scraped_data]
        }

# Example usage
if __name__ == "__main__":
    # Initialize the complete text scraper
    homepage_url = "https://www.teambuilding-teamlearning.com/"
    scraper = CompleteTextWebScraper(homepage_url, delay=2.0)
    
    print("🚀 Starting AUTOMATIC WEBSITE CRAWLING...")
    print(f"🌐 Starting from homepage: {homepage_url}")
    print("🔍 Will automatically discover and scrape ALL website pages...")
    
    # Automatically discover and scrape ALL pages on the website
    # max_pages: limit for safety (increase if needed)
    # max_depth: how many levels deep to crawl from homepage
    all_scraped_data = scraper.scrape_entire_website(
        start_url=homepage_url,
        max_pages=100,  # Adjust this number based on website size
        max_depth=4     # Adjust crawl depth (4 levels should cover most sites)
    )
    
    if all_scraped_data:
        # Get comprehensive statistics
        stats = scraper.get_summary_stats()
        print(f"\n🎉 COMPLETE WEBSITE SCRAPING FINISHED!")
        print(f"   ✅ Total pages scraped: {stats.get('total_pages', 0)}")
        print(f"   📝 Total words extracted: {stats.get('total_words', 0):,}")
        print(f"   📄 Total characters: {stats.get('total_characters', 0):,}")
        print(f"   🔗 Total links found: {stats.get('total_links', 0):,}")
        print(f"   📊 Average words per page: {stats.get('average_words_per_page', 0):,}")
        
        # Save comprehensive data
        scraper.save_to_json('complete_website_data.json')
        scraper.create_text_only_file('complete_website_text.txt')
        
        print(f"\n💾 Files created:")
        print(f"   📁 complete_website_data.json - ALL pages structured data")
        print(f"   📄 complete_website_text.txt - ALL pages text content")
        
        print(f"\n📋 Pages scraped:")
        for i, url in enumerate(stats.get('urls_scraped', []), 1):
            print(f"   {i:2d}. {url}")
        
        print(f"\n🎯 Complete website data ready for IntelliWeave AI!")
        
    else:
        print("❌ No pages were successfully scraped. Please check:")
        print("   - Internet connection")
        print("   - Website URL is correct")
        print("   - Website is accessible")
        
    print(f"\n🏁 Scraping process completed!")