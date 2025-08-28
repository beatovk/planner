#!/usr/bin/env python3
from core.fetchers.eventbrite_bkk import EventbriteBKKFetcher

def test_event_keys():
    fetcher = EventbriteBKKFetcher()
    events = fetcher.fetch(limit=3)
    
    print('Event keys:')
    for i, e in enumerate(events[:2]):
        print(f'- Event {i+1}:')
        print(f'  Title: {e.title[:30]}...')
        print(f'  Date: {e.start}')
        print(f'  URL: {str(e.url)[:50]}...')
        print(f'  Key: ("{e.title[:30]}...", "{e.start}", "{str(e.url)[:30]}...")')
        print()

if __name__ == "__main__":
    test_event_keys()
