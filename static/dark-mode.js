const toggle = document.getElementById('darkModeToggle');

if (localStorage.getItem('darkMode') === 'enabled') {
  document.body.classList.add('dark-mode');
  if (toggle) toggle.textContent = '☀️';
}

if (toggle) {
  toggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');

    const isDark = document.body.classList.contains('dark-mode');

    // Save preference
    localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');

    // Update icon
    toggle.textContent = isDark ? '☀️' : '🌙';
  });
}