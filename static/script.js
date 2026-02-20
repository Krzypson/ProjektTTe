function initializeTokenCountdown() {
        const expirationTimestamp = getCookie('token_expiration');
        if (!expirationTimestamp) {
            return;
        }

        const expirationTime = parseInt(expirationTimestamp) * 1000; // Convert to milliseconds

        function updateCountdown() {
            const currentTime = Date.now();
            const remainingMs = expirationTime - currentTime;

            if (remainingMs <= 0) {
                document.getElementById('token-timer').textContent = '0:00';
                clearInterval(countdownInterval);
                return;
            }

            const remainingSeconds = Math.floor(remainingMs / 1000);
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;

            document.getElementById('token-timer').textContent =
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        // Update immediately
        updateCountdown();

        // Update every second
        const countdownInterval = setInterval(updateCountdown, 1000);
    }

    // Initialize countdown when page loads
    document.addEventListener('DOMContentLoaded', initializeTokenCountdown);