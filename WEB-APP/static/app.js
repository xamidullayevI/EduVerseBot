let tg = window.Telegram.WebApp;

// Hamburger menu (Bootstrap bilan)
const hamburger = document.getElementById('hamburger-menu');
const sidebar = document.getElementById('sidebar');
const overlay = document.querySelector('.sidebar-overlay');
hamburger.onclick = () => {
    sidebar.classList.toggle('open');
    document.body.classList.toggle('menu-open');
    overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
};
overlay.onclick = () => {
    sidebar.classList.remove('open');
    document.body.classList.remove('menu-open');
    overlay.style.display = 'none';
};

// Qidiruv
const searchInput = document.getElementById('search-input');
let allTopics = [];

async function loadTopics() {
    const res = await fetch('/api/topics');
    allTopics = await res.json();
    renderTopics(allTopics);
    document.querySelector('.loader').style.display = 'none';
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

function renderExamples(text) {
    // Har bir nuqta bilan tugaydigan gapni raqamlab chiqaradi
    if (!text) return '';
    // Split by ". " (nuqta va probel) va filter bo'shlarni olib tashlash
    const sentences = text.split('.').map(s => s.trim()).filter(Boolean);
    return '<ol>' + sentences.map(s => `<li>${s}.</li>`).join('') + '</ol>';
}

async function showTopic(id, li) {
    document.querySelectorAll('.sidebar .list-group-item').forEach(el => el.classList.remove('active'));
    if (li) li.classList.add('active');
    const res = await fetch(`/api/topics/${id}`);
    const topic = await res.json();
    const main = document.getElementById('main-content');
    main.innerHTML = formatTopicContent(topic);
    // Welcome stats yangilash
    loadWelcomeStats();
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
document.getElementById('webapp-btn').onclick = () => {
    window.open(window.location.href, '_blank');
};

// Yangi mavzu formasi
const form = document.getElementById('new-topic-form');
const imageFile = document.getElementById('image-file');
const imageLink = document.getElementById('image-link');
const imagePreview = document.getElementById('image-preview');
const videoFile = document.getElementById('video-file');
const videoLink = document.getElementById('video-link');
const videoPreview = document.getElementById('video-preview');

imageFile.onchange = () => {
    if (imageFile.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            imagePreview.innerHTML = `<img src="${e.target.result}" style="max-width:200px;">`;
        };
        reader.readAsDataURL(imageFile.files[0]);
    }
};
imageLink.oninput = () => {
    if (imageLink.value) {
        imagePreview.innerHTML = `<img src="${imageLink.value}" style="max-width:200px;">`;
    } else {
        imagePreview.innerHTML = '';
    }
};
videoFile.onchange = () => {
    if (videoFile.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            videoPreview.innerHTML = `<video src="${e.target.result}" controls style="max-width:300px;"></video>`;
        };
        reader.readAsDataURL(videoFile.files[0]);
    }
};
videoLink.oninput = () => {
    if (videoLink.value.includes('youtube.com') || videoLink.value.includes('youtu.be')) {
        // YouTube linkdan video ID ajratib iframe ko'rsatish
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

// Real-time stats, news, feedback rendering for welcome section
function loadWelcomeStats() {
    // Statistika
    fetch('/api/stats').then(r=>r.json()).then(data => {
        if (data.users_count !== undefined) {
            document.getElementById('stats-users').textContent = data.users_count;
        }
    });
    fetch('/api/topics').then(r=>r.json()).then(data => {
        document.getElementById('stats-topics').textContent = data.length;
    });
    // Yangiliklar
    fetch('/api/news').then(r=>r.json()).then(news => {
        const newsList = document.querySelector('.welcome ul.list-unstyled');
        if(newsList && news.length) {
            newsList.innerHTML = news.map(n => `<li><b>${n.created_at}:</b> ${n.title}</li>`).join('');
        }
    });
    // Foydalanuvchi sharhlari
    fetch('/api/feedback').then(r=>r.json()).then(feedbacks => {
        const fbBox = document.querySelector('.welcome .bg-white.rounded-4.shadow-sm.p-4');
        if(fbBox && feedbacks.length) {
            fbBox.innerHTML = `<div class='fw-bold mb-2' style='color:#2481cc;'>💬 Foydalanuvchi sharhlari</div>` +
                feedbacks.map(f => `<div class='small text-muted mb-2'>"${f.comment}" <span class='text-secondary'>- ${f.user}</span></div>`).join('');
        }
    });
}

document.addEventListener('DOMContentLoaded', loadWelcomeStats);

// Feedback form submit handler
document.addEventListener('submit', async function(e) {
    if (e.target.classList.contains('feedback-form')) {
        e.preventDefault();
        const form = e.target;
        const topicId = form.getAttribute('data-topic-id');
        const textarea = form.querySelector('textarea');
        const comment = textarea.value.trim();
        const successMsg = form.querySelector('.feedback-success');
        const errorMsg = form.querySelector('.feedback-error');
        successMsg.style.display = 'none';
        errorMsg.style.display = 'none';
        if (!comment) {
            errorMsg.textContent = 'Sharh bo‘sh bo‘lishi mumkin emas!';
            errorMsg.style.display = 'block';
            return;
        }
        // Telegram user_id ni olish
        let userId = null;
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
            userId = window.Telegram.WebApp.initDataUnsafe.user.id;
        }
        if (!userId) {
            errorMsg.textContent = 'Foydalanuvchi aniqlanmadi. Telegram WebApp orqali kiring.';
            errorMsg.style.display = 'block';
            return;
        }
        // Yuborish
        try {
            const res = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, topic_id: topicId, comment })
            });
            const data = await res.json();
            if (data.status === 'ok') {
                successMsg.style.display = 'block';
                textarea.value = '';
                if (document.querySelector('.welcome')) loadWelcomeStats();
            } else {
                errorMsg.textContent = data.error || 'Xatolik yuz berdi.';
                errorMsg.style.display = 'block';
            }
        } catch (err) {
            errorMsg.textContent = 'Tarmoq xatoligi.';
            errorMsg.style.display = 'block';
        }
    }
});

// Har 30 soniyada welcome stats yangilash (real-time uchun)
setInterval(loadWelcomeStats, 30000); 