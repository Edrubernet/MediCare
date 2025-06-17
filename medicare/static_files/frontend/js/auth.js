// This file handles JWT authentication logic for the frontend.

const publicPaths = ['/', '/login/', '/register/'];

// 1. Redirect to login if no token is found and the page is not public
if (!localStorage.getItem('accessToken') && !publicPaths.includes(window.location.pathname)) {
    window.location.href = '/login/';
}

// 2. Override the default fetch function to include the Authorization header
const originalFetch = window.fetch;
window.fetch = async (url, options) => {
    let accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    // Add Authorization header if the URL is an API endpoint
    if (url.startsWith('/api/') && accessToken) {
        if (!options) {
            options = {};
        }
        if (!options.headers) {
            options.headers = {};
        }
        options.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    let response = await originalFetch(url, options);

    // 3. Handle token refresh if the access token has expired
    if (response.status === 401 && refreshToken && url.startsWith('/api/')) {
        try {
            const refreshResponse = await originalFetch('/api/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (refreshResponse.ok) {
                const newTokens = await refreshResponse.json();
                localStorage.setItem('accessToken', newTokens.access);
                accessToken = newTokens.access;

                // Re-add the Authorization header with the new token
                options.headers['Authorization'] = `Bearer ${accessToken}`;
                
                // Retry the original request with the new token
                console.log('Token refreshed, retrying original request...');
                response = await originalFetch(url, options);
            } else {
                // If refresh fails, redirect to login
                console.error('Failed to refresh token. Redirecting to login.');
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login/';
            }
        } catch (error) {
            console.error('Error during token refresh:', error);
            window.location.href = '/login/';
        }
    }

    return response;
}; 