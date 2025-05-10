let tg = window.Telegram.WebApp;

// Hamburger menu (Bootstrap bilan)
const hamburger = document.getElementById('hamburger-menu');
const sidebar = document.getElementById('sidebar');
const overlay = document.querySelector('.sidebar-overlay');

function toggleSidebar(e) {
    if (e) e.preventDefault();
    sidebar.classList.toggle('open');
    document.body.classList.toggle('menu-open');
    overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
}

if (hamburger) {
    hamburger.onclick = toggleSidebar;
    hamburger.ontouchstart = function(e) {
        // Prevent double firing on touch devices
        e.preventDefault();
        toggleSidebar(e);
    };
}
if (overlay) {
    overlay.onclick = () => {
        sidebar.classList.remove('open');
        document.body.classList.remove('menu-open');
        overlay.style.display = 'none';
    };
}

// Qidiruv
const searchInput = document.getElementById('search-input');
let allTopics = [];

// Error handling
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.insertBefore(errorDiv, document.body.firstChild);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Loading state
function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Yuklanmoqda...';
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.textContent = originalText;
}

// API calls with error handling
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': window.API_KEY,
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Server xatolik');
        }
        
        return await response.json();
    } catch (error) {
        showError(error.message);
        throw error;
    }
}

// Load topics with error handling
async function loadTopics() {
    try {
        const topics = await apiCall('/api/topics');
        allTopics = topics;
        renderTopics(allTopics);
        document.querySelector('.loader').style.display = 'none';
    } catch (error) {
        document.querySelector('.loader').innerHTML = `
            <div class="text-danger">
                <i class="bi bi-exclamation-triangle"></i>
                Mavzular yuklanmadi. Iltimos, sahifani yangilang.
            </div>
        `;
    }
}

function renderTopics(topics) {
    const list = document.getElementById('topics-list');
    list.innerHTML = '';
    topics.forEach(topic => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = topic.title;
        li.onclick = () => {
            showTopic(topic.id, li);
            // Mobilda sidebar avtomatik yopilsin
            if (window.innerWidth < 992) {
                sidebar.classList.remove('open');
                document.body.classList.remove('menu-open');
                if (overlay) overlay.style.display = 'none';
            }
        };
        list.appendChild(li);
    });
}

const searchResults = document.getElementById('search-results');

searchInput.oninput = () => {
    const val = searchInput.value.toLowerCase();
    if (!val) {
        searchResults.classList.remove('show');
        renderTopics(allTopics);
        return;
    }
    const filtered = allTopics.filter(t => t.title.toLowerCase().includes(val));
    renderTopics(filtered);

    // Dropdown natijalar
    if (filtered.length > 0) {
        searchResults.innerHTML = filtered.map(t =>
            `<button class="dropdown-item" type="button" data-id="${t.id}">${t.title}</button>`
        ).join('');
        searchResults.classList.add('show');
    } else {
        searchResults.innerHTML = '<span class="dropdown-item text-muted">Hech narsa topilmadi</span>';
        searchResults.classList.add('show');
    }
};

// Natijaga bosilganda mavzu tafsiloti ochiladi
searchResults.onclick = e => {
    if (e.target.matches('.dropdown-item[data-id]')) {
        const id = e.target.getAttribute('data-id');
        showTopic(id);
        searchResults.classList.remove('show');
        searchInput.value = '';
        // Barcha mavzularni qayta ko'rsatish
        renderTopics(allTopics);
    }
};

// Show topic with error handling
async function showTopic(id, li) {
    try {
        document.querySelectorAll('.sidebar .list-group-item').forEach(el => el.classList.remove('active'));
        if (li) li.classList.add('active');
        
        const topic = await apiCall(`/api/topics/${id}`);
        const main = document.getElementById('main-content');
        main.innerHTML = formatTopicContent(topic);
        
        // Welcome stats yangilash
        loadWelcomeStats();
        
        // Mobilda sidebar avtomatik yopilsin
        if (window.innerWidth < 992) {
            sidebar.classList.remove('open');
            document.body.classList.remove('menu-open');
            if (overlay) overlay.style.display = 'none';
        }
    } catch (error) {
        showError('Mavzu yuklanmadi. Iltimos, qaytadan urinib ko\'ring.');
    }
}

function formatTopicContent(topic) {
    return `
        <div class="topic-card">
            <h2 class="topic-title">${topic.title}</h2>
            <div class="topic-structure">
                <strong>Qoidalar:</strong>
                <div class="structure">${topic.structure}</div>
            </div>
            <div class="topic-media">
                ${topic.image_url ? `<img src="${topic.image_url}" alt="Rasm">` : ''}
                ${topic.video_url ? renderVideo(topic.video_url) : ''}
            </div>
            <div class="topic-examples">
                <div class="examples-accordion">
                    <div class="examples-header collapsed">
                        Misollar
                    </div>
                    <div class="examples-content">
                        <div class="structure">${topic.examples}</div>
                    </div>
                </div>
            </div>
            <form class="feedback-form mt-4 p-3 bg-light rounded-4" data-topic-id="${topic.id}">
                <label class="mb-2 fw-bold" for="feedback-text">Sharhingiz:</label>
                <textarea class="form-control mb-2" id="feedback-text" rows="2" required placeholder="Fikringizni yozing..."></textarea>
                <button type="submit" class="btn btn-primary">Yuborish</button>
                <div class="feedback-success text-success mt-2" style="display:none;">Sharhingiz yuborildi!</div>
                <div class="feedback-error text-danger mt-2" style="display:none;"></div>
            </form>
        </div>
    `;
}

// Accordion funksionalligi
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('examples-header')) {
        const header = e.target;
        const content = header.nextElementSibling;
        const isCollapsed = header.classList.contains('collapsed');
        
        // Barcha accordionlarni yopish
        document.querySelectorAll('.examples-header').forEach(h => {
            h.classList.add('collapsed');
            h.nextElementSibling.classList.remove('show');
        });
        
        // Agar bosilgan accordion yopiq bo'lsa, uni ochish
        if (isCollapsed) {
            header.classList.remove('collapsed');
            content.classList.add('show');
        }
    }
});

function renderVideo(url) {
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        let videoId = '';
        if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split(/[?&]/)[0];
        } else if (url.includes('v=')) {
            videoId = url.split('v=')[1].split('&')[0];
        }
        if (videoId) {
            return `<iframe width="360" height="215" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>`;
        }
    }
    return `<video src="${url}" controls style="max-width:360px;"></video>`;
}

// Telegram WebApp ready
tg.ready();
tg.expand();

// Load topics when page loads
loadTopics();

// Webapp tugmasi (admin uchun doim ko'rinadi)
const webappBtn = document.getElementById('webapp-btn');
if (webappBtn) {
    webappBtn.onclick = () => {
        window.open(window.location.href, '_blank');
    };
}

// Yangi mavzu formasi
const form = document.getElementById('new-topic-form');
const imageFile = document.getElementById('image-file');
const imageLink = document.getElementById('image-link');
const imagePreview = document.getElementById('image-preview');
const videoFile = document.getElementById('video-file');
const videoLink = document.getElementById('video-link');
const videoPreview = document.getElementById('video-preview');

if (imageFile) {
    imageFile.onchange = () => {
        if (imageFile.files[0]) {
            const reader = new FileReader();
            reader.onload = e => {
                imagePreview.innerHTML = `<img src="${e.target.result}" style="max-width:200px;">`;
            };
            reader.readAsDataURL(imageFile.files[0]);
        }
    };
}
if (imageLink) {
    imageLink.oninput = () => {
        if (imageLink.value) {
            imagePreview.innerHTML = `<img src="${imageLink.value}" style="max-width:200px;">`;
        } else {
            imagePreview.innerHTML = '';
        }
    };
}
if (videoFile) {
    videoFile.onchange = () => {
        if (videoFile.files[0]) {
            const reader = new FileReader();
            reader.onload = e => {
                videoPreview.innerHTML = `<video src="${e.target.result}" controls style="max-width:300px;"></video>`;
            };
            reader.readAsDataURL(videoFile.files[0]);
        }
    };
}
if (videoLink) {
    videoLink.oninput = () => {
        if (videoLink.value.includes('youtube.com') || videoLink.value.includes('youtu.be')) {
            let videoId = '';
            if (videoLink.value.includes('youtu.be/')) {
                videoId = videoLink.value.split('youtu.be/')[1].split(/[?&]/)[0];
            } else if (videoLink.value.includes('v=')) {
                videoId = videoLink.value.split('v=')[1].split('&')[0];
            }
            if (videoId) {
                videoPreview.innerHTML = `<iframe width="300" height="180" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>`;
            }
        } else if (videoLink.value) {
            videoPreview.innerHTML = `<video src="${videoLink.value}" controls style="max-width:300px;"></video>`;
        } else {
            videoPreview.innerHTML = '';
        }
    };
}

if (form) {
    form.onsubmit = async e => {
        e.preventDefault();
        const data = {
            title: form.title.value,
            structure: form.structure.value,
            examples: form.examples.value,
            image_url: '',
            video_url: ''
        };
        // Rasm yuklash yoki link
        if (imageFile.files[0]) {
            const fd = new FormData();
            fd.append('file', imageFile.files[0]);
            const res = await fetch('/api/upload', { method: 'POST', body: fd });
            const json = await res.json();
            data.image_url = json.url;
        } else if (imageLink.value) {
            data.image_url = imageLink.value;
        }
        // Video yuklash yoki link
        if (videoFile.files[0]) {
            const fd = new FormData();
            fd.append('file', videoFile.files[0]);
            const res = await fetch('/api/upload', { method: 'POST', body: fd });
            const json = await res.json();
            data.video_url = json.url;
        } else if (videoLink.value) {
            data.video_url = videoLink.value;
        }
        // Yangi mavzuni saqlash
        await fetch('/api/topics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        form.reset();
        imagePreview.innerHTML = '';
        videoPreview.innerHTML = '';
        loadTopics();
        alert('Mavzu qo\'shildi!');
    };
}

// Sidebar faqat overlay ustiga bosilganda yopiladi
document.addEventListener('click', function(e) {
    if (
        window.innerWidth < 992 &&
        sidebar.classList.contains('open')
    ) {
        if (
            !sidebar.contains(e.target) &&
            !hamburger.contains(e.target) &&
            !overlay.contains(e.target)
        ) {
            sidebar.classList.remove('open');
            document.body.classList.remove('menu-open');
            overlay.style.display = 'none';
        }
    }
});

function closeSidebarIfOpen(e) {
    if (
        window.innerWidth < 992 &&
        sidebar.classList.contains('open')
    ) {
        sidebar.classList.remove('open');
        document.body.classList.remove('menu-open');
    }
}

const navbar = document.querySelector('.navbar');
function updateOverlayTop() {
    overlay.style.top = navbar.offsetHeight + 'px';
}
window.addEventListener('resize', updateOverlayTop);
updateOverlayTop();

// Update only stats and feedback after feedback submit
function updateWelcomeFeedbackAndStats() {
    loadWelcomeStats();
}

// Feedback form submit handler (delegated to body for robustness)
document.body.addEventListener('submit', async function(e) {
    if (e.target.classList.contains('feedback-form')) {
        e.preventDefault();
        alert('Feedback form submit ishladi!');
        console.log('Feedback form submit ishladi!');
        const form = e.target;
        const topicId = form.getAttribute('data-topic-id');
        const textarea = form.querySelector('textarea');
        const submitBtn = form.querySelector('button[type="submit"]');
        const comment = textarea.value.trim();
        const successMsg = form.querySelector('.feedback-success');
        const errorMsg = form.querySelector('.feedback-error');

        // Reset messages
        successMsg.style.display = 'none';
        errorMsg.style.display = 'none';

        // Yangi: topicId tekshirish
        if (!topicId || isNaN(Number(topicId))) {
            errorMsg.textContent = "Mavzu aniqlanmadi yoki noto'g'ri!";
            errorMsg.style.display = 'block';
            alert("Mavzu aniqlanmadi yoki noto'g'ri! Iltimos, sahifani yangilang.");
            return;
        }
        if (!comment) {
            errorMsg.textContent = "Sharh bo'sh bo'lishi mumkin emas!";
            errorMsg.style.display = 'block';
            return;
        }

        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Yuborilmoqda...';

        // user_id olish (Telegram yoki oddiy ism)
        let userId = null;
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
            userId = window.Telegram.WebApp.initDataUnsafe.user.id;
        } else {
            userId = localStorage.getItem('webapp_name');
            if (!userId) {
                userId = prompt("Ismingizni kiriting (faqat bir marta so'raladi):");
                if (userId) localStorage.setItem('webapp_name', userId);
            }
        }

        if (!userId) {
            errorMsg.textContent = "Ismingiz kiritilmadi.";
            errorMsg.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Yuborish';
            return;
        }

        try {
            const res = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, topic_id: topicId, comment })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(`HTTP error! status: ${res.status}, body: ${errText}`);
            }

            const data = await res.json();
            if (data.status === 'ok') {
                textarea.value = '';
                successMsg.style.display = 'block';
                setTimeout(() => { successMsg.style.display = 'none'; }, 2500);
                if (typeof updateWelcomeFeedbackAndStats === 'function') updateWelcomeFeedbackAndStats();
            } else {
                throw new Error(data.error || 'Xatolik yuz berdi.');
            }
        } catch (err) {
            console.error('Feedback submission error:', err);
            errorMsg.textContent = err.message || 'Tarmoq xatoligi.';
            errorMsg.style.display = 'block';
            alert('Sharh yuborishda xatolik: ' + (err.message || 'Tarmoq xatoligi.'));
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = 'Yuborish';
        }
    }
});

function renderFeedbackBox(feedbacks) {
    if (!feedbacks.length) return "<div class='text-muted'>Sharhlar hali yo'q.</div>";
    let html = `<div class='fw-bold mb-2' style='color:#2481cc;'>💬 Foydalanuvchi sharhlari</div>`;
    const showCount = 3;
    const visible = feedbacks.slice(0, showCount);
    const hidden = feedbacks.slice(showCount);

    html += visible.map(f =>
        `<div class='feedback-item small text-muted mb-2'>
            <span class='d-block' style='font-size:1.05em;'>&ldquo;${f.comment}&rdquo;</span>
            <span class='text-secondary' style='font-size:0.95em;'>- ${f.user} <span style='color:#bbb;'>(${f.topic})</span></span>
        </div>`
    ).join('');

    if (hidden.length) {
        html += `<div class='feedback-hidden' style='display:none;'>` +
            hidden.map(f =>
                `<div class='feedback-item small text-muted mb-2'>
                    <span class='d-block' style='font-size:1.05em;'>&ldquo;${f.comment}&rdquo;</span>
                    <span class='text-secondary' style='font-size:0.95em;'>- ${f.user} <span style='color:#bbb;'>(${f.topic})</span></span>
                </div>`
            ).join('') +
            `</div>
            <button class='btn btn-link p-0 feedback-toggle' style='font-size:0.98em;'>Barcha sharhlarni ko'rish</button>`;
    }
    return html;
}

// WebSocket connection
const socket = io();

// WebSocket event handlers
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
});

socket.on('feedback_update', (data) => {
    console.log('New feedback received:', data);
    // Update feedback list
    const fbBox = document.getElementById('feedback-list');
    if (fbBox) {
        const feedbacks = JSON.parse(localStorage.getItem('feedbacks') || '[]');
        feedbacks.unshift(data);
        localStorage.setItem('feedbacks', JSON.stringify(feedbacks.slice(0, 5)));
        fbBox.innerHTML = renderFeedbackBox(feedbacks);
    }
});

socket.on('stats_update', (data) => {
    console.log('Stats updated:', data);
    // Update stats
    const users = document.getElementById('stats-users');
    if (users && data.users_count !== undefined) {
        users.textContent = data.users_count;
    }
});

socket.on('news_update', (data) => {
    console.log('News updated:', data);
    // Update news
    const newsList = document.getElementById('news-list');
    if (newsList) {
        const news = JSON.parse(localStorage.getItem('news') || '[]');
        news.unshift(data);
        localStorage.setItem('news', JSON.stringify(news.slice(0, 5)));
        newsList.innerHTML = news.map(n => 
            `<li><b>${n.created_at}:</b> ${n.title}</li>`
        ).join('');
    }
});

// Update loadWelcomeStats function
function loadWelcomeStats() {
    // Statistika
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            const users = document.getElementById('stats-users');
            if (users && data.users_count !== undefined) {
                users.textContent = data.users_count;
            }
        })
        .catch(err => {
            console.error('Stats API error:', err);
            const users = document.getElementById('stats-users');
            if (users) users.textContent = '...';
        });

    // Mavzular soni
    fetch('/api/topics')
        .then(r => r.json())
        .then(data => {
            const topics = document.getElementById('stats-topics');
            if (topics && Array.isArray(data)) {
                topics.textContent = data.length;
            }
        })
        .catch(err => {
            console.error('Topics API error:', err);
            const topics = document.getElementById('stats-topics');
            if (topics) topics.textContent = '...';
        });

    // Yangiliklar
    fetch('/api/news')
        .then(r => r.json())
        .then(news => {
            const newsList = document.getElementById('news-list');
            if (newsList) {
                if (news && news.length > 0) {
                    localStorage.setItem('news', JSON.stringify(news));
                    newsList.innerHTML = news.map(n => 
                        `<li><b>${n.created_at}:</b> ${n.title}</li>`
                    ).join('');
                } else {
                    newsList.innerHTML = '<li class="text-center text-muted">Yangiliklar yo\'q</li>';
                }
            }
        })
        .catch(err => {
            console.error('News API error:', err);
            const newsList = document.getElementById('news-list');
            if (newsList) {
                newsList.innerHTML = '<li class="text-center text-danger">Yangiliklar yuklanmadi</li>';
            }
        });

    // Foydalanuvchi sharhlari
    fetch('/api/feedback')
        .then(r => r.json())
        .then(feedbacks => {
            const fbBox = document.getElementById('feedback-list');
            if (fbBox) {
                localStorage.setItem('feedbacks', JSON.stringify(feedbacks));
                fbBox.innerHTML = renderFeedbackBox(feedbacks);
                const toggle = fbBox.querySelector('.feedback-toggle');
                if (toggle) {
                    toggle.onclick = function() {
                        const hidden = fbBox.querySelector('.feedback-hidden');
                        if (hidden.style.display === 'none') {
                            hidden.style.display = 'block';
                            toggle.textContent = "Yopish";
                        } else {
                            hidden.style.display = 'none';
                            toggle.textContent = "Barcha sharhlarni ko'rish";
                        }
                    };
                }
            }
        })
        .catch(err => {
            console.error('Feedback API error:', err);
            const fbBox = document.getElementById('feedback-list');
            if (fbBox) fbBox.innerHTML = "<div class='text-muted'>Sharhlar yuklanmadi.</div>";
        });
}

// Load stats when page loads
document.addEventListener('DOMContentLoaded', loadWelcomeStats);
// Update stats every 30 seconds
setInterval(loadWelcomeStats, 30000); 