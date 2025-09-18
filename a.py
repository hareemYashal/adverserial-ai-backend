import requests
import time
from urllib.parse import quote
import json

class PaperFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_crossref(self, title, authors=None, timeout=10):
        """CrossRef API se search karta hai"""
        try:
            base_url = "https://api.crossref.org/works"
            params = {
                'query.title': title,
                'rows': 5
            }
            if authors:
                params['query.author'] = authors[0] if isinstance(authors, list) else authors
            
            response = self.session.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data['message']['items']:
                result = {
                    'source': 'CrossRef',
                    'title': item['title'][0] if item.get('title') else 'No title',
                    'authors': [author.get('given', '') + ' ' + author.get('family', '') 
                              for author in item.get('author', [])],
                    'doi': item.get('DOI', 'No DOI'),
                    'url': f"https://doi.org/{item['DOI']}" if item.get('DOI') else 'No URL',
                    'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0],
                    'journal': item.get('container-title', ['Unknown'])[0]
                }
                results.append(result)
            
            return results
            
        except requests.exceptions.Timeout:
            print(f"⚠️ CrossRef timeout after {timeout} seconds")
            return []
        except Exception as e:
            print(f"❌ CrossRef error: {str(e)}")
            return []
    
    def search_semantic_scholar(self, title, timeout=10):
        """Semantic Scholar API se search karta hai"""
        try:
            base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': title,
                'limit': 5,
                'fields': 'title,authors,year,journal,doi,url'
            }
            
            response = self.session.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('data', []):
                result = {
                    'source': 'Semantic Scholar',
                    'title': item.get('title', 'No title'),
                    'authors': [author.get('name', 'Unknown') 
                              for author in item.get('authors', [])],
                    'doi': item.get('doi', 'No DOI'),
                    'url': item.get('url', 'No URL'),
                    'year': item.get('year'),
                    'journal': item.get('journal', {}).get('name', 'Unknown') if item.get('journal') else 'Unknown'
                }
                results.append(result)
            
            return results
            
        except requests.exceptions.Timeout:
            print(f"⚠️ Semantic Scholar timeout after {timeout} seconds")
            return []
        except Exception as e:
            print(f"❌ Semantic Scholar error: {str(e)}")
            return []
    
    def search_pubmed(self, title, authors=None, timeout=10):
        """PubMed API se search karta hai"""
        try:
            # PubMed search
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': f'"{title}"',
                'retmode': 'json',
                'retmax': 5
            }
            
            if authors:
                author_query = f" AND {authors[0]}[Author]" if isinstance(authors, list) else f" AND {authors}[Author]"
                search_params['term'] += author_query
            
            search_response = self.session.get(search_url, params=search_params, timeout=timeout)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            ids = search_data.get('esearchresult', {}).get('idlist', [])
            
            if not ids:
                return []
            
            # Get details
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(ids),
                'retmode': 'json'
            }
            
            fetch_response = self.session.get(fetch_url, params=fetch_params, timeout=timeout)
            fetch_response.raise_for_status()
            fetch_data = fetch_response.json()
            
            results = []
            for uid, item in fetch_data.get('result', {}).items():
                if uid == 'uids':
                    continue
                    
                result = {
                    'source': 'PubMed',
                    'title': item.get('title', 'No title'),
                    'authors': [author.get('name', 'Unknown') 
                              for author in item.get('authors', [])],
                    'doi': item.get('elocationid', '').replace('doi: ', '') or 'No DOI',
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    'year': item.get('pubdate', '').split(' ')[0],
                    'journal': item.get('source', 'Unknown')
                }
                results.append(result)
            
            return results
            
        except requests.exceptions.Timeout:
            print(f"⚠️ PubMed timeout after {timeout} seconds")
            return []
        except Exception as e:
            print(f"❌ PubMed error: {str(e)}")
            return []
    
    def search_all_sources(self, title, authors=None):
        """Sabhi sources se search karta hai"""
        print(f"🔍 Searching for: '{title}'")
        if authors:
            print(f"📝 Authors: {authors}")
        print("-" * 60)
        
        all_results = []
        
        # Method 1: CrossRef
        print("🔄 Searching CrossRef...")
        crossref_results = self.search_crossref(title, authors)
        all_results.extend(crossref_results)
        print(f"✅ Found {len(crossref_results)} results from CrossRef")
        time.sleep(1)  # Rate limiting
        
        # Method 2: Semantic Scholar
        print("🔄 Searching Semantic Scholar...")
        semantic_results = self.search_semantic_scholar(title)
        all_results.extend(semantic_results)
        print(f"✅ Found {len(semantic_results)} results from Semantic Scholar")
        time.sleep(1)  # Rate limiting
        
        # Method 3: PubMed
        print("🔄 Searching PubMed...")
        pubmed_results = self.search_pubmed(title, authors)
        all_results.extend(pubmed_results)
        print(f"✅ Found {len(pubmed_results)} results from PubMed")
        
        return all_results
    
    def display_results(self, results):
        """Results ko nicely display karta hai"""
        if not results:
            print("❌ No papers found!")
            return
        
        print(f"\n📊 Total Results Found: {len(results)}")
        print("=" * 80)
        
        for i, paper in enumerate(results, 1):
            print(f"\n📄 Result #{i}")
            print(f"🏷️  Source: {paper['source']}")
            print(f"📖 Title: {paper['title']}")
            print(f"👥 Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
            print(f"📅 Year: {paper.get('year', 'Unknown')}")
            print(f"📰 Journal: {paper['journal']}")
            print(f"🔗 DOI: {paper['doi']}")
            print(f"🌐 URL: {paper['url']}")
            print("-" * 60)

def main():
    # Your research paper details
    paper_info = {
        "title": "Equity in Health and Health Care: A Conceptual Framework",
        "authors": ["Pereira, A.", "Bennett, J."]
    }
    
    # Initialize finder
    finder = PaperFinder()
    
    # Search all sources
    results = finder.search_all_sources(
        title=paper_info["title"],
        authors=paper_info["authors"]
    )
    
    # Display results
    finder.display_results(results)
    
    # Save to JSON file
    with open('search_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to 'search_results.json'")

if __name__ == "__main__":
    main()