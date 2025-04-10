document.addEventListener('DOMContentLoaded', () => {
    const sliderWrapper = document.querySelector('.slider-wrapper');
    const slides = document.querySelectorAll('.slider-slide');
    const prevArrow = document.querySelector('.prev-arrow');
    const nextArrow = document.querySelector('.next-arrow');
    const dotsContainer = document.querySelector('.slider-dots');
    let currentIndex = 0;

    // Create pagination dots
    slides.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.classList.add('slider-dot');
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });

    const dots = document.querySelectorAll('.slider-dot');

    // Function to go to a specific slide
    function goToSlide(index) {
        if (index < 0) index = slides.length - 1;
        if (index >= slides.length) index = 0;
        currentIndex = index;
        sliderWrapper.style.transform = `translateX(-${currentIndex * 100}%)`;
        updateDots();
    }

    // Update active dot
    function updateDots() {
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });
    }

    // Event listeners for arrows
    prevArrow.addEventListener('click', () => goToSlide(currentIndex - 1));
    nextArrow.addEventListener('click', () => goToSlide(currentIndex + 1));

    // Optional: Auto-slide every 5 seconds
    setInterval(() => {
        goToSlide(currentIndex + 1);
    }, 5000);
});
