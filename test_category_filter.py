#!/usr/bin/env python3
from core.fetchers.eventbrite_bkk import EventbriteBKKFetcher

def test_category_filter():
    fetcher = EventbriteBKKFetcher()
    events = fetcher.fetch(limit=10)
    
    print(f"Found {len(events)} events without category")
    
    # Test food category filtering
    print("\n🔍 Testing food category filtering...")
    food_keywords = ['food', 'restaurant', 'cooking', 'culinary', 'dining', 'chef', 'kitchen', 'wine', 'beer', 'coffee', 'tea']
    
    food_events = []
    for event in events:
        title = event.title.lower()
        desc = event.desc.lower() if event.desc else ""
        
        # Check if any keyword matches title or description
        if any(keyword in title or keyword in desc for keyword in food_keywords):
            food_events.append(event)
            print(f"  ✅ Food event: {event.title[:50]}...")
        else:
            print(f"  ❌ Not food: {event.title[:50]}...")
    
    print(f"\n📊 Food events found: {len(food_events)} out of {len(events)}")
    
    # Test other categories
    categories = ['workshops', 'music', 'art', 'wellness']
    for category in categories:
        print(f"\n🔍 Testing {category} category...")
        category_keywords = {
            'workshops': ['workshop', 'class', 'training', 'course', 'learning', 'skill', 'craft', 'diy'],
            'music': ['music', 'concert', 'gig', 'band', 'performance', 'show', 'guitar', 'piano', 'vocal'],
            'art': ['art', 'exhibition', 'gallery', 'museum', 'painting', 'sculpture', 'photography'],
            'wellness': ['yoga', 'wellness', 'meditation', 'spa', 'massage', 'fitness', 'health']
        }
        
        keywords = category_keywords.get(category, [category])
        category_events = []
        
        for event in events:
            title = event.title.lower()
            desc = event.desc.lower() if event.desc else ""
            
            if any(keyword in title or keyword in desc for keyword in keywords):
                category_events.append(event)
        
        print(f"  {category.capitalize()} events: {len(category_events)}")

if __name__ == "__main__":
    test_category_filter()
