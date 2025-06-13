// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Add loading states to cards
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            // Add loading state
            this.classList.add('opacity-75');
            // Remove loading state after animation
            setTimeout(() => {
                this.classList.remove('opacity-75');
            }, 200);
        });
    });
}); 