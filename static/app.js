const form = document.querySelector('#analysis-form');
const imageInput = document.querySelector('#image');
const preview = document.querySelector('#preview');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const submit = document.querySelector('#submit');

imageInput.addEventListener('change', () => {
  const [file] = imageInput.files;
  preview.replaceChildren();
  preview.hidden = true;
  if (!file) return;
  const image = document.createElement('img');
  image.alt = 'Selected food image preview';
  image.src = URL.createObjectURL(file);
  image.onload = () => URL.revokeObjectURL(image.src);
  preview.append(image);
  preview.hidden = false;
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = document.querySelector('#question').value.trim();
  if (!question) {
    status.textContent = 'Enter a nutrition question or description.';
    return;
  }
  result.hidden = true;
  status.textContent = 'Retrieving evidence and preparing your response…';
  submit.disabled = true;
  try {
    const response = await fetch('/api/analyze', { method: 'POST', body: new FormData(form) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error?.message || 'Unable to analyze this request.');
    renderResult(payload);
    status.textContent = '';
  } catch (error) {
    status.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

function renderResult(payload) {
  document.querySelector('#mode').textContent = payload.mode === 'model-assisted'
    ? 'Model-assisted, evidence-grounded' : 'Evidence-only fallback';
  document.querySelector('#assessment').textContent = payload.assessment;
  document.querySelector('#limitations').textContent = payload.limitations.join(' ');
  const evidence = document.querySelector('#evidence');
  evidence.replaceChildren();
  if (!payload.evidence.length) {
    const item = document.createElement('li');
    item.textContent = 'No relevant local source was retrieved.';
    evidence.append(item);
  }
  for (const source of payload.evidence) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = source.url;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = source.title;
    item.append(link, document.createTextNode(` — ${source.excerpt}`));
    evidence.append(item);
  }
  result.hidden = false;
}
