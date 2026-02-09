/* ============================================
   JAVASCRIPT - Interactions et Animations
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // === NAVBAR DYNAMICS ===
    const navbar = document.getElementById('mainNavbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // === AOS (Animate On Scroll) Initialization ===
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            easing: 'ease-in-out',
            once: true,
            offset: 100
        });
    }

    // === Smooth Scroll for Anchor Links ===
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                const target = document.querySelector(href);
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // === Active Nav Link ===
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    window.addEventListener('scroll', function() {
        let current = '';
        navLinks.forEach(link => {
            const section = document.querySelector(link.getAttribute('href'));
            if (section && section.offsetTop <= window.scrollY + 100) {
                current = link.getAttribute('href');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === current) {
                link.classList.add('active');
            }
        });
    });

    // === Scroll To Top Button ===
    const scrollBtn = document.querySelector('.scroll-to-top');
    if (scrollBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                scrollBtn.classList.add('show');
            } else {
                scrollBtn.classList.remove('show');
            }
        });

        scrollBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // === Form Handling ===
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            
            // Here you would typically send this to a backend
            // For now, we'll show a success message
            showSuccessMessage('Merci ! Votre message a été envoyé avec succès.');
            
            // Reset form
            this.reset();
        });
    }

    // === Success Message ===
    function showSuccessMessage(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.insertBefore(alert, document.body.firstChild);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    // === Typewriter Effect for Hero Text ===
    const heroTitle = document.querySelector('.display-3');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.textContent = '';
        let index = 0;
        
        function typeWriter() {
            if (index < text.length) {
                heroTitle.textContent += text.charAt(index);
                index++;
                setTimeout(typeWriter, 50);
            }
        }
        typeWriter();
    }

    // === Counter Animation ===
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length > 0) {
        window.addEventListener('scroll', animateCounters);
        
        function animateCounters() {
            statNumbers.forEach(stat => {
                const value = parseInt(stat.textContent);
                if (isNaN(value)) return;
                
                let current = 0;
                const increment = value / 50;
                
                const interval = setInterval(() => {
                    current += increment;
                    if (current >= value) {
                        stat.textContent = value + (stat.textContent.includes('%') ? '%' : '+');
                        clearInterval(interval);
                    } else {
                        stat.textContent = Math.floor(current) + (stat.textContent.includes('%') ? '%' : '+');
                    }
                }, 30);
            });
            
            window.removeEventListener('scroll', animateCounters);
        }
    }

    // === Fade In Animation on Scroll ===
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .expertise-card, .project-card').forEach(el => {
        observer.observe(el);
    });

    // === Mobile Menu Close on Link Click ===
    const navbarToggle = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggle) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navbarToggle.click();
            });
        });
    }

    // === Parallax Effect ===
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        const orbs = document.querySelectorAll('.gradient-orb');
        
        orbs.forEach((orb, index) => {
            orb.style.transform = `translate(0, ${scrollPosition * 0.5 * (index + 1)}px)`;
        });
    });

    console.log('✅ Portfolio initialized successfully!');
});
// --- Navbar dynamique au scroll ---
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('mainNavbar');
  navbar.classList.toggle('scrolled', window.scrollY > 50);
});

// --- AOS init ---
AOS.init({
  duration: 1000,
  once: true,
  easing: 'ease-in-out',
});

// --- Animation des chiffres statistiques ---
document.addEventListener('DOMContentLoaded', () => {
  const counters = document.querySelectorAll('.stat-number');
  counters.forEach(counter => {
    const updateCount = () => {
      const target = +counter.innerText.replace(/\D/g, '');
      const count = +counter.getAttribute('data-count') || 0;
      const inc = Math.max(1, target / 80);
      if (count < target) {
        counter.setAttribute('data-count', count + inc);
        counter.innerText = Math.floor(count + inc) + '+';
        setTimeout(updateCount, 40);
      } else {
        counter.innerText = target + '+';
      }
    };
    updateCount();
  });
});
