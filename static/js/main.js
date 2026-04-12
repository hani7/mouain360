// =============================================
// MOUIN 360 — Main JavaScript
// =============================================

// ===== PARTICLE BACKGROUND =====
(function () {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < 55; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            r: Math.random() * 1.5 + 0.3,
            dx: (Math.random() - 0.5) * 0.4,
            dy: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.5 + 0.1
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(1,238,254,${p.alpha})`;
            ctx.fill();
            p.x += p.dx; p.y += p.dy;
            if (p.x < 0 || p.x > canvas.width)  p.dx *= -1;
            if (p.y < 0 || p.y > canvas.height)  p.dy *= -1;
        });
        // Draw connecting lines
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dist = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(1,238,254,${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();

// ===== PAGE TRANSITION FADE-IN =====
document.body.style.opacity = '0';
document.body.style.transition = 'opacity 0.35s ease';
window.addEventListener('load', () => { document.body.style.opacity = '1'; });

document.querySelectorAll('a[href]').forEach(a => {
    if (a.href && !a.href.startsWith('#') && a.target !== '_blank'
        && a.getAttribute('href') && !a.getAttribute('href').startsWith('#')) {
        a.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href && !href.startsWith('javascript') && !href.startsWith('mailto')) {
                e.preventDefault();
                document.body.style.opacity = '0';
                setTimeout(() => { window.location.href = href; }, 300);
            }
        });
    }
});

// ===== AUTO-DISMISS TOASTS =====
document.querySelectorAll('.m360-toast').forEach(t => {
    setTimeout(() => {
        t.style.animation = 'toastOut 0.4s ease forwards';
        setTimeout(() => t.remove(), 400);
    }, 4000);
});
