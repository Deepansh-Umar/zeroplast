// ==========================
// Dashboard JS (for index.html)
// ==========================

// Animate progress bar
window.addEventListener('load', () => {
    const progress = document.querySelector('.progress-bar div');
    if (progress) {
        const value = parseInt(progress.parentElement.previousElementSibling.innerText.replace(/\D/g,''));
        progress.style.width = value + '%';
    }
});

// Search logs
const searchBox = document.getElementById('searchBox');
if(searchBox){
    searchBox.addEventListener('input', function() {
        const term = this.value.toLowerCase();
        document.querySelectorAll('.logCard').forEach(card => {
            const text = card.querySelector('.logInfo').innerText.toLowerCase();
            card.style.display = text.includes(term) ? 'flex' : 'none';
        });
    });
}

// Delete log function
function deleteLog(id){
    // Example using fetch API
    fetch(`/delete/${id}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            document.querySelector(`.logCard button[onclick="deleteLog(${id})"]`).parentElement.remove();
        } else {
            alert('Error deleting log!');
        }
    });
}

// Chart.js setup
if(document.getElementById('donationChart')){
    const ctx = document.getElementById('donationChart').getContext('2d');
    const donationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chart_labels, // from Flask render_template
            datasets: [{
                label: 'Donations (kg)',
                data: chart_data, // from Flask
                backgroundColor: 'rgba(45,156,219,0.2)',
                borderColor: '#2d9cdb',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index' }
            },
            scales: { y: { beginAtZero: true } }
        }
    });
}
