document.getElementById('scrape-news-btn').addEventListener('click', async function() {
    const btn = this;
    const text = document.getElementById('scrape-text');
    const loading = document.getElementById('scrape-loading');
    
    // Disable button and show loading
    btn.disabled = true;
    text.classList.add('hidden');
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/scrape/news', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            window.location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error scraping news: ' + error.message);
    } finally {
        // Re-enable button
        btn.disabled = false;
        text.classList.remove('hidden');
        loading.classList.add('hidden');
    }
});
