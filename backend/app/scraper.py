import requests
from bs4 import BeautifulSoup
import logging

def scrape_fighters_from_fight(fight_url: str):
    response = requests.get(fight_url)
    if response.status_code != 200:
        return None, None
    
    soup = BeautifulSoup(response.text, "html.parser")
    fighter_links = soup.select("a[href*='/fighter-details/']")
    if len(fighter_links) < 2:
        return None, None
    
    fighter1_url = fighter_links[0]["href"].strip()
    fighter2_url = fighter_links[1]["href"].strip()
    if not fighter1_url or not fighter2_url:
        logging.warning(f"Scraping failed for fight URL: {fight_url}")
    return fighter1_url, fighter2_url