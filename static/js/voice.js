const voiceBtn = document.getElementById('voiceBtn');
const newsText = document.getElementById('newsText');
if (voiceBtn && newsText) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.textContent = '🎙 Voice unavailable';
    voiceBtn.title = 'Use Chrome/Edge voice recognition';
  } else {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';
    voiceBtn.addEventListener('click', () => {
      recognition.lang = document.documentElement.lang === 'gu' ? 'gu-IN' : 'en-IN';
      recognition.start();
      voiceBtn.textContent = '● Listening...';
    });
    recognition.onresult = e => {
      let text = '';
      for (let i = e.resultIndex; i < e.results.length; i++) text += e.results[i][0].transcript;
      newsText.value = `${newsText.value} ${text}`.trim();
      newsText.dispatchEvent(new Event('input'));
    };
    recognition.onend = () => { voiceBtn.textContent = '🎙 Start Voice'; };
    recognition.onerror = () => { voiceBtn.textContent = '🎙 Try Voice Again'; };
  }
}
