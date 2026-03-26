// Navigasi Halaman Sederhana
function showPage(pageId) {
    document.getElementById('dashboard-page').style.display = pageId === 'dashboard' ? 'block' : 'none';
    document.getElementById('products-page').style.display = pageId === 'products' ? 'block' : 'none';
    
    // Update active class sidebar
    const navItems = document.querySelectorAll('nav li');
    navItems.forEach(li => li.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

// Render Revenue Chart (Line)
const ctxRev = document.getElementById('revenueChart').getContext('2d');
new Chart(ctxRev, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'],
        datasets: [{
            label: 'Revenue 2025',
            data: [520, 560, 490, 570, 520, 540, 550, 565, 570, 555, 580, 620],
            borderColor: '#ED1C24',
            backgroundColor: 'rgba(237, 28, 36, 0.1)',
            fill: true,
            tension: 0.4
        }]
    }
});

// Render Branch Chart (Horizontal Bar)
const ctxBranch = document.getElementById('branchChart').getContext('2d');
new Chart(ctxBranch, {
    type: 'bar',
    indexAxis: 'y',
    data: {
        labels: ['MANADO', 'PALU', 'MAKASSAR', 'KENDARI', 'PAREPARE'],
        datasets: [{
            label: 'Total Revenue',
            data: [1200, 950, 1500, 800, 700],
            backgroundColor: '#ED1C24'
        }]
    }
});