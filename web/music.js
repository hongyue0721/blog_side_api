class MusicPlayer {
    constructor() {
        this.audio = new Audio();
        this.isPlaying = false;
        this.playlist = [];
        this.container = null;
        this.toggleBtn = null;
        this.volumeContainer = null;
        this.volumeSlider = null;
        this.isExpanded = false;
    }

    init(musicUrl, mountPoint) {
        if (!musicUrl) return;
        
        this.playlist = [musicUrl];
        this.audio.src = musicUrl;
        this.audio.loop = true;
        this.audio.volume = 0.5;
        
        this.createUI(mountPoint);
        
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

    createUI(mountPoint) {
        if (document.getElementById('music-player-container')) return;

        // Main Container (Embedded in menu)
        this.container = document.createElement('div');
        this.container.id = 'music-player-container';
        this.container.className = 'menu-item';
        Object.assign(this.container.style, {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 12px',
            cursor: 'default'
        });

        // Left side: Icon + Text
        const leftSide = document.createElement('div');
        leftSide.style.display = 'flex';
        leftSide.style.alignItems = 'center';
        leftSide.style.gap = '12px';

        // Play/Pause Button (Icon)
        this.toggleBtn = document.createElement('span');
        this.toggleBtn.className = 'menu-icon';
        this.toggleBtn.style.cursor = 'pointer';
        this.toggleBtn.innerHTML = '🔇';
        
        const label = document.createElement('span');
        label.textContent = '背景音乐';

        leftSide.appendChild(this.toggleBtn);
        leftSide.appendChild(label);

        // Right side: Volume Slider
        this.volumeSlider = document.createElement('input');
        this.volumeSlider.type = 'range';
        this.volumeSlider.min = 0;
        this.volumeSlider.max = 1;
        this.volumeSlider.step = 0.05;
        this.volumeSlider.value = this.audio.volume;
        Object.assign(this.volumeSlider.style, {
            width: '60px',
            height: '4px',
            cursor: 'pointer'
        });

        this.container.appendChild(leftSide);
        this.container.appendChild(this.volumeSlider);

        if (mountPoint) {
            mountPoint.appendChild(this.container);
        } else {
            document.body.appendChild(this.container);
        }

        // --- Interaction Logic ---

        // Toggle Button Click
        this.toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // Volume Slider
        this.volumeSlider.addEventListener('input', (e) => {
            this.audio.volume = e.target.value;
        });
        
        // Prevent menu closing when interacting with slider
        this.volumeSlider.addEventListener('click', (e) => e.stopPropagation());

        this.updateIcon();
    }

    updateIcon() {
        if (this.toggleBtn) {
            this.toggleBtn.innerHTML = this.isPlaying ? '🎵' : '🔇';
            this.toggleBtn.style.opacity = this.isPlaying ? '1' : '0.5';
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
