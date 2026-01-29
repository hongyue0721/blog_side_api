class MusicPlayer {
    constructor() {
        this.audio = new Audio();
        this.isPlaying = false;
        this.playlist = [];
        this.container = null;
        this.toggleBtn = null;
        this.volumeContainer = null;
        this.volumeSlider = null;
    }

    init(musicUrl) {
        if (!musicUrl) return;
        
        this.playlist = [musicUrl];
        this.audio.src = musicUrl;
        this.audio.loop = true;
        this.audio.volume = 0.5;
        
        this.createUI();
        
        // Try autoplay
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updateIcon();
        }).catch(() => {
            console.log("Autoplay blocked");
            this.isPlaying = false;
            this.updateIcon();
            const startPlay = () => {
                this.play();
                document.removeEventListener('click', startPlay);
            };
            document.addEventListener('click', startPlay);
        });
    }

    createUI() {
        if (document.getElementById('music-player-container')) return;

        // Main Container
        this.container = document.createElement('div');
        this.container.id = 'music-player-container';
        Object.assign(this.container.style, {
            position: 'fixed',
            top: '80px', // Below theme/snow toggles
            right: '24px',
            zIndex: '9999',
            background: 'var(--card, rgba(255, 255, 255, 0.8))',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            padding: '0 4px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            transition: 'width 0.3s ease, box-shadow 0.3s ease',
            overflow: 'hidden',
            width: '40px', // Collapsed state
            border: '1px solid var(--border, rgba(229, 231, 235, 0.5))'
        });

        // Play/Pause Button (Icon)
        this.toggleBtn = document.createElement('div');
        Object.assign(this.toggleBtn.style, {
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '18px',
            flexShrink: 0,
            userSelect: 'none'
        });
        
        // Volume Control Container
        this.volumeContainer = document.createElement('div');
        Object.assign(this.volumeContainer.style, {
            width: '0',
            opacity: '0',
            overflow: 'hidden',
            transition: 'width 0.3s ease, opacity 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            marginLeft: '0'
        });

        // Slider
        this.volumeSlider = document.createElement('input');
        this.volumeSlider.type = 'range';
        this.volumeSlider.min = 0;
        this.volumeSlider.max = 1;
        this.volumeSlider.step = 0.05;
        this.volumeSlider.value = this.audio.volume;
        Object.assign(this.volumeSlider.style, {
            width: '80px',
            margin: '0 10px',
            cursor: 'pointer',
            height: '4px'
        });

        this.volumeContainer.appendChild(this.volumeSlider);
        this.container.appendChild(this.toggleBtn);
        this.container.appendChild(this.volumeContainer);
        document.body.appendChild(this.container);

        // Event Listeners
        
        // 1. Toggle Play/Pause
        this.toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // 2. Expand/Collapse (Hover for Desktop, Click for Mobile)
        const expand = () => {
            this.container.style.width = '150px';
            this.volumeContainer.style.width = '100px';
            this.volumeContainer.style.opacity = '1';
        };
        
        const collapse = () => {
            this.container.style.width = '40px';
            this.volumeContainer.style.width = '0';
            this.volumeContainer.style.opacity = '0';
        };

        this.container.addEventListener('mouseenter', expand);
        this.container.addEventListener('mouseleave', collapse);

        // 3. Volume Change
        this.volumeSlider.addEventListener('input', (e) => {
            this.audio.volume = e.target.value;
        });
        this.volumeSlider.addEventListener('click', (e) => e.stopPropagation());

        this.updateIcon();
    }

    updateIcon() {
        if (this.toggleBtn) {
            this.toggleBtn.innerHTML = this.isPlaying ? '🎵' : '🔇';
            if (this.isPlaying) {
                this.container.style.boxShadow = '0 0 15px var(--primary, #2563eb)';
                this.container.style.borderColor = 'var(--primary, #2563eb)';
            } else {
                this.container.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
                this.container.style.borderColor = 'var(--border, rgba(229, 231, 235, 0.5))';
            }
        }
    }

    toggle() {
        if (this.isPlaying) this.pause();
        else this.play();
    }

    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updateIcon();
        }).catch(e => console.error(e));
    }

    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.updateIcon();
    }
}

window.musicPlayer = new MusicPlayer();
