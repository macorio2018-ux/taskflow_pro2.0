// Lógica de cambio de tema (Claro/Oscuro)
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';

    // Aplicar el tema guardado al cargar la página
    if (currentTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeToggle) themeToggle.innerHTML = '<i data-feather="moon"></i>';
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isLight = document.documentElement.getAttribute('data-theme') === 'light';
            const newTheme = isLight ? 'dark' : 'light';
            
            // Cambiar atributo y guardar preferencia
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Cambiar el icono
            themeToggle.innerHTML = newTheme === 'light' ? '<i data-feather="moon"></i>' : '<i data-feather="sun"></i>';
            
            // Re-renderizar iconos de feather
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        });
    }
});
