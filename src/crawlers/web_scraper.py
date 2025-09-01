"""
Web scraping module for content extraction
"""
import asyncio
try:
    import aiohttp
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    aiohttp = None
    BeautifulSoup = None
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import time
from ..core.config import config


@dataclass
class ScrapedDocument:
    """Scraped document data structure"""
    url: str
    title: str
    content: str
    metadata: Dict
    links: List[str]
    timestamp: str
    content_type: str = 'web_page'
    
    def to_dict(self) -> Dict:
        return asdict(self)


class WebScraper:
    """Web scraper for extracting content from websites"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scraped_urls: Set[str] = set()
        self.session: Optional = None
        
        if not SCRAPING_AVAILABLE:
            self.logger.warning("Web scraping dependencies not available. Install aiohttp and beautifulsoup4.")
            
        if SCRAPING_AVAILABLE:
            self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
    async def scrape_website(self, start_url: str, max_depth: int = 3, 
                           max_pages: int = 100) -> List[ScrapedDocument]:
        """Scrape website starting from given URL"""
        self.logger.info(f"Starting to scrape: {start_url}")
        
        scraped_documents = []
        urls_to_scrape = [(start_url, 0)]
        
        connector = aiohttp.TCPConnector(limit=config.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=config.request_timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Smart Knowledge Repository Bot 1.0'}
        ) as session:
            self.session = session
            
            while urls_to_scrape and len(scraped_documents) < max_pages:
                current_url, depth = urls_to_scrape.pop(0)
                
                if (current_url in self.scraped_urls or 
                    depth > max_depth or 
                    not self._is_valid_url(current_url)):
                    continue
                
                try:
                    document = await self._scrape_single_page(current_url, depth)
                    if document:
                        scraped_documents.append(document)
                        self.scraped_urls.add(current_url)
                        
                        # Add discovered links for next depth level
                        if depth < max_depth:
                            new_links = self._filter_same_domain_links(
                                document.links, start_url
                            )
                            urls_to_scrape.extend([
                                (link, depth + 1) for link in new_links
                                if link not in self.scraped_urls
                            ])
                        
                        self.logger.info(f"Scraped: {document.title} ({current_url})")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {current_url}: {e}")
                
                # Respect crawl delay
                await asyncio.sleep(config.crawl_delay)
        
        self.logger.info(f"Scraping completed. Collected {len(scraped_documents)} documents")
        return scraped_documents
    
    async def _scrape_single_page(self, url: str, depth: int) -> Optional[ScrapedDocument]:
        """Scrape a single web page"""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"HTTP {response.status} for {url}")
                        return None
                    
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        self.logger.info(f"Skipping non-HTML content: {url}")
                        return None
                    
                    html = await response.text()
                    return self._parse_html_content(url, html)
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout scraping {url}")
                return None
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                return None
    
    def _parse_html_content(self, url: str, html: str) -> Optional[ScrapedDocument]:
        """Parse HTML content and extract structured data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract main content
            content = self._extract_content(soup)
            if len(content.strip()) < 100:  # Skip pages with minimal content
                return None
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            return ScrapedDocument(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                links=links,
                timestamp=datetime.now().isoformat(),
                content_type='web_page'
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try multiple methods to get title
        title_sources = [
            soup.find('title'),
            soup.find('h1'),
            soup.find('meta', attrs={'property': 'og:title'}),
            soup.find('meta', attrs={'name': 'twitter:title'})
        ]
        
        for source in title_sources:
            if source:
                title = source.get('content') if source.name == 'meta' else source.get_text()
                if title and title.strip():
                    return title.strip()[:200]  # Limit title length
        
        return "Untitled Document"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'noscript']):
            element.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'article',
            'main',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '#content'
        ]
        
        content_text = ""
        
        # Try each selector
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content_text = ' '.join([elem.get_text(strip=True) for elem in elements])
                break
        
        # Fallback to body text if no specific content area found
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = body.get_text(strip=True)
        
        # Clean up the text
        content_text = ' '.join(content_text.split())  # Normalize whitespace
        return content_text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from page"""
        metadata = {
            'scraped_at': datetime.now().isoformat(),
            'source_url': url,
            'domain': urlparse(url).netloc
        }
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[f'meta_{name}'] = content[:500]  # Limit metadata length
        
        # Extract language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from page"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            if self._is_valid_url(absolute_url):
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for scraping"""
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            # Only HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                             '.ppt', '.pptx', '.zip', '.rar', '.jpg', '.jpeg', 
                             '.png', '.gif', '.mp3', '.mp4', '.avi']
            
            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _filter_same_domain_links(self, links: List[str], base_url: str) -> List[str]:
        """Filter links to only include same domain"""
        base_domain = urlparse(base_url).netloc
        same_domain_links = []
        
        for link in links:
            try:
                if urlparse(link).netloc == base_domain:
                    same_domain_links.append(link)
            except Exception:
                continue
        
        return same_domain_links

    def scrape_website_sync(self, start_url: str, max_depth: int = 3, 
                           max_pages: int = 100) -> List[ScrapedDocument]:
        """Synchronous wrapper for scrape_website - for use in non-async contexts"""
        if not SCRAPING_AVAILABLE:
            self.logger.error("Scraping dependencies not available. Install aiohttp and beautifulsoup4.")
            return []
        
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async scraping method
            result = loop.run_until_complete(
                self.scrape_website(start_url, max_depth, max_pages)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in synchronous scraping wrapper: {e}")
            return []
        finally:
            try:
                loop.close()
            except:
                pass
