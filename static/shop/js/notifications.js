(function () {
    'use strict';

    const POLL_INTERVAL = 8000;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];

    async function fetchNotifications() {
        try {
            const res = await fetch('/api/notifications/');
            if (!res.ok) return;
            const data = await res.json();
            updateNotificationUI(data);
        } catch (e) { /* silent */ }
    }

    function updateNotificationUI(data) {
        const dot = document.getElementById('notif-dot');
        const list = document.getElementById('notification-list');
        if (!dot && !list) return;

        if (data.count > 0) {
            if (dot) dot.classList.remove('d-none');
            if (list) {
                list.innerHTML = data.notifications.map(n => `
                    <div class="notification-item p-3 border-bottom" data-id="${n.id}">
                        <strong>${escapeHtml(n.title)}</strong>
                        <p class="mb-1 small text-muted">${escapeHtml(n.message)}</p>
                        <small class="text-muted">${n.created_at}</small>
                    </div>
                `).join('');
            }
            data.notifications.forEach(n => showToast(n.title, n.message));
        } else {
            if (dot) dot.classList.add('d-none');
        }
    }

    function showToast(title, message) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const id = 'toast-' + Date.now();
        container.insertAdjacentHTML('beforeend', `
            <div id="${id}" class="toast show" role="alert">
                <div class="toast-header">
                    <strong class="me-auto">🧇 ${escapeHtml(title)}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">${escapeHtml(message)}</div>
            </div>
        `);
        setTimeout(() => document.getElementById(id)?.remove(), 6000);
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    document.getElementById('mark-all-read')?.addEventListener('click', async () => {
        await fetch('/api/notifications/read-all/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
        });
        document.getElementById('notif-dot')?.classList.add('d-none');
    });

    if (document.body.classList.contains('admin-page') === false) {
        setInterval(fetchNotifications, POLL_INTERVAL);
        fetchNotifications();
    }
})();
