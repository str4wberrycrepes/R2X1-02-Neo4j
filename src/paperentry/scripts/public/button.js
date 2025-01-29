// Get button and figure parent
const button = document.getElementById('addKeyword');
const keywordsFig = button.closest('figure');

// Event listener
button.addEventListener('click', () => {
    const textarea = document.createElement('textarea');
    textarea.name = 'keywords';
    textarea.id = 'keywords';
    textarea.style.marginTop = '8px';

    // Add the new textarea
    keywordsFig.appendChild(textarea);
});