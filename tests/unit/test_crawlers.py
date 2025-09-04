"""
Tests for web scraper functionality
"""
import unittest
from unittest.mock import Mock, patch
from src.crawlers.web_scraper import WebScraper, ScrapedDocument
from bs4 import BeautifulSoup


class TestWebScraper(unittest.TestCase):
    """Test cases for WebScraper"""
    
    def setUp(self):
        """Set up test environment"""
        self.scraper = WebScraper()
        self.scraper.logger.disabled = True
    
    def test_is_valid_url(self):
        """Test URL validation"""
        valid_urls = [
            'https://example.com',
            'http://test.org/page',
            'https://subdomain.example.com/path'
        ]
        
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            'https://example.com/file.pdf',
            ''
        ]
        
        for url in valid_urls:
            self.assertTrue(self.scraper._is_valid_url(url), f"Should be valid: {url}")
        
        for url in invalid_urls:
            self.assertFalse(self.scraper._is_valid_url(url), f"Should be invalid: {url}")
    
    def test_extract_title(self):
        """Test title extraction from HTML"""
        html = """
        <html>
            <head>
                <title>Test Page Title</title>
            </head>
            <body>
                <h1>Main Heading</h1>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        title = self.scraper._extract_title(soup)
        
        self.assertEqual(title, "Test Page Title")
    
    def test_extract_content(self):
        """Test content extraction from HTML"""
        html = """
        <html>
            <body>
                <nav>Navigation menu</nav>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the main content of the article.</p>
                    <p>Another paragraph with useful information.</p>
                </article>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        content = self.scraper._extract_content(soup)
        
        self.assertIn("main content", content)
        self.assertNotIn("Navigation menu", content)
        self.assertNotIn("Footer content", content)
    
    def test_extract_links(self):
        """Test link extraction from HTML"""
        html = """
        <html>
            <body>
                <a href="https://example.com/page1">Link 1</a>
                <a href="/relative-link">Relative Link</a>
                <a href="mailto:test@example.com">Email Link</a>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com"
        links = self.scraper._extract_links(soup, base_url)
        
        self.assertIn("https://example.com/page1", links)
        self.assertIn("https://example.com/relative-link", links)
    
    def test_filter_same_domain_links(self):
        """Test same domain link filtering"""
        links = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://other-site.com/page",
            "https://subdomain.example.com/page"
        ]
        
        base_url = "https://example.com"
        filtered_links = self.scraper._filter_same_domain_links(links, base_url)
        
        self.assertIn("https://example.com/page1", filtered_links)
        self.assertIn("https://example.com/page2", filtered_links)
        self.assertNotIn("https://other-site.com/page", filtered_links)
        self.assertNotIn("https://subdomain.example.com/page", filtered_links)


if __name__ == '__main__':
    unittest.main()
