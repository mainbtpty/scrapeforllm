from web_scraper import WebScraperForLLM

def scrape_eagles_team_experiences():
    """Scrape only the Eagles Team Experiences website"""
    
    # Your actual website
    EAGLES_WEBSITE = "https://www.teambuilding-paris.com/"
    
    # Initialize scraper
    scraper = WebScraperForLLM(EAGLES_WEBSITE, delay=1.5)
    
    # Specific pages to scrape
    eagles_pages = [
        f"{EAGLES_WEBSITE}/",  # Homepage
        f"{EAGLES_WEBSITE}/about", # About page (has lots of FAQ content)
        f"{EAGLES_WEBSITE}/faq",   # FAQ page
        f"{EAGLES_WEBSITE}/contact",
        f"{EAGLES_WEBSITE}/services",
        f"{EAGLES_WEBSITE}/team-building",
        f"{EAGLES_WEBSITE}/experiences",
        # Add more if you know specific URLs
    ]
    
    print(f"🎯 Scraping Eagles Team Experiences website...")
    print(f"Will scrape {len(eagles_pages)} specific pages")
    
    # Scrape specific pages
    results = scraper.scrape_multiple_urls(eagles_pages)
    
    # Auto-discover more Eagles URLs (optional)
    print(f"\n🔍 Discovering more Eagles URLs...")
    discovered = scraper.discover_urls(EAGLES_WEBSITE, max_depth=1)
    
    # Filter to keep only Eagles URLs and avoid duplicates
    eagles_urls = []
    already_scraped = set(eagles_pages)
    
    for url in discovered:
        if EAGLES_WEBSITE in url and url not in already_scraped:
            eagles_urls.append(url)
    
    print(f"Found {len(eagles_urls)} additional Eagles URLs")
    
    # Scrape additional Eagles URLs
    if eagles_urls:
        additional_results = scraper.scrape_multiple_urls(eagles_urls[:10])
    
    # Save results with clear filename
    scraper.save_to_json('eagles_team_data.json')
    scraper.save_to_csv('eagles_team_data.csv')
    scraper.create_llm_training_format('eagles_training_data.jsonl')
    
    print(f"\n✅ Scraping complete!")
    print(f"📊 Total pages scraped: {len(scraper.scraped_data)}")
    print(f"📁 Files created:")
    print(f"  - eagles_team_data.json")
    print(f"  - eagles_team_data.csv") 
    print(f"  - eagles_training_data.jsonl")
    
    return scraper.scraped_data

if __name__ == "__main__":
    scrape_eagles_team_experiences()