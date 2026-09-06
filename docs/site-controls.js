(() => {
  const menu = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  const closeMenu = () => {
    links.classList.remove('open');
    menu.setAttribute('aria-expanded', 'false');
  };
  menu.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && links.classList.contains('open')) {
      closeMenu();
      menu.focus();
    }
  });
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', event => {
      const id = link.getAttribute('href').slice(1);
      const target = id ? document.getElementById(id) : document.body;
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
      closeMenu();
    });
  });
  document.querySelectorAll('.copy-btn').forEach(button => {
    let reset;
    button.addEventListener('click', async () => {
      const status = document.getElementById('copy-status');
      const command = button.closest('.code-block').querySelector('code').textContent.trim();
      clearTimeout(reset);
      button.disabled = true;
      button.textContent = 'Copying…';
      status.textContent = '';
      try {
        await navigator.clipboard.writeText(command);
        button.textContent = 'Copied';
        status.textContent = 'Command copied to clipboard.';
      } catch {
        button.textContent = 'Copy';
        status.textContent = 'Clipboard unavailable. Select and copy the command above.';
      } finally {
        button.disabled = false;
        reset = setTimeout(() => { button.textContent = 'Copy'; }, 2000);
      }
    });
  });
})();
