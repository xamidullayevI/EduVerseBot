let tg = window.Telegram.WebApp;

async function loadTopics() {
    const res = await fetch('/api/topics');
    const topics = await res.json();
    const list = document.getElementById('topics-list');
    list.innerHTML = '';
    topics.forEach(topic => {
        const li = document.createElement('li');
        li.textContent = topic.title;
        li.onclick = () => showTopic(topic.id, li);
        list.appendChild(li);
    });
    document.querySelector('.loader').style.display = 'none';
}

async function showTopic(id, li) {
    document.querySelectorAll('.sidebar li').forEach(el => el.classList.remove('active'));
    li.classList.add('active');
    const res = await fetch(`/api/topics/${id}`);
    const topic = await res.json();
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <h2>${topic.title}</h2>
        <p><b>Strukturasi:</b> ${topic.structure}</p>
        <p><b>Misollar:</b> ${topic.examples}</p>
        ${topic.image_url ? `<img src="${topic.image_url}" alt="Rasm">` : ''}
        ${topic.video_url ? `<video src="${topic.video_url}" controls></video>` : ''}
    `;
}

// Telegram WebApp ready
tg.ready();
tg.expand();

// Load topics when page loads
loadTopics(); 