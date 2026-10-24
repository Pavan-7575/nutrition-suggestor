// In-memory state (resets on page reload)
let sessions = [
  {
    id: 'session-1',
    title: 'New Chat',
    messages: []
  }
];

let activeSessionId = 'session-1';
let currentImageFile = null;
let currentImageBase64 = null;

// Views & Navigation DOM
const landingView = document.querySelector('#landing-view');
const chatAppView = document.querySelector('#chat-app-view');
const navHomeBtn = document.querySelector('#nav-home-btn');
const navAssistantBtn = document.querySelector('#nav-assistant-btn');
const navGetStartedBtn = document.querySelector('#nav-get-started-btn');
const navBrandBtn = document.querySelector('#nav-brand-btn');
const heroStartBtn = document.querySelector('#hero-start-btn');
const heroLearnBtn = document.querySelector('#hero-learn-btn');

// Chat DOM Elements
const sidebar = document.querySelector('#sidebar');
const toggleSidebarBtn = document.querySelector('#toggle-sidebar-btn');
const newChatBtn = document.querySelector('#new-chat-btn');
const chatHistoryList = document.querySelector('#chat-history-list');
const chatThread = document.querySelector('#chat-thread');
const chatScrollArea = document.querySelector('#chat-scroll-area');
const chatTitle = document.querySelector('#chat-title');
const welcomeHero = document.querySelector('#welcome-hero');

const userInput = document.querySelector('#user-input');
const sendBtn = document.querySelector('#send-btn');
const fileInput = document.querySelector('#file-input');
const cameraInput = document.querySelector('#camera-input');
const uploadFileBtn = document.querySelector('#upload-file-btn');
const cameraBtn = document.querySelector('#camera-btn');
const attachmentPreview = document.querySelector('#attachment-preview');
const previewImg = document.querySelector('#preview-img');
const clearAttachBtn = document.querySelector('#clear-attach-btn');

// View Switching Functions
function showLandingView() {
  landingView.style.display = 'flex';
  chatAppView.style.display = 'none';
  navHomeBtn.classList.add('active');
  navAssistantBtn.classList.remove('active');
}

function showChatView() {
  landingView.style.display = 'none';
  chatAppView.style.display = 'block';
  navHomeBtn.classList.remove('active');
  navAssistantBtn.classList.add('active');
  userInput.focus();
}

// Nav Click Listeners
navHomeBtn.addEventListener('click', showLandingView);
navBrandBtn.addEventListener('click', showLandingView);
navAssistantBtn.addEventListener('click', showChatView);
navGetStartedBtn.addEventListener('click', showChatView);
heroStartBtn.addEventListener('click', showChatView);
heroLearnBtn.addEventListener('click', () => {
  document.querySelector('.features-grid').scrollIntoView({ behavior: 'smooth' });
});

// Sidebar toggle
toggleSidebarBtn.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
});

// Auto-expand textarea
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = `${Math.min(userInput.scrollHeight, 180)}px`;
  updateSendButtonState();
});

function updateSendButtonState() {
  const hasText = Boolean(userInput.value.trim());
  const hasImage = Boolean(currentImageFile);
  sendBtn.disabled = !(hasText || hasImage);
}

// Upload file button trigger
uploadFileBtn.addEventListener('click', () => {
  fileInput.click();
});

// Camera button trigger
cameraBtn.addEventListener('click', () => {
  cameraInput.click();
});

// Handle file selection (upload & camera)
[fileInput, cameraInput].forEach((input) => {
  input.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file) {
      currentImageFile = file;
      const reader = new FileReader();
      reader.onload = () => {
        currentImageBase64 = reader.result;
        previewImg.src = reader.result;
        attachmentPreview.style.display = 'flex';
        updateSendButtonState();
      };
      reader.readAsDataURL(file);
    }
  });
});

// Clear attached image
clearAttachBtn.addEventListener('click', clearAttachment);

function clearAttachment() {
  currentImageFile = null;
  currentImageBase64 = null;
  attachmentPreview.style.display = 'none';
  previewImg.removeAttribute('src');
  fileInput.value = '';
  cameraInput.value = '';
  updateSendButtonState();
}

// New Chat Button
newChatBtn.addEventListener('click', () => {
  const newId = `session-${Date.now()}`;
  sessions.unshift({
    id: newId,
    title: 'New Chat',
    messages: []
  });
  activeSessionId = newId;
  clearAttachment();
  renderHistoryList();
  renderActiveChat();
});

// Prompt Chips trigger
document.querySelectorAll('.prompt-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    const promptText = chip.getAttribute('data-prompt');
    userInput.value = promptText;
    userInput.dispatchEvent(new Event('input'));
    sendMessage();
  });
});

// Enter key to send (Shift+Enter for newline)
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled) {
      sendMessage();
    }
  }
});

sendBtn.addEventListener('click', sendMessage);

async function sendMessage() {
  const query = userInput.value.trim();
  if (!query && !currentImageFile) return;

  const currentSession = sessions.find((s) => s.id === activeSessionId);
  if (!currentSession) return;

  // Set chat title from first user message
  if (currentSession.messages.length === 0 && query) {
    currentSession.title = query.length > 28 ? `${query.substring(0, 28)}…` : query;
    renderHistoryList();
    chatTitle.textContent = currentSession.title;
  }

  // Push user message
  const userMsg = {
    sender: 'user',
    text: query || 'Analyze this food item.',
    image: currentImageBase64
  };
  currentSession.messages.push(userMsg);

  // Prepare FormData
  const formData = new FormData();
  formData.append('question', query || 'Analyze this food item.');
  if (currentImageFile) {
    formData.append('image', currentImageFile);
  }

  // Clear composer
  userInput.value = '';
  userInput.style.height = 'auto';
  clearAttachment();
  renderActiveChat();

  // Add temporary loading indicator
  const loadingMsg = {
    sender: 'bot',
    isLoading: true
  };
  currentSession.messages.push(loadingMsg);
  renderActiveChat();

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    // Remove loading msg
    currentSession.messages.pop();

    if (!res.ok) {
      throw new Error(data.error?.message || 'Server error occurred.');
    }

    currentSession.messages.push({
      sender: 'bot',
      text: data.assessment || 'No assessment returned.',
      evidence: data.evidence || [],
      limitations: data.limitations || []
    });
  } catch (err) {
    currentSession.messages.pop();
    currentSession.messages.push({
      sender: 'bot',
      text: `⚠️ Analysis failed: ${err.message}. Please check if Ollama is running with minicpm-v.`,
      evidence: [],
      limitations: []
    });
  }

  renderActiveChat();
}

function renderHistoryList() {
  chatHistoryList.innerHTML = '';
  sessions.forEach((session) => {
    const item = document.createElement('div');
    item.className = `history-item ${session.id === activeSessionId ? 'active' : ''}`;
    item.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span>${escapeHtml(session.title)}</span>
    `;
    item.addEventListener('click', () => {
      activeSessionId = session.id;
      renderHistoryList();
      renderActiveChat();
    });
    chatHistoryList.appendChild(item);
  });
}

function renderActiveChat() {
  const currentSession = sessions.find((s) => s.id === activeSessionId);
  if (!currentSession) return;

  chatTitle.textContent = currentSession.title;

  if (currentSession.messages.length === 0) {
    chatThread.innerHTML = '';
    chatThread.appendChild(welcomeHero);
    return;
  }

  chatThread.innerHTML = '';

  currentSession.messages.forEach((msg) => {
    const row = document.createElement('div');
    row.className = `message-row ${msg.sender}`;

    if (msg.sender === 'bot') {
      row.innerHTML = `
        <div class="message-avatar bot">🥗</div>
        <div class="message-body">
          <div class="bubble">
            ${msg.isLoading ? 'Thinking & analyzing nutrition evidence…' : formatBotText(msg.text)}
            ${renderEvidence(msg.evidence)}
            ${renderLimitations(msg.limitations)}
          </div>
        </div>
      `;
    } else {
      row.innerHTML = `
        <div class="message-body">
          ${msg.image ? `<img src="${msg.image}" alt="Attached meal" class="chat-image">` : ''}
          <div class="bubble">${escapeHtml(msg.text)}</div>
        </div>
      `;
    }

    chatThread.appendChild(row);
  });

  chatScrollArea.scrollTop = chatScrollArea.scrollHeight;
}

function renderEvidence(evidence) {
  if (!evidence || evidence.length === 0) return '';
  let html = '<div class="evidence-card"><div class="evidence-header">📚 VERIFIED CLINICAL EVIDENCE</div>';
  evidence.forEach((item) => {
    html += `
      <div style="margin-bottom: 0.4rem;">
        <a href="${item.url}" target="_blank" rel="noreferrer" class="evidence-link">🔗 ${escapeHtml(item.title)}</a>
        <div class="evidence-desc">${escapeHtml(item.excerpt)}</div>
      </div>
    `;
  });
  html += '</div>';
  return html;
}

function renderLimitations(limitations) {
  if (!limitations || limitations.length === 0) return '';
  return `<div class="notice-pill">* ${escapeHtml(limitations[0])}</div>`;
}

function formatBotText(text) {
  return escapeHtml(text).replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Initial render
renderHistoryList();
renderActiveChat();
