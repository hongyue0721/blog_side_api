class SnowEffect {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.flakes = [];
        this.isRunning = false;
        this.animationFrame = null;
    }

    init() {
        // Create canvas if not exists
        if (!document.getElementById('snow-canvas')) {
            this.canvas = document.createElement('canvas');
            this.canvas.id = 'snow-canvas';
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.pointerEvents = 'none';
            this.canvas.style.zIndex = '9999';
            document.body.appendChild(this.canvas);
            
            this.ctx = this.canvas.getContext('2d');
            
            window.addEventListener('resize', () => this.resize());
            this.resize();
        }
    }

    resize() {
        if (this.canvas) {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        }
    }

    createFlakes() {
        const count = 50; // Number of flakes
        this.flakes = [];
        for (let i = 0; i < count; i++) {
            this.flakes.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                r: Math.random() * 3 + 1, // Radius
                d: Math.random() * count, // Density
                a: Math.random() // Alpha
            });
        }
    }

    draw() {
        if (!this.isRunning) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        this.ctx.beginPath();

        for (let i = 0; i < this.flakes.length; i++) {
            const f = this.flakes[i];
            this.ctx.moveTo(f.x, f.y);
            this.ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2, true);
        }

        this.ctx.fill();
        this.move();
        this.animationFrame = requestAnimationFrame(() => this.draw());
    }

    move() {
        for (let i = 0; i < this.flakes.length; i++) {
            const f = this.flakes[i];
            f.y += Math.pow(f.d, 0.5) * 0.5 + 1; // Speed
            f.x += Math.sin(i + f.d) * 0.5; // Sway

            // Reset if out of view
            if (f.y > this.canvas.height) {
                this.flakes[i] = {
                    x: Math.random() * this.canvas.width,
                    y: 0,
                    r: f.r,
                    d: f.d,
                    a: f.a
                };
            }
        }
    }

    start() {
        if (this.isRunning) return;
        this.init();
        this.createFlakes();
        this.isRunning = true;
        this.draw();
    }

    stop() {
        this.isRunning = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
}

window.snowEffect = new SnowEffect();
