// JavaScript extracted from index.html

document.addEventListener('DOMContentLoaded', () => {
    const contentDisplay = document.getElementById('content-display');
    const lastEntryLink = document.getElementById('last-entry-link');
    const owner = 'wllclngn';
    const repo = 'SomeKindofFiction';
    const branch = 'main';
    const filePath = 'Fantasy.txt';
    const rawFileURL = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${filePath}`;

    fetch(rawFileURL)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.text();
        })
        .then(text => {
            if (text.trim() === '') {
                contentDisplay.innerHTML = '<p class="error-message">Fantasy.txt appears to be empty.</p>';
            } else {
                const processedText = text.replace(/([^\n])\n([^\n])/g, '$1 $2');
                const entries = processedText.split(/(?=●)/).map(entry => entry.trim()).filter(entry => entry);

                const lastEntryIndex = entries.length - 1;
                lastEntryLink.href = `?entry=${lastEntryIndex}`;
                lastEntryLink.addEventListener('click', (event) => {
                    event.preventDefault();
                    renderEntry(entries[lastEntryIndex]);
                });

                const urlParams = new URLSearchParams(window.location.search);
                const entryIndex = urlParams.get('entry');
                if (entryIndex !== null && entries[entryIndex]) {
                    renderEntry(entries[entryIndex]);
                } else {
                    renderEntry(entries.join('\n\n'));
                }
            }
        })
        .catch(error => {
            console.error('Error fetching Fantasy.txt:', error);
            contentDisplay.innerHTML = `<p class="error-message">Error loading content from ${filePath}.<br>Please ensure the file exists at the correct path in the '${branch}' branch, and that the file contains valid content.</p>`;
        });

    function renderEntry(entry) {
        contentDisplay.innerHTML = `<p>${entry.replace(/\n/g, '<p class="desktop-width"></p>')}</p>`;
    }
});