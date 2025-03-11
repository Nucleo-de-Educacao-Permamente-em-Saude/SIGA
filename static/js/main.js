// Initialize Feather icons
document.addEventListener('DOMContentLoaded', function() {
    feather.replace();
});

// Enable Bootstrap tooltips
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        let alerts = document.getElementsByClassName('alert');
        for(let alert of alerts) {
            alert.style.display = 'none';
        }
    }, 5000);
});
