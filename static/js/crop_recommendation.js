document.getElementById('crop-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Get form data
    const formData = {
        N: parseFloat(document.getElementById('nitrogen').value),
        P: parseFloat(document.getElementById('phosphorus').value),
        K: parseFloat(document.getElementById('potassium').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        humidity: parseFloat(document.getElementById('humidity').value),
        ph: parseFloat(document.getElementById('ph').value),
        rainfall: parseFloat(document.getElementById('rainfall').value)
    };
    
    // Show loading state
    document.getElementById('initial-state').classList.add('hidden');
    document.getElementById('result').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        // Make API call
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        // Hide loading
        document.getElementById('loading').classList.add('hidden');
        
        if (data.success) {
            // Display result
            document.getElementById('crop-name').textContent = data.crop.toUpperCase();
            document.getElementById('confidence').textContent = data.confidence;
            document.getElementById('season').textContent = data.season || 'N/A';
            document.getElementById('duration').textContent = data.duration || 'N/A';
            document.getElementById('tips').textContent = data.tips || 'No additional information';
            
            // Set crop image
            if (data.image) {
                document.getElementById('crop-image').src = data.image;
            }
            
            document.getElementById('result').classList.remove('hidden');
        } else {
            // Show error
            document.getElementById('error-message').textContent = data.error || 'Prediction failed';
            document.getElementById('error').classList.remove('hidden');
        }
    } catch (error) {
        // Hide loading
        document.getElementById('loading').classList.add('hidden');
        
        // Show error
        document.getElementById('error-message').textContent = 'Network error: ' + error.message;
        document.getElementById('error').classList.remove('hidden');
    }
});
