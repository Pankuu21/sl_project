// Fetch and display analytics data

async function loadAnalytics() {
    try {
        // Fetch crop distribution
        const cropDistResponse = await fetch('/api/analytics/crop-distribution');
        const cropDistData = await cropDistResponse.json();
        
        // Fetch nutrient stats
        const nutrientResponse = await fetch('/api/analytics/nutrient-stats');
        const nutrientData = await nutrientResponse.json();
        
        // Create charts
        createCropDistributionChart(cropDistData);
        createNutrientChart(nutrientData);
        createTempRainfallChart(nutrientData);
        createPHChart(nutrientData);
        
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

function createCropDistributionChart(data) {
    if (!data || data.length === 0) {
        document.getElementById('crop-distribution-chart').innerHTML = 
            '<p class="text-center text-gray-500 py-8">No prediction data available</p>';
        return;
    }
    
    const trace = {
        labels: data.map(d => d.crop),
        values: data.map(d => d.count),
        type: 'pie',
        marker: {
            colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
        }
    };
    
    const layout = {
        height: 400,
        margin: { t: 20, b: 20, l: 20, r: 20 }
    };
    
    Plotly.newPlot('crop-distribution-chart', [trace], layout, {responsive: true});
}

function createNutrientChart(data) {
    if (!data || data.length === 0) {
        document.getElementById('nutrient-chart').innerHTML = 
            '<p class="text-center text-gray-500 py-8">No data available</p>';
        return;
    }
    
    const crops = data.map(d => d.crop);
    
    const traceN = {
        x: crops,
        y: data.map(d => d.avg_n),
        name: 'Nitrogen (N)',
        type: 'bar',
        marker: { color: '#10b981' }
    };
    
    const traceP = {
        x: crops,
        y: data.map(d => d.avg_p),
        name: 'Phosphorus (P)',
        type: 'bar',
        marker: { color: '#3b82f6' }
    };
    
    const traceK = {
        x: crops,
        y: data.map(d => d.avg_k),
        name: 'Potassium (K)',
        type: 'bar',
        marker: { color: '#f59e0b' }
    };
    
    const layout = {
        barmode: 'group',
        height: 400,
        xaxis: { title: 'Crop' },
        yaxis: { title: 'Average Value' },
        margin: { t: 20, b: 60, l: 60, r: 20 }
    };
    
    Plotly.newPlot('nutrient-chart', [traceN, traceP, traceK], layout, {responsive: true});
}

function createTempRainfallChart(data) {
    if (!data || data.length === 0) {
        document.getElementById('temp-rainfall-chart').innerHTML = 
            '<p class="text-center text-gray-500 py-8">No data available</p>';
        return;
    }
    
    const trace = {
        x: data.map(d => d.avg_temp),
        y: data.map(d => d.avg_rainfall),
        mode: 'markers+text',
        type: 'scatter',
        text: data.map(d => d.crop),
        textposition: 'top center',
        marker: {
            size: 12,
            color: data.map((d, i) => i),
            colorscale: 'Viridis'
        }
    };
    
    const layout = {
        height: 400,
        xaxis: { title: 'Average Temperature (°C)' },
        yaxis: { title: 'Average Rainfall (mm)' },
        margin: { t: 20, b: 60, l: 60, r: 20 }
    };
    
    Plotly.newPlot('temp-rainfall-chart', [trace], layout, {responsive: true});
}

function createPHChart(data) {
    if (!data || data.length === 0) {
        document.getElementById('ph-chart').innerHTML = 
            '<p class="text-center text-gray-500 py-8">No data available</p>';
        return;
    }
    
    const trace = {
        x: data.map(d => d.crop),
        y: data.map(d => d.avg_ph),
        type: 'bar',
        marker: {
            color: data.map(d => d.avg_ph),
            colorscale: 'Portland',
            showscale: true
        }
    };
    
    const layout = {
        height: 400,
        xaxis: { title: 'Crop' },
        yaxis: { title: 'Average pH Level', range: [0, 14] },
        margin: { t: 20, b: 60, l: 60, r: 20 }
    };
    
    Plotly.newPlot('ph-chart', [trace], layout, {responsive: true});
}

// Load analytics on page load
if (document.getElementById('crop-distribution-chart')) {
    loadAnalytics();
}
