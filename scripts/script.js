document.addEventListener('DOMContentLoaded', () => {
    const contentDisplay = document.getElementById('content-display');
    const lastEntryLink = document.getElementById('last-entry-link');
    const owner = 'wllclngn';
    const repo = 'SomeKindofFiction';
    const branch = 'main';
    const filePath = 'src/Fantasy.txt';
    const rawFileURL = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${filePath}`;

    // Fetch the content of Fantasy.txt
    fetch(rawFileURL)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.text();
        })
        .then(text => {
            if (text.trim() === '') {
                displayErrorMessage('Fantasy.txt appears to be empty.');
            } else {
                const processedText = preprocessText(text);
                const entries = splitEntries(processedText);

                const lastEntryIndex = entries.length - 1;
                lastEntryLink.href = `?entry=${lastEntryIndex}`;
                lastEntryLink.addEventListener('click', (event) => {
                    event.preventDefault();
                    renderEntry(entries[lastEntryIndex]);
                });

                const entryIndex = new URLSearchParams(window.location.search).get('entry');
                if (entryIndex !== null && entries[entryIndex]) {
                    renderEntry(entries[entryIndex]);
                } else {
                    renderEntry(entries.join('\n\n'));
                }
            }
        })
        .catch(error => {
            console.error('Error fetching Fantasy.txt:', error);
            displayErrorMessage(`Error loading content from ${filePath}.<br>Please ensure the file exists at the correct path in the '${branch}' branch, and try again.`);
        });

    function renderEntry(entry) {
        contentDisplay.innerHTML = `<p>${entry.replace(/\n/g, '<br>')}</p>`;
    }

    function preprocessText(text) {
        // Collapse single newlines into spaces
        return text.replace(/([^\n])\n([^\n])/g, '$1 $2');
    }

    function splitEntries(text) {
        return text
            .split(/(?=\u25cf)/)
            .map(entry => entry.trim())
            .filter(entry => entry);
    }

    function displayErrorMessage(message) {
        contentDisplay.innerHTML = `<p class="error-message">${message}</p>`;
    }
});
