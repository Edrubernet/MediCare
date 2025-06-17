// Функція для отримання CSRF токену
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Налаштування AJAX для відправки CSRF токену
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

// Функція для роботи з API з використанням JWT токену
function apiRequest(endpoint, method = 'GET', data = null) {
    // Отримання JWT токену з локального сховища
    const token = localStorage.getItem('access_token');
    
    // Налаштування заголовків
    const headers = {
        'Content-Type': 'application/json',
    };
    
    // Додавання токену до заголовків, якщо він існує
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Налаштування запиту
    const requestOptions = {
        method: method,
        headers: headers,
    };
    
    // Додавання даних до запиту, якщо вони існують
    if (data) {
        requestOptions.body = JSON.stringify(data);
    }
    
    // Виконання запиту
    return fetch(endpoint, requestOptions)
        .then(response => {
            // Перевірка на 401 (неавторизований) для оновлення токену
            if (response.status === 401) {
                return refreshToken()
                    .then(() => apiRequest(endpoint, method, data))
                    .catch(() => {
                        // Якщо оновлення токену не вдалося, перенаправлення на сторінку входу
                        window.location.href = "/login/";
                        return Promise.reject('Unauthorized');
                    });
            }
            
            // Обробка інших відповідей
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            return response.json().catch(() => response.text());
        });
}

// Функція для оновлення JWT токену
function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
        return Promise.reject('No refresh token');
    }
    
    return fetch('/api/token/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to refresh token');
        }
        return response.json();
    })
    .then(data => {
        localStorage.setItem('access_token', data.access);
        return data;
    });
}

// Функція для виходу з системи
function logout() {
    // Видалення токенів
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Перенаправлення на сторінку входу
    window.location.href = "/login/";
}

// Автоматичне закриття повідомлень через 5 секунд
$(document).ready(function() {
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
});