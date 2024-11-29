document.addEventListener('DOMContentLoaded', function() {
    const startSummarizerBtn = document.getElementById('start-summarizer');

    startSummarizerBtn.addEventListener('click', function() {
        window.location.href = '/summarizer';
    });
});
