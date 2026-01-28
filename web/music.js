class MusicPlayer {
    constructor() {
        this.audio = new Audio();
        this.isPlaying = false;
        this.playlist = [];
        this.currentIndex = 0;
        this.container = null;
        this.toggleBtn = null;
    }

    init(musicUrl) {
        if (!musicUrl) return;
        
        this.playlist = [musicUrl];
        this.audio.src = musicUrl;
        this.audio.loop = true;
        
        this.createUI();
        
        // Auto play might be blocked by browser policy
        // We'll try to play on first interaction if autoplay fails
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updateIcon();
        }).catch(() => {
            console.log("Autoplay blocked, waiting for interaction");
            this.isPlaying = false;
            this.updateIcon();
            
            // Add one-time click listener to document to start playing
            const startPlay = () => {
                this.play();
                document.removeEventListener('click', startPlay);
            };
            document.addEventListener('click', startPlay);
        });
    }

    createUI() {
        if (document.getElementById('music-player-container')) return;

        this.container = document.createElement('div');
        this.container.id = 'music-player-container';
        this.container.style.position = 'fixed';
        this.container.style.bottom = '20px';
        this.container.style.right = '20px';
        this.container.style.zIndex = '10000';
        this.container.style.background = 'rgba(255, 255, 255, 0.8)';
        this.container.style.backdropFilter = 'blur(10px)';
        this.container.style.borderRadius = '50%';
        this.container.style.width = '40px';
        this.container.style.height = '40px';
        this.container.style.display = 'flex';
        this.container.style.alignItems = 'center';
        this.container.style.justifyContent = 'center';
        this.container.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        this.container.style.cursor = 'pointer';
        this.container.style.transition = 'transform 0.3s ease';

        this.toggleBtn = document.createElement('div');
        this.toggleBtn.style.fontSize = '20px';
        
        this.container.appendChild(this.toggleBtn);
        document.body.appendChild(this.container);

        this.container.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering document click
            this.toggle();
        });
        
        this.container.addEventListener('mouseenter', () => {
            this.container.style.transform = 'scale(1.1)';
        });
        
        this.container.addEventListener('mouseleave', () => {
            this.container.style.transform = 'scale(1)';
        });

        this.updateIcon();
    }

    updateIcon() {
        if (this.toggleBtn) {
            this.toggleBtn.innerHTML = this.isPlaying ? '🔊' : '🔇';
            // Add animation class if playing
            if (this.isPlaying) {
                this.container.style.animation = 'pulse 2s infinite';
            } else {
                this.container.style.animation = 'none';
            }
        }
    }

    toggle() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updateIcon();
        }).catch(e => console.error("Play failed:", e));
    }

    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.updateIcon();
    }
}

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }
        70% { box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
    }
`;
document.head.appendChild(style);

window.musicPlayer = new MusicPlayer();
