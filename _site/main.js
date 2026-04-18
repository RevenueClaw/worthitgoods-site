// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchProducts');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const productCards = document.querySelectorAll('.product-card');
            
            productCards.forEach(card => {
                const productName = card.querySelector('h3').textContent.toLowerCase();
                card.style.display = productName.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }
});

// Review form submission
document.addEventListener('DOMContentLoaded', function() {
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('reviewName').value;
            const email = document.getElementById('reviewEmail').value;
            const rating = document.getElementById('reviewRating').value;
            const comment = document.getElementById('reviewComment').value;
            
            if (name && email && rating && comment) {
                // Create review element
                const reviewContainer = document.querySelector('.reviews-container');
                if (reviewContainer) {
                    const newReview = document.createElement('div');
                    newReview.className = 'review';
                    newReview.innerHTML = `
                        <p>⭐ ${rating}/5 - "${comment}"</p>
                        <p class="author">— ${name}</p>
                    `;
                    reviewContainer.appendChild(newReview);
                }
                
                // Reset form
                reviewForm.reset();
                
                // Show success message
                const successMsg = document.createElement('div');
                successMsg.style.color = '#28a745';
                successMsg.style.marginTop = '1rem';
                successMsg.textContent = 'Thank you! Your review has been submitted.';
                reviewForm.appendChild(successMsg);
                
                setTimeout(() => {
                    successMsg.remove();
                }, 3000);
            }
        });
    }
});

// Trust badges interaction
document.addEventListener('DOMContentLoaded', function() {
    const trustBadges = document.querySelectorAll('.trust-badge');
    trustBadges.forEach(badge => {
        badge.addEventListener('click', function() {
            const badgeInfo = this.getAttribute('data-info');
            alert(badgeInfo);
        });
    });
});