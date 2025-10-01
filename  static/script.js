// NASA Space Explorer JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Load NASA data when page loads
    loadAstronomyPictureOfTheDay();
    loadMarsWeather();
    loadNearEarthObjects();
    loadLatestNews();
});

// Load Astronomy Picture of the Day for Featured Content (Left Column)
async function loadAstronomyPictureOfTheDay() {
    try {
        const response = await fetch('/api/apod');
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // Update featured content with APOD (Left Column)
            const featuredImg = document.getElementById('featured-image');
            const featuredLoading = document.querySelector('#featured-card .loading');
            if (featuredLoading) {
                featuredLoading.style.display = 'none';
            }
            
            if (data.media_type === 'image') {
                featuredImg.src = data.hdurl || data.url;
                featuredImg.style.display = 'block';
            } else if (data.media_type === 'video') {
                featuredImg.style.display = 'none';
                const videoDiv = document.createElement('div');
                videoDiv.innerHTML = `<iframe width="100%" height="315" src="${data.url}" frameborder="0" allowfullscreen></iframe>`;
                const featuredCard = document.getElementById('featured-card');
                // Remove any existing iframe or video div first
                const existingVideoDiv = featuredCard.querySelector('div');
                if (existingVideoDiv) {
                    featuredCard.removeChild(existingVideoDiv);
                }
                featuredCard.appendChild(videoDiv);
            }
            
            document.getElementById('featured-title').textContent = data.title;
            document.getElementById('featured-description').textContent = data.explanation.substring(0, 200) + '...';
        } else {
            console.error('Failed to load APOD:', result.error);
            updateLoadingError('#featured-card', 'Failed to load Featured Content');
        }
    } catch (error) {
        console.error('Error loading APOD:', error);
        updateLoadingError('#featured-card', 'Error loading Featured Content');
    }
}

// Load Mars Weather Data (unchanged)
async function loadMarsWeather() {
    try {
        const response = await fetch('/api/mars-weather');
        const result = await response.json();
        
        if (result.success) {
            // Mars weather API might not have current data, so provide fallback
            document.getElementById('mars-weather').innerHTML = `
                <strong>Latest Mars Data:</strong><br>
                Weather monitoring from NASA's InSight mission provides atmospheric data from Mars.
                <br><br>
                <em>Temperature:</em> -80°C to -10°C<br>
                <em>Pressure:</em> Variable<br>
                <em>Status:</em> Monitoring
            `;
        } else {
            document.getElementById('mars-weather').innerHTML = `
                <strong>Mars Weather:</strong><br>
                Data temporarily unavailable. Mars experiences extreme temperature variations and seasonal changes.
            `;
        }
    } catch (error) {
        console.error('Error loading Mars weather:', error);
        document.getElementById('mars-weather').innerHTML = `
            <strong>Mars Weather:</strong><br>
            Monitoring atmospheric conditions on Mars through various NASA missions.
        `;
    }
}

// Load Near Earth Objects (unchanged)
async function loadNearEarthObjects() {
    try {
        const response = await fetch('/api/neo');
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            const today = new Date().toISOString().split('T')[0];
            const todayObjects = data.near_earth_objects[today] || [];
            
            document.getElementById('neo-count').innerHTML = `
                <strong>Today's NEOs:</strong><br>
                ${todayObjects.length} objects detected<br>
                <br>
                <em>Closest approach:</em><br>
                ${todayObjects.length > 0 ? 
                    `${todayObjects[0].name}<br>
                     ${Math.round(parseFloat(todayObjects[0].close_approach_data[0].miss_distance.kilometers))} km` 
                    : 'No close approaches today'}
            `;
        } else {
            document.getElementById('neo-count').innerHTML = `
                <strong>Near Earth Objects:</strong><br>
                NASA tracks thousands of asteroids and comets that pass close to Earth.
            `;
        }
    } catch (error) {
        console.error('Error loading NEO data:', error);
        document.getElementById('neo-count').innerHTML = `
            <strong>Near Earth Objects:</strong><br>
            Continuous monitoring of space objects near Earth's orbit.
        `;
    }
}

// Load Latest News (Right Column) from NASA RSS feed
async function loadLatestNews() {
    const newsContainer = document.getElementById('latest-news');
    if (!newsContainer) return;
    newsContainer.innerHTML = '<p>Loading latest news...</p>';
    try {
        // Using NASA RSS feed converted to JSON via rss2json API or similar
        // Since no backend proxy is specified, we'll use a public RSS to JSON service
        const rssUrl = encodeURIComponent('https://www.nasa.gov/rss/dyn/breaking_news.rss');
        const apiUrl = `https://api.rss2json.com/v1/api.json?rss_url=${rssUrl}`;
        
        const response = await fetch(apiUrl);
        const result = await response.json();
        
        if (result.status === 'ok' && result.items && result.items.length > 0) {
            newsContainer.innerHTML = '';
            const maxItems = 5;
            result.items.slice(0, maxItems).forEach(item => {
                const newsItem = document.createElement('div');
                newsItem.classList.add('news-item');
                newsItem.innerHTML = `
                    <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                    <p>${item.pubDate ? new Date(item.pubDate).toLocaleDateString() : ''}</p>
                `;
                newsContainer.appendChild(newsItem);
            });
        } else {
            newsContainer.innerHTML = '<p>No news available at the moment.</p>';
        }
    } catch (error) {
        console.error('Error loading latest news:', error);
        newsContainer.innerHTML = '<p>Failed to load latest news.</p>';
    }
}

// Helper function to update loading errors
function updateLoadingError(selector, message) {
    const card = document.querySelector(selector);
    const loading = card.querySelector('.loading');
    if (loading) {
        loading.textContent = message;
        loading.style.color = '#666';
    }
}

// Search functionality (unchanged)
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('.nav-input, .search-box');
    
    searchInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
    });
    
    // Search icon click
    const searchIcon = document.querySelector('.search-icon');
    if (searchIcon) {
        searchIcon.addEventListener('click', function() {
            const searchBox = document.querySelector('.search-box');
            if (searchBox) performSearch(searchBox.value);
        });
    }
});

// Search function (unchanged)
function performSearch(query) {
    if (query.trim()) {
        console.log('Searching for:', query);
        // Here you could implement actual search functionality
        // For now, we'll just log the search query
        alert(`Search functionality would search for: "${query}"`);
    }
}

// Auto-refresh data every 30 minutes (unchanged)
setInterval(() => {
    loadAstronomyPictureOfTheDay();
    loadMarsWeather();
    loadNearEarthObjects();
    loadLatestNews();
}, 30 * 60 * 1000);

