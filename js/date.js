var d = new Date();
var opts = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
var el = document.getElementById('dateNow');
if (el) el.textContent = d.toLocaleDateString('ja-JP', opts);