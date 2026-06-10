// WebSocket connection
let ws = null;
let isConnected = false;

// DOM elements
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const statusElement = document.getElementById('status');
const robotAvatar = document.getElementById('robotAvatar');

// Connect to WebSocket
function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        isConnected = true;
        statusElement.textContent = 'Online';
        statusElement.classList.add('online');
        console.log('Connected to Buddy!');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onclose = () => {
        isConnected = false;
        statusElement.textContent = 'Disconnected - Reconnecting...';
        statusElement.classList.remove('online');
        // Reconnect after 2 seconds
        setTimeout(connect, 2000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Audio player
let audioPlayer = new Audio();
let voiceEnabled = true;

// Handle incoming messages
function handleMessage(data) {
    if (data.type === 'message') {
        addMessage(data.content, data.role, data.actions);

        // Animate robot based on actions
        if (data.actions && data.actions.length > 0) {
            animateRobot(data.actions);
        }

        // Play audio if available
        if (data.audio && voiceEnabled) {
            playAudio(data.audio);
        }
    } else if (data.type === 'system') {
        addSystemMessage(data.content);
        // Play audio for system messages too (voice change confirmation)
        if (data.audio && voiceEnabled) {
            playAudio(data.audio);
        }
    } else if (data.type === 'voices') {
        // Could update dropdown dynamically, but we hardcoded it
        console.log('Available voices:', data.voices);
    }
}

// Play base64 encoded audio
function playAudio(base64Audio) {
    try {
        audioPlayer.src = `data:audio/mp3;base64,${base64Audio}`;

        // Start talking animation
        startTalking();

        audioPlayer.onended = () => {
            stopTalking();
        };

        audioPlayer.play().catch(e => {
            console.log('Audio autoplay blocked, click to enable');
            stopTalking();
        });
    } catch (e) {
        console.error('Audio playback error:', e);
        stopTalking();
    }
}

// Toggle voice
function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voiceBtn');
    if (btn) {
        btn.textContent = voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off';
    }
}

// Change voice/language
function changeVoice(voiceKey) {
    if (!isConnected) return;

    ws.send(JSON.stringify({
        type: 'set_voice',
        voice: voiceKey
    }));
}

// Add a chat message
function addMessage(content, role, actions = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user' : 'assistant'}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    if (role === 'user') {
        avatar.textContent = '👤';
    } else {
        // Create mini animated Buddy avatar
        avatar.innerHTML = `
            <div class="mini-buddy" id="miniBuddy${Date.now()}">
                <div class="mini-antenna left"></div>
                <div class="mini-antenna right"></div>
                <div class="mini-face">
                    <div class="mini-eye left"></div>
                    <div class="mini-eye right"></div>
                </div>
            </div>
        `;
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    // Add action tags if present
    if (actions && actions.length > 0) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        actions.forEach(action => {
            const tag = document.createElement('span');
            tag.className = 'action-tag';
            tag.textContent = formatAction(action);
            actionsDiv.appendChild(tag);
        });
        contentDiv.appendChild(actionsDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

// Add system message
function addSystemMessage(content) {
    const div = document.createElement('div');
    div.className = 'system-message';
    div.textContent = content;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

// Add typing indicator
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.innerHTML = '<span></span><span></span><span></span>';

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(typing);
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

// Format action name for display
function formatAction(action) {
    const actionMap = {
        'nod': '✓ Nodding',
        'shake': '✗ Shaking head',
        'look_up': '👆 Looking up',
        'look_down': '👇 Looking down',
        'perk_antennas': '📡 Perking up',
        'droop_antennas': '😔 Drooping',
        'spin': '🔄 Spinning',
        'curious': '🤔 Curious tilt'
    };
    return actionMap[action] || action;
}

// Animate robot avatar based on actions
function animateRobot(actions) {
    // Reset classes
    robotAvatar.className = 'robot-avatar';

    actions.forEach(action => {
        if (action === 'perk_antennas') {
            robotAvatar.classList.add('perk');
        } else if (action === 'droop_antennas') {
            robotAvatar.classList.add('droop');
        } else if (action === 'curious') {
            robotAvatar.classList.add('curious');
        }
    });

    // Reset after animation
    setTimeout(() => {
        robotAvatar.className = 'robot-avatar';
    }, 2000);

    // Also animate floating buddy
    animateFloatingBuddy(actions);
}

// Animate the floating Buddy avatar
function animateFloatingBuddy(actions) {
    const floatingBuddy = document.getElementById('floatingBuddy');
    if (!floatingBuddy) return;

    // Reset classes
    floatingBuddy.className = 'floating-buddy';

    actions.forEach(action => {
        if (action === 'perk_antennas' || action === 'look_up' || action === 'spin') {
            floatingBuddy.classList.add('excited');
        } else if (action === 'droop_antennas' || action === 'look_down') {
            floatingBuddy.classList.add('sad');
        }
    });

    // Reset after animation
    setTimeout(() => {
        floatingBuddy.className = 'floating-buddy';
    }, 3000);
}

// Make buddy talk while audio plays
function startTalking() {
    const floatingBuddy = document.getElementById('floatingBuddy');
    if (floatingBuddy) {
        floatingBuddy.classList.add('talking');
    }
}

function stopTalking() {
    const floatingBuddy = document.getElementById('floatingBuddy');
    if (floatingBuddy) {
        floatingBuddy.classList.remove('talking');
    }
}

// ---------------------------------------------------------------
// Voice input via Web Speech API (Chrome/Edge)
// ---------------------------------------------------------------
let recognition = null;
let isListening = false;
let currentLang = 'en-US';
let autoListenAfterReply = true;

function initSpeechRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        document.getElementById('micHint').textContent =
            '⚠️ Voice input requires Chrome or Edge';
        document.getElementById('micBtn').disabled = true;
        return;
    }
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = currentLang;

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('micBtn').classList.add('listening');
        document.getElementById('micHint').textContent = '🎙️ Listening… click again to stop';
        document.getElementById('liveTranscript').textContent = '';
    };

    recognition.onresult = (event) => {
        let final = '';
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript;
            if (event.results[i].isFinal) final += t;
            else interim += t;
        }
        document.getElementById('liveTranscript').textContent = interim || final;
        if (final.trim()) sendVoiceText(final.trim());
    };

    recognition.onerror = (event) => {
        document.getElementById('micHint').textContent =
            `Mic error: ${event.error}. Click to try again.`;
        stopListening();
    };

    recognition.onend = () => {
        stopListening();
    };
}

function startListening() {
    if (!recognition || isListening) return;
    try {
        recognition.lang = currentLang;
        recognition.start();
    } catch (e) {
        console.error('Recognition start failed:', e);
    }
}

function stopListening() {
    isListening = false;
    document.getElementById('micBtn').classList.remove('listening');
    document.getElementById('micHint').textContent = 'Click the mic and talk to Buddy';
    if (recognition) {
        try { recognition.stop(); } catch (e) {}
    }
}

function toggleListening() {
    if (isListening) stopListening();
    else startListening();
}

function sendVoiceText(text) {
    if (!isConnected) return;
    addMessage(text, 'user');
    showTyping();
    document.getElementById('liveTranscript').textContent = '';
    ws.send(JSON.stringify({ type: 'chat', message: text }));
}

// ---------------------------------------------------------------
// Quick action buttons still work — they bypass STT
// ---------------------------------------------------------------
function sendQuickMessage(message) {
    if (!isConnected) return;
    addMessage(message, 'user');
    showTyping();
    ws.send(JSON.stringify({ type: 'chat', message: message }));
}

function resetChat() {
    if (!isConnected) return;
    ws.send(JSON.stringify({ type: 'reset' }));
    messagesContainer.innerHTML = '';
}

function scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ---------------------------------------------------------------
// Auto-listen after Buddy finishes speaking (natural conversation)
// ---------------------------------------------------------------
const _origPlayAudio = playAudio;
playAudio = function(b64) {
    _origPlayAudio(b64);
    const prevEnd = audioPlayer.onended;
    audioPlayer.onended = () => {
        if (prevEnd) prevEnd();
        if (autoListenAfterReply) {
            setTimeout(() => startListening(), 400);
        }
    };
};

// Update recognition language when user changes voice
const _origChangeVoice = changeVoice;
changeVoice = function(voiceKey) {
    _origChangeVoice(voiceKey);
    // map voice prefix → BCP-47 lang for SpeechRecognition
    const langMap = {
        'ar-iq': 'ar-IQ', 'ar-eg': 'ar-EG', 'ar-sa': 'ar-SA',
        'en-funny': 'en-IE', 'en-aussie': 'en-AU',
        'en-us': 'en-US', 'en-gb': 'en-GB'
    };
    for (const [prefix, lang] of Object.entries(langMap)) {
        if (voiceKey.startsWith(prefix)) {
            currentLang = lang;
            if (recognition) recognition.lang = lang;
            break;
        }
    }
};

// Override handleMessage to hide typing
const originalHandleMessage = handleMessage;
handleMessage = function(data) {
    hideTyping();
    originalHandleMessage(data);
};

// Connect on page load
document.addEventListener('DOMContentLoaded', () => {
    connect();
    initSpeechRecognition();
});
