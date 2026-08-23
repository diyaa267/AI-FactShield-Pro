const textArea = document.getElementById('newsText');
const charCount = document.getElementById('charCount');
if (textArea && charCount) {
  const update = () => { charCount.textContent = `${textArea.value.length.toLocaleString()} characters`; };
  textArea.addEventListener('input', update); update();
}

document.querySelectorAll('.mode-btn').forEach(btn => btn.addEventListener('click', () => {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const mode = btn.dataset.mode;
  if (textArea && mode !== 'text') textArea.placeholder = mode === 'video' ? 'Video mode: upload a video below. Add a claim here too for stronger verification.' : mode === 'audio' ? 'Audio mode: use Start Voice or upload a WAV/FLAC file.' : 'Add a claim here, or upload an image/PDF below for extraction.';
}));
