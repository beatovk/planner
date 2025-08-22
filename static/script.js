let selectedCategories = new Set();

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        const grid = document.getElementById('categoriesGrid');
        grid.innerHTML = '';
        
        categories.forEach(category => {
            const btn = document.createElement('button');
            btn.className = 'category-btn';
            btn.textContent = category.label;
            btn.onclick = () => toggleCategory(category.id, btn);
            grid.appendChild(btn);
        });
        
        // Load sources and events after categories
        await loadSources();
        await loadAllEvents();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadSources() {
    try {
        const response = await fetch('/api/sources');
        const sourcesData = await response.json();
        
        const sourcesSection = document.getElementById('sourcesSection');
        const sourcesContent = document.getElementById('sourcesContent');
        
        sourcesContent.innerHTML = '';
        
        sourcesData.categories.forEach(categorySources => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'source-card';
            
            const categoryName = document.createElement('h3');
            categoryName.textContent = categorySources.category_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            categoryName.style.color = '#007bff';
            categoryName.style.marginBottom = '15px';
            categoryDiv.appendChild(categoryName);
            
            categorySources.sources.forEach(source => {
                const sourceDiv = document.createElement('div');
                sourceDiv.style.marginBottom = '15px';
                sourceDiv.style.padding = '10px';
                sourceDiv.style.border = '1px solid #444';
                sourceDiv.style.borderRadius = '6px';
                sourceDiv.style.backgroundColor = '#333';
                
                const sourceType = document.createElement('span');
                sourceType.className = `source-type ${source.type}`;
                sourceType.textContent = source.type.toUpperCase();
                sourceDiv.appendChild(sourceType);
                
                const sourceName = document.createElement('div');
                sourceName.className = 'source-name';
                sourceName.textContent = source.name;
                sourceDiv.appendChild(sourceName);
                
                const sourceDescription = document.createElement('div');
                sourceDescription.className = 'source-description';
                sourceDescription.textContent = source.description;
                sourceDiv.appendChild(sourceDescription);
                
                const sourceLink = document.createElement('a');
                sourceLink.className = 'source-link';
                sourceLink.href = source.url;
                sourceLink.target = '_blank';
                sourceLink.textContent = 'Visit Source';
                sourceDiv.appendChild(sourceLink);
                
                categoryDiv.appendChild(sourceDiv);
            });
            
            sourcesContent.appendChild(categoryDiv);
        });
        
        sourcesSection.style.display = 'block';
    } catch (error) {
        console.error('Error loading sources:', error);
    }
}

async function loadAllEvents() {
    try {
        const response = await fetch('/api/events');
        const eventsData = await response.json();
        
        const eventsSection = document.getElementById('eventsSection');
        const eventsContent = document.getElementById('eventsContent');
        
        eventsContent.innerHTML = '';
        
        // Группируем события по категориям
        const eventsByCategory = {};
        eventsData.events.forEach(event => {
            if (!eventsByCategory[event.category]) {
                eventsByCategory[event.category] = [];
            }
            eventsByCategory[event.category].push(event);
        });
        
        // Отображаем события по категориям
        Object.keys(eventsByCategory).forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'source-card';
            
            const categoryName = document.createElement('h3');
            categoryName.textContent = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            categoryName.style.color = '#28a745';
            categoryName.style.marginBottom = '15px';
            categoryDiv.appendChild(categoryName);
            
            eventsByCategory[category].forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event-card';
                eventDiv.style.marginBottom = '15px';
                
                const eventSource = document.createElement('span');
                eventSource.className = 'event-source';
                eventSource.textContent = event.source;
                eventDiv.appendChild(eventSource);
                
                const eventTitle = document.createElement('div');
                eventTitle.className = 'event-title';
                eventTitle.textContent = event.title;
                eventDiv.appendChild(eventTitle);
                
                const eventDate = document.createElement('div');
                eventDate.className = 'event-date';
                eventDate.textContent = `📅 ${event.date}`;
                eventDiv.appendChild(eventDate);
                
                const eventVenue = document.createElement('div');
                eventVenue.className = 'event-venue';
                eventVenue.textContent = `📍 ${event.venue}`;
                eventDiv.appendChild(eventVenue);
                
                if (event.description) {
                    const eventDescription = document.createElement('div');
                    eventDescription.className = 'event-description';
                    eventDescription.textContent = event.description;
                    eventDiv.appendChild(eventDescription);
                }
                
                const eventLink = document.createElement('a');
                eventLink.className = 'event-link';
                eventLink.href = event.url;
                eventLink.target = '_blank';
                eventLink.textContent = 'View Event';
                eventDiv.appendChild(eventLink);
                
                categoryDiv.appendChild(eventDiv);
            });
            
            eventsContent.appendChild(categoryDiv);
        });
        
        eventsSection.style.display = 'block';
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

function toggleCategory(categoryId, button) {
    if (selectedCategories.has(categoryId)) {
        selectedCategories.delete(categoryId);
        button.classList.remove('selected');
    } else {
        selectedCategories.add(categoryId);
        button.classList.add('selected');
    }
    
    updateApplyButton();
}

function updateApplyButton() {
    const applyBtn = document.getElementById('applyBtn');
    applyBtn.disabled = selectedCategories.size === 0;
}

async function createWeekPlan() {
    if (selectedCategories.size === 0) return;
    
    try {
        const response = await fetch('/api/week-plan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                city: 'Bangkok',
                selected_category_ids: Array.from(selectedCategories)
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayWeekPlan(result);
    } catch (error) {
        console.error('Error creating week plan:', error);
        alert('Error creating week plan. Please try again.');
    }
}

function displayWeekPlan(weekPlanData) {
    const weekEventsSection = document.getElementById('weekEventsSection');
    const weekEventsContent = document.getElementById('weekEventsContent');
    
    weekEventsContent.innerHTML = '';
    
    if (weekPlanData.week_events.days.length === 0) {
        weekEventsContent.innerHTML = '<p style="text-align: center; color: #ccc;">No events found for selected categories in the next 7 days.</p>';
    } else {
        weekPlanData.week_events.days.forEach(day => {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'day-events';
            
            // Заголовок дня
            const dayHeader = document.createElement('div');
            dayHeader.className = 'day-header';
            
            const dayDate = document.createElement('div');
            dayDate.className = 'day-date';
            dayDate.textContent = day.date;
            
            const dayName = document.createElement('div');
            dayName.className = 'day-name';
            dayName.textContent = day.day_name;
            
            dayHeader.appendChild(dayDate);
            dayHeader.appendChild(dayName);
            dayDiv.appendChild(dayHeader);
            
            // События дня
            const dayEventsList = document.createElement('div');
            dayEventsList.className = 'day-events-list';
            
            day.events.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event-card';
                
                const eventSource = document.createElement('span');
                eventSource.className = 'event-source';
                eventSource.textContent = event.source;
                eventDiv.appendChild(eventSource);
                
                const eventTitle = document.createElement('div');
                eventTitle.className = 'event-title';
                eventTitle.textContent = event.title;
                eventDiv.appendChild(eventTitle);
                
                const eventDate = document.createElement('div');
                eventDate.className = 'event-date';
                eventDate.textContent = `📅 ${event.date}`;
                eventDiv.appendChild(eventDate);
                
                const eventVenue = document.createElement('div');
                eventVenue.className = 'event-venue';
                eventVenue.textContent = `📍 ${event.venue}`;
                eventDiv.appendChild(eventVenue);
                
                if (event.description) {
                    const eventDescription = document.createElement('div');
                    eventDescription.className = 'event-description';
                    eventDescription.textContent = event.description;
                    eventDiv.appendChild(eventDescription);
                }
                
                const eventLink = document.createElement('a');
                eventLink.className = 'event-link';
                eventLink.href = event.url;
                eventLink.target = '_blank';
                eventLink.textContent = 'View Event';
                eventDiv.appendChild(eventLink);
                
                dayEventsList.appendChild(eventDiv);
            });
            
            dayDiv.appendChild(dayEventsList);
            weekEventsContent.appendChild(dayDiv);
        });
    }
    
    weekEventsSection.style.display = 'block';
    
    // Scroll to result
    weekEventsSection.scrollIntoView({ behavior: 'smooth' });
}

// Event listeners
document.getElementById('applyBtn').onclick = createWeekPlan;

// Load categories when page loads
document.addEventListener('DOMContentLoaded', loadCategories);
