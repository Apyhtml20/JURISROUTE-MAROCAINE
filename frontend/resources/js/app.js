function togglePassword(id) {
    const input = document.getElementById(id);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach((el) => {
        setTimeout(() => {
            el.style.transition = 'opacity .35s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 350);
        }, 5000);
    });
});
