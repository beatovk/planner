from __future__ import annotations
from typing import List, Optional, Dict, Any
import asyncio
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

from .interface import FetcherInterface
from .validator import ensure_events
from ..events import Event
from ..logging import logger


class EventbriteBKKFetcher(FetcherInterface):
    """Eventbrite Bangkok: парсинг событий с главной страницы."""
    name = "eventbrite_bkk"
    SOURCE = "eventbrite_bkk"
    CITY = "bangkok"
    
    _BASE_URL = "https://www.eventbrite.com/d/thailand--bangkok/events/"
    _TIMEOUT = 15.0
    _UA = "Mozilla/5.0 (WeekPlanner/EventbriteFetcher) AppleWebKit/537.36"

    def fetch(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        """Fetch events from Eventbrite Bangkok."""
        try:
            raw = asyncio.run(self._gather(category=category, limit=limit))
            return ensure_events(raw, source_name=self.name)
        except Exception as exc:
            logger.warning("eventbrite_bkk fetch failed: %s", exc)
            return []

    async def _gather(self, category: Optional[str], limit: Optional[int]) -> List[Dict[str, Any]]:
        """Gather events from Eventbrite."""
        # Eventbrite doesn't support category filtering via URL params
        # So we always fetch all events and filter later if needed
        url = self._BASE_URL
        
        async with httpx.AsyncClient(timeout=self._TIMEOUT, headers={"User-Agent": self._UA}) as client:
            response = await client.get(url)
            if response.status_code != 200:
                logger.error(f"Eventbrite returned {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            events = self._parse_events(soup, limit)
            
            # If category is specified, try to filter events by title/description
            if category and events:
                filtered_events = self._filter_by_category(events, category)
                logger.info(f"Filtered {len(events)} events to {len(filtered_events)} for category '{category}'")
                return filtered_events
            
            return events

    def _filter_by_category(self, events: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """Filter events by category using keyword matching."""
        category_keywords = {
            'food': ['food', 'restaurant', 'cooking', 'culinary', 'dining', 'chef', 'kitchen', 'wine', 'beer', 'coffee', 'tea', 'bar', 'pub', 'lounge'],
            'electronic_music': ['electronic', 'edm', 'techno', 'house', 'trance', 'dubstep', 'dance', 'dj', 'club', 'party', 'nightlife'],
            'live_music_gigs': ['live music', 'concert', 'gig', 'band', 'performance', 'show', 'music', 'guitar', 'piano', 'vocal', 'singer', 'musician'],
            'jazz_blues': ['jazz', 'blues', 'saxophone', 'trumpet', 'piano jazz', 'blues band', 'jazz band'],
            'rooftops_bars': ['rooftop', 'bar', 'pub', 'cocktail', 'wine bar', 'beer garden', 'lounge', 'nightlife', 'drinks'],
            'art_exhibits': ['art', 'exhibition', 'gallery', 'museum', 'painting', 'sculpture', 'photography', 'installation', 'creative', 'culture'],
            'workshops': ['workshop', 'class', 'training', 'course', 'learning', 'skill', 'craft', 'diy', 'education', 'seminar', 'conference', 'meetup', 'coding', 'programming', 'tech', 'it'],
            'cinema': ['cinema', 'movie', 'film', 'theater', 'screening', 'premiere', 'documentary', 'cinema', 'movie'],
            'markets_fairs': ['market', 'fair', 'bazaar', 'festival', 'exhibition', 'trade show', 'craft fair', 'expo', 'conference', 'meetup'],
            'yoga_wellness': ['yoga', 'wellness', 'meditation', 'spa', 'massage', 'fitness', 'health', 'mindfulness', 'wellness'],
            'parks_walks': ['park', 'walk', 'hiking', 'nature', 'outdoor', 'garden', 'trail', 'tour', 'adventure', 'exploration']
        }
        
        keywords = category_keywords.get(category.lower(), [category.lower()])
        
        filtered = []
        for event in events:
            title = event.get('title', '').lower()
            desc = event.get('desc', '').lower()
            
            # Check if any keyword matches title or description
            if any(keyword in title or keyword in desc for keyword in keywords):
                filtered.append(event)
        
        return filtered

    def _parse_events(self, soup: BeautifulSoup, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Parse events from BeautifulSoup."""
        events = []
        
        # Find event cards
        cards = soup.select(".event-card, [data-testid='event-card'], .eds-event-card")
        if not cards:
            # Fallback selectors
            cards = soup.select("article, .card, .item")
        
        logger.info(f"Found {len(cards)} event cards")
        
        # Debug: show what we found
        if cards:
            logger.info(f"First card classes: {cards[0].get('class', [])}")
            logger.info(f"First card HTML preview: {str(cards[0])[:200]}...")
        
        for i, card in enumerate(cards):
            if limit and len(events) >= limit:
                break
                
            try:
                logger.info(f"Parsing card {i+1}/{len(cards)}")
                event = self._parse_event_card(card)
                if event:
                    events.append(event)
                    logger.info(f"Successfully parsed event: {event.get('title', 'No title')[:30]}...")
                else:
                    logger.warning(f"Failed to parse card {i+1}")
            except Exception as e:
                logger.warning(f"Error parsing event card {i+1}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(events)} events out of {len(cards)} cards")
        return events

    def _parse_event_card(self, card) -> Optional[Dict[str, Any]]:
        """Parse a single event card."""
        # Title
        title = self._extract_title(card)
        if not title:
            return None
        
        # URL
        url = self._extract_url(card)
        if not url:
            return None
        
        # Date
        start_date, end_date, time_str = self._extract_dates(card)
        
        # Description
        description = self._extract_description(card)
        
        # Image
        image = self._extract_image(card)
        
        # Venue
        venue = self._extract_venue(card)
        
        # Generate ID
        event_id = f"eventbrite_{hash(title + url) % 1000000}"
        
        event = {
            "id": event_id,
            "title": title,
            "desc": description,
            "url": url,
            "image": image,
            "start": start_date,
            "end": end_date,
            "time_str": time_str,
            "venue": venue,
            "tags": ["Eventbrite", "Bangkok"],
            "source": self.name,
        }
        
        return event

    def _extract_title(self, card) -> Optional[str]:
        """Extract event title from card."""
        title_selectors = [
            "h3", "h2", "h1",
            ".eds-event-card__title",
            ".event-title",
            "[data-testid='event-title']",
            ".title",
            "a"
        ]
        
        for selector in title_selectors:
            title_el = card.select_one(selector)
            if title_el:
                title = title_el.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return None

    def _extract_url(self, card) -> Optional[str]:
        """Extract event URL from card."""
        links = card.select("a")
        for link in links:
            href = link.get('href', '')
            if href and 'eventbrite.com' in href and '/e/' in href:
                if href.startswith('/'):
                    return f"https://www.eventbrite.com{href}"
                return href
        return None

    def _extract_dates(self, card) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract event dates from card."""
        # First try to find date elements
        date_selectors = [
            "time",
            ".eds-event-card__formatted-date",
            ".event-date",
            "[data-testid='event-date']",
            ".eds-text-bs",
            ".date",
            ".time"
        ]
        
        for selector in date_selectors:
            date_el = card.select_one(selector)
            if date_el:
                # Check datetime attribute first
                datetime_attr = date_el.get('datetime')
                if datetime_attr:
                    try:
                        # Parse ISO date
                        dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        return dt.isoformat(), None, dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                # Check text content
                date_text = date_el.get_text(strip=True)
                if date_text:
                    # Try to parse common date formats
                    parsed_date = self._parse_date_text(date_text)
                    if parsed_date:
                        return parsed_date, None, date_text
        
        # If no date elements found, search in entire card text
        card_text = card.get_text()
        parsed_date = self._parse_date_text(card_text)
        if parsed_date:
            return parsed_date, None, "Found in card text"
        
        # Fallback: use current date
        today = datetime.now()
        return today.isoformat(), None, "Today"

    def _parse_date_text(self, date_text: str) -> Optional[str]:
        """Parse date from text."""
        # Common Eventbrite date patterns
        patterns = [
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
            r'\b(\d{4})-(\d{2})-(\d{2})\b',
            r'\b(?:Today|Tomorrow|This weekend|Next week)\b',
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b'
        ]
        
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Debug: log what we're trying to parse
        logger.info(f"Parsing date text: '{date_text[:100]}...'")
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                logger.info(f"Pattern {i+1} matched: {match.group()}")
                try:
                    if len(match.groups()) == 3:
                        if pattern == patterns[0]:  # "12 Jan 2025"
                            day, month, year = int(match.group(1)), month_map[match.group(2).lower()], int(match.group(3))
                        elif pattern == patterns[1]:  # "Jan 12, 2025"
                            month, day, year = month_map[match.group(1).lower()], int(match.group(2)), int(match.group(3))
                        elif pattern == patterns[2]:  # "2025-01-12"
                            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        elif pattern == patterns[3]:  # "12/01/2025"
                            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        
                        dt = datetime(year, month, day)
                        logger.info(f"Successfully parsed date: {dt.isoformat()}")
                        return dt.isoformat()
                    elif len(match.groups()) == 2:
                        # Handle patterns without year (assume current year)
                        if pattern == patterns[4]:  # "12 Jan"
                            day, month = int(match.group(1)), month_map[match.group(2).lower()]
                            year = datetime.now().year
                        elif pattern == patterns[5]:  # "Jan 12"
                            month, day = month_map[match.group(1).lower()], int(match.group(2))
                            year = datetime.now().year
                        
                        dt = datetime(year, month, day)
                        logger.info(f"Successfully parsed date (no year): {dt.isoformat()}")
                        return dt.isoformat()
                except Exception as e:
                    logger.warning(f"Error parsing date from match '{match.group()}': {e}")
                    continue
        
        logger.warning(f"No date patterns matched for text: '{date_text[:100]}...'")
        return None

    def _extract_description(self, card) -> Optional[str]:
        """Extract event description from card."""
        desc_selectors = [
            "p",
            ".description",
            ".summary",
            ".excerpt",
            ".eds-event-card__description"
        ]
        
        for selector in desc_selectors:
            desc_el = card.select_one(selector)
            if desc_el:
                desc = desc_el.get_text(strip=True)
                if desc and len(desc) > 10:
                    return desc[:200] + "..." if len(desc) > 200 else desc
        
        return None

    def _extract_image(self, card) -> Optional[str]:
        """Extract event image from card."""
        images = card.select("img")
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                if src.startswith('//'):
                    return f"https:{src}"
                elif src.startswith('/'):
                    return f"https://www.eventbrite.com{src}"
                elif src.startswith('http'):
                    return src
        return None

    def _extract_venue(self, card) -> Optional[str]:
        """Extract event venue from card."""
        venue_selectors = [
            ".venue",
            ".location",
            ".address",
            ".place",
            ".eds-event-card__venue"
        ]
        
        for selector in venue_selectors:
            venue_el = card.select_one(selector)
            if venue_el:
                venue = venue_el.get_text(strip=True)
                if venue and len(venue) > 3:
                    return venue
        
        return "Bangkok, Thailand"
