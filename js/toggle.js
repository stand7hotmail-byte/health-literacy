function toggleAcc(btn) {
  var body = btn.nextElementSibling;
  var isOpen = body.classList.contains('open');
  if (isOpen) {
    body.classList.remove('open');
    btn.classList.remove('open');
    btn.querySelector('.arrow').textContent = '\u25BC';
  } else {
    body.classList.add('open');
    btn.classList.add('open');
    btn.querySelector('.arrow').textContent = '\u25B2';
  }
}