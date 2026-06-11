/* ==========================================================
   Buddy — companion robot front-end
   Voice-first. Arabic-default. Presence orb instead of avatar.
   Preserves: WS to /ws, Web Speech API, base64 mp3 autoplay,
              auto-listen after reply, voice picker, reset, quick actions.
   ========================================================== */

// ----- State -----
const state = {
    ws: null,
    connected: false,
    voiceEnabled: true,
    isListening: false,
    isSpeaking: false,
    currentVoice: 'ar-iq-female',
    currentLang: 'ar-IQ',
    uiLang: 'ar',
    autoListenAfterReply: true,
    voices: null,
    exchanges: [], // {role, content, actions?, el}
    maxExchanges: 6, // 3 turns ≈ 6 cards
};

const audioPlayer = new Audio();
let recognition = null;

// ----- Voice catalog (static; server sends authoritative VOICES on connect) -----
const VOICE_CATALOG = [
    { key: 'ar-iq-female', name: { ar: 'رنا', en: 'Rana' },     meta: { ar: 'عراقية',  en: 'Iraqi Arabic' },    lang: 'ar-IQ' },
    { key: 'ar-iq-male',   name: { ar: 'باسل', en: 'Bassel' },  meta: { ar: 'عراقي',   en: 'Iraqi Arabic' },    lang: 'ar-IQ' },
    { key: 'ar-eg-female', name: { ar: 'سلمى', en: 'Salma' },   meta: { ar: 'مصرية',   en: 'Egyptian Arabic' }, lang: 'ar-EG' },
    { key: 'ar-eg-male',   name: { ar: 'شاكر', en: 'Shakir' },  meta: { ar: 'مصري',    en: 'Egyptian Arabic' }, lang: 'ar-EG' },
    { key: 'ar-sa-female', name: { ar: 'زارا', en: 'Zara' },    meta: { ar: 'خليجية',  en: 'Saudi Arabic' },    lang: 'ar-SA' },
    { key: 'ar-sa-male',   name: { ar: 'حمد',  en: 'Hamed' },   meta: { ar: 'خليجي',   en: 'Saudi Arabic' },    lang: 'ar-SA' },
    { key: 'en-us-female', name: { ar: 'آريا', en: 'Aria' },    meta: { ar: 'أمريكية', en: 'US English' },       lang: 'en-US' },
    { key: 'en-us-male',   name: { ar: 'غاي',  en: 'Guy' },     meta: { ar: 'أمريكي',  en: 'US English' },       lang: 'en-US' },
    { key: 'en-gb-female', name: { ar: 'سونيا', en: 'Sonia' },  meta: { ar: 'بريطانية', en: 'UK English' },      lang: 'en-GB' },
    { key: 'en-gb-male',   name: { ar: 'رايان', en: 'Ryan' },   meta: { ar: 'بريطاني',  en: 'UK English' },      lang: 'en-GB' },
    { key: 'en-aussie',    name: { ar: 'ناتاشا', en: 'Natasha' }, meta: { ar: 'أسترالية', en: 'Australian' },    lang: 'en-AU' },
    { key: 'en-funny',     name: { ar: 'كونور', en: 'Connor' }, meta: { ar: 'أيرلندي',  en: 'Irish' },           lang: 'en-IE' },
];

// ----- i18n -----
const STRINGS = {
    ar: {
        brand: 'بَدي',
        connecting: 'يتصل…',
        online: 'متصل',
        offline: 'غير متصل',
        reconnecting: 'يحاول الاتصال…',
        tapToTalk: 'اضغط للحديث مع بَدي',
        listening: 'يسمعك… اضغط لتوقف',
        speaking: 'يتحدث بَدي',
        thinking: 'يفكّر…',
        micUnsupported: 'يحتاج مايك Chrome أو Edge',
        settings: 'الإعدادات',
        voice: 'الصوت',
        interface: 'لغة الواجهة',
        langNote: 'تتبع الواجهة لغة الصوت المختار.',
        reset: 'امسح المحادثة',
        madeIn: 'صُنع في أربيل',
        suggest1: 'احكِ لي نكتة',
        suggest2: 'كيف حالك اليوم؟',
        suggest3: 'لِف لفّة فرح',
    },
    en: {
        brand: 'Buddy',
        connecting: 'Connecting…',
        online: 'Online',
        offline: 'Offline',
        reconnecting: 'Reconnecting…',
        tapToTalk: 'Tap to talk to Buddy',
        listening: 'Listening… tap to stop',
        speaking: 'Buddy is speaking',
        thinking: 'Thinking…',
        micUnsupported: 'Voice needs Chrome or Edge',
        settings: 'Settings',
        voice: 'Voice',
        interface: 'Interface language',
        langNote: 'The interface follows the selected voice.',
        reset: 'Clear conversation',
        madeIn: 'Made in Erbil',
        suggest1: 'Tell me a joke',
        suggest2: 'How are you?',
        suggest3: 'Do a happy spin',
    },
};

// ----- DOM -----
const $ = (id) => document.getElementById(id);
const dom = {
    body: document.body,
    status: $('status'),
    statusPill: $('statusPill'),
    micBtn: $('micBtn'),
    micHint: $('micHint'),
    transcript: $('liveTranscript'),
    exchange: $('exchange'),
    suggestions: $('suggestions'),
    settingsBtn: $('settingsBtn'),
    closeSheet: $('closeSheet'),
    sheet: $('settingsSheet'),
    sheetBackdrop: $('sheetBackdrop'),
    voiceGrid: $('voiceGrid'),
    resetBtn: $('resetBtn'),
    langToggle: document.querySelectorAll('.lang-opt'),
};

// ----- Presence state -----
function setState(s) {
    dom.body.dataset.state = s;
    const t = STRINGS[state.uiLang];
    if (s === 'listening')      dom.micHint.textContent = t.listening;
    else if (s === 'speaking')  dom.micHint.textContent = t.speaking;
    else if (s === 'thinking')  dom.micHint.textContent = t.thinking;
    else                        dom.micHint.textContent = t.tapToTalk;
}

function setActionMood(mood) {
    if (!mood) {
        delete dom.body.dataset.action;
        return;
    }
    dom.body.dataset.action = mood;
    setTimeout(() => { delete dom.body.dataset.action; }, 2400);
}

// ----- i18n + direction -----
function applyLang(lang) {
    state.uiLang = lang;
    const html = document.documentElement;
    html.lang = lang;
    html.dir = lang === 'ar' ? 'rtl' : 'ltr';

    const t = STRINGS[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (t[key]) el.textContent = t[key];
    });

    // Update suggestion chips with localized labels (data-ar / data-en)
    document.querySelectorAll('.chip').forEach(chip => {
        const v = chip.dataset[lang];
        if (v) chip.textContent = v;
    });

    // Status text based on state
    if (state.connected) dom.status.textContent = t.online;

    // Active lang toggle
    dom.langToggle.forEach(b => {
        b.classList.toggle('is-active', b.dataset.lang === lang);
    });

    // Refresh voice grid labels
    renderVoiceGrid();
    setState(dom.body.dataset.state || 'idle');
}

// ----- WebSocket -----
function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    state.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    state.ws.onopen = () => {
        state.connected = true;
        dom.statusPill.classList.add('is-online');
        dom.status.textContent = STRINGS[state.uiLang].online;
    };

    state.ws.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch { return; }
        handleMessage(data);
    };

    state.ws.onclose = () => {
        const wasConnected = state.connected;
        state.connected = false;
        dom.statusPill.classList.remove('is-online');
        dom.status.textContent = STRINGS[state.uiLang].reconnecting;
        // Only show a card if we dropped mid-conversation (had been connected).
        if (wasConnected) {
            const msg = state.uiLang === 'ar' ? 'انقطع الاتصال. تتم إعادة المحاولة…' : 'Reconnecting…';
            addCard('system', msg);
        }
        setTimeout(connect, 2000);
    };

    state.ws.onerror = (err) => console.error('WS error:', err);
}

function handleMessage(data) {
    if (data.type === 'message') {
        // Buddy's reply
        if (dom.body.dataset.state === 'thinking') setState('idle');
        addCard(data.role || 'assistant', data.content, data.actions || []);
        if (data.actions && data.actions.length) animateActions(data.actions);
        if (data.audio && state.voiceEnabled) playAudio(data.audio);
    } else if (data.type === 'system') {
        addCard('system', data.content);
        if (data.audio && state.voiceEnabled) playAudio(data.audio);
    } else if (data.type === 'voices') {
        state.voices = data.voices;
        renderVoiceGrid();
    }
}

// ----- Audio playback -----
function playAudio(b64) {
    try {
        audioPlayer.src = `data:audio/mp3;base64,${b64}`;
        state.isSpeaking = true;
        setState('speaking');

        audioPlayer.onended = () => {
            state.isSpeaking = false;
            setState('idle');
            if (state.autoListenAfterReply && recognition && !state.isListening) {
                setTimeout(() => startListening(), 380);
            }
        };

        audioPlayer.play().catch(e => {
            console.log('Audio autoplay blocked:', e);
            state.isSpeaking = false;
            setState('idle');
        });
    } catch (e) {
        console.error('Audio playback error:', e);
        state.isSpeaking = false;
        setState('idle');
    }
}

// ----- Exchange cards -----
function addCard(role, content, actions = []) {
    const card = document.createElement('div');
    card.className = 'card card--' + (role === 'user' ? 'user' : role === 'system' ? 'system' : 'buddy');
    card.textContent = content;

    // Set lang/dir based on script detection so screen readers + fonts pick the right one.
    if (typeof content === 'string' && content.length) {
        const hasArabic = /[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/.test(content);
        if (hasArabic) {
            card.lang = 'ar';
            card.dir = 'rtl';
        } else if (/[A-Za-z]/.test(content)) {
            card.lang = 'en';
            card.dir = 'ltr';
        }
    }

    if (actions && actions.length && role !== 'system') {
        const wrap = document.createElement('div');
        wrap.className = 'card-actions';
        actions.forEach(a => {
            const tag = document.createElement('span');
            tag.className = 'action-tag';
            tag.textContent = formatAction(a);
            wrap.appendChild(tag);
        });
        card.appendChild(wrap);
    }

    dom.exchange.appendChild(card);
    state.exchanges.push({ role, el: card });

    // Fade older
    const visible = state.exchanges.slice(-state.maxExchanges);
    state.exchanges.forEach((ex, idx) => {
        const distFromEnd = state.exchanges.length - 1 - idx;
        ex.el.classList.remove('fading', 'faded');
        if (distFromEnd >= state.maxExchanges) ex.el.remove();
        else if (distFromEnd >= 4) ex.el.classList.add('faded');
        else if (distFromEnd >= 2) ex.el.classList.add('fading');
    });
    state.exchanges = state.exchanges.filter(ex => ex.el.isConnected);

    // Scroll to newest
    requestAnimationFrame(() => {
        dom.exchange.scrollTop = dom.exchange.scrollHeight;
    });
}

const ACTION_LABELS = {
    nod:             { ar: 'يومئ', en: 'Nodding' },
    shake:           { ar: 'يهز رأسه',   en: 'Shaking head' },
    look_up:         { ar: 'ينظر فوق',   en: 'Looking up' },
    look_down:       { ar: 'ينظر تحت',   en: 'Looking down' },
    perk_antennas:   { ar: 'منتبه',      en: 'Perked up' },
    droop_antennas:  { ar: 'حزين',       en: 'Drooping' },
    spin:            { ar: 'يلف',        en: 'Spinning' },
    curious:         { ar: 'فضولي',      en: 'Curious' },
};

function formatAction(a) {
    const l = ACTION_LABELS[a];
    if (!l) return a;
    return l[state.uiLang] || l.en;
}

function animateActions(actions) {
    let mood = null;
    actions.forEach(a => {
        if (['perk_antennas', 'look_up', 'spin', 'nod'].includes(a)) mood = 'excited';
        else if (['droop_antennas', 'look_down'].includes(a)) mood = 'sad';
    });
    if (mood) setActionMood(mood);
}

// ----- Suggestions / quick chips -----
function sendQuickMessage(message) {
    if (!state.connected) return;
    addCard('user', message);
    setState('thinking');
    state.ws.send(JSON.stringify({ type: 'chat', message }));
}

// ----- Voice grid -----
function renderVoiceGrid() {
    const grid = dom.voiceGrid;
    if (!grid) return;
    grid.innerHTML = '';
    VOICE_CATALOG.forEach(v => {
        const b = document.createElement('button');
        b.className = 'voice-opt' + (v.key === state.currentVoice ? ' is-active' : '');
        b.dataset.key = v.key;
        const name = document.createElement('span');
        name.className = 'voice-opt-name';
        name.textContent = v.name[state.uiLang] || v.name.en;
        const meta = document.createElement('span');
        meta.className = 'voice-opt-meta';
        meta.textContent = v.meta[state.uiLang] || v.meta.en;
        b.appendChild(name);
        b.appendChild(meta);
        b.addEventListener('click', () => selectVoice(v.key));
        grid.appendChild(b);
    });
}

function selectVoice(voiceKey) {
    state.currentVoice = voiceKey;
    const v = VOICE_CATALOG.find(x => x.key === voiceKey);
    if (v) {
        state.currentLang = v.lang;
        if (recognition) recognition.lang = v.lang;
        // Switch UI lang based on voice lang prefix
        const newUiLang = v.lang.startsWith('ar') ? 'ar' : 'en';
        if (newUiLang !== state.uiLang) applyLang(newUiLang);
        else renderVoiceGrid();
    }
    if (state.connected) {
        state.ws.send(JSON.stringify({ type: 'set_voice', voice: voiceKey }));
    }
}

// ----- Settings sheet -----
function openSheet() {
    dom.sheet.hidden = false;
    dom.sheetBackdrop.hidden = false;
}

function closeSheet() {
    dom.sheet.hidden = true;
    dom.sheetBackdrop.hidden = true;
}

// ----- Reset -----
function resetChat() {
    if (!state.connected) return;
    state.ws.send(JSON.stringify({ type: 'reset' }));
    dom.exchange.innerHTML = '';
    state.exchanges = [];
    closeSheet();
}

// ----- Server-side Whisper STT (replaces browser Web Speech) -----
// Records mic audio via MediaRecorder, POSTs to /api/transcribe, gets text back.
// Includes voice-activity detection (VAD) so it auto-stops after silence,
// the way Web Speech used to.
let mediaRecorder = null;
let audioChunks = [];
let mediaStream = null;
let vadCtx = null;        // AudioContext for silence detection
let vadAnalyser = null;
let vadSilenceMs = 0;     // accumulated silence duration
let vadRafId = null;
const VAD_SILENCE_THRESHOLD = 0.012;  // RMS — below = silence
const VAD_HANG_MS = 1500;             // ms of silence before auto-stop
const VAD_MIN_SPEECH_MS = 600;        // require at least this much speech first
let vadSpeechMs = 0;
let vadStartedAt = 0;

async function initRecorder() {
    if (mediaStream) return true;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        dom.micHint.textContent = STRINGS[state.uiLang].micUnsupported;
        dom.micBtn.disabled = true;
        return false;
    }
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        });
        return true;
    } catch (e) {
        console.error('Mic permission denied:', e);
        dom.micHint.textContent = STRINGS[state.uiLang].micUnsupported;
        dom.micBtn.disabled = true;
        return false;
    }
}

async function startListening() {
    if (state.isListening || state.isSpeaking) return;
    const ok = await initRecorder();
    if (!ok) return;

    audioChunks = [];
    // Prefer opus webm — small + Whisper handles it via ffmpeg.
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
    try {
        mediaRecorder = new MediaRecorder(mediaStream, { mimeType: mime });
    } catch {
        mediaRecorder = new MediaRecorder(mediaStream);
    }
    mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.onstop = onRecordingStop;
    mediaRecorder.start();
    state.isListening = true;
    setState('listening');
    startVad();
}

// Voice-activity detection — auto-stop after ~1.5s of silence (once they've spoken).
function startVad() {
    try {
        if (!vadCtx) {
            const AC = window.AudioContext || window.webkitAudioContext;
            vadCtx = new AC();
        }
        const src = vadCtx.createMediaStreamSource(mediaStream);
        vadAnalyser = vadCtx.createAnalyser();
        vadAnalyser.fftSize = 1024;
        src.connect(vadAnalyser);
        vadSilenceMs = 0;
        vadSpeechMs = 0;
        vadStartedAt = performance.now();
        const buf = new Float32Array(vadAnalyser.fftSize);
        let lastTick = performance.now();

        const tick = () => {
            if (!state.isListening) return;
            vadAnalyser.getFloatTimeDomainData(buf);
            // RMS volume
            let sum = 0;
            for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
            const rms = Math.sqrt(sum / buf.length);

            const now = performance.now();
            const dt = now - lastTick;
            lastTick = now;

            if (rms > VAD_SILENCE_THRESHOLD) {
                vadSpeechMs += dt;
                vadSilenceMs = 0;
            } else {
                vadSilenceMs += dt;
            }

            // Auto-stop only after they've actually talked
            if (vadSpeechMs > VAD_MIN_SPEECH_MS && vadSilenceMs > VAD_HANG_MS) {
                stopListening();
                return;
            }
            // Hard cap: 30s safety
            if (now - vadStartedAt > 30000) {
                stopListening();
                return;
            }
            vadRafId = requestAnimationFrame(tick);
        };
        vadRafId = requestAnimationFrame(tick);
    } catch (e) {
        console.warn('VAD unavailable:', e);
    }
}

function stopVad() {
    if (vadRafId) {
        cancelAnimationFrame(vadRafId);
        vadRafId = null;
    }
    if (vadAnalyser) {
        try { vadAnalyser.disconnect(); } catch {}
        vadAnalyser = null;
    }
}

function stopListening() {
    stopVad();
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        try { mediaRecorder.stop(); } catch {}
    }
    state.isListening = false;
}

async function onRecordingStop() {
    if (audioChunks.length === 0) {
        setState('idle');
        return;
    }
    const blob = new Blob(audioChunks, { type: mediaRecorder?.mimeType || 'audio/webm' });

    // Tiny clip (<0.3 sec) = probably a tap, ignore
    if (blob.size < 4000) {
        setState('idle');
        return;
    }

    setState('thinking');
    dom.transcript.textContent = STRINGS[state.uiLang].thinking;

    const form = new FormData();
    form.append('audio', blob, 'audio.webm');
    // Send language hint so Whisper doesn't misdetect a short "marhaba" as Thai.
    const langHint = (state.currentLang || 'ar-IQ').slice(0, 2);
    try {
        const res = await fetch('/api/transcribe?lang=' + encodeURIComponent(langHint), {
            method: 'POST', body: form,
        });
        const data = await res.json();
        if (data && data.error) {
            console.warn('STT error:', data.error);
            const msg = state.uiLang === 'ar'
                ? 'تعذر التعرف على الصوت. حاول مرة أخرى.'
                : "Couldn't transcribe audio. Please try again.";
            addCard('system', msg);
            setState('idle');
        } else if (data && data.text && data.text.trim()) {
            sendVoiceText(data.text.trim());
        } else {
            console.warn('STT empty:', data);
            const msg = state.uiLang === 'ar'
                ? 'لم أسمع شيئًا. اضغط وتحدث مجددًا.'
                : "I didn't hear anything. Tap and try again.";
            addCard('system', msg);
            setState('idle');
        }
    } catch (e) {
        console.error('STT request failed:', e);
        const msg = state.uiLang === 'ar'
            ? 'فشل الاتصال بالخادم. حاول مرة أخرى.'
            : 'Server request failed. Please try again.';
        addCard('system', msg);
        setState('idle');
    }
}

function toggleListening() {
    // Tap-to-interrupt: if Buddy is speaking, stop playback and start listening.
    if (state.isSpeaking || dom.body.dataset.state === 'speaking') {
        try {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
        } catch (e) { /* ignore */ }
        state.isSpeaking = false;
        setState('idle');
        startListening();
        return;
    }
    if (state.isListening) stopListening();
    else startListening();
}

function sendVoiceText(text) {
    if (!state.connected) return;
    addCard('user', text);
    dom.transcript.textContent = '';
    setState('thinking');
    state.ws.send(JSON.stringify({ type: 'chat', message: text }));
}

// ----- Wire events -----
function wire() {
    dom.micBtn.addEventListener('click', toggleListening);

    dom.settingsBtn.addEventListener('click', openSheet);
    dom.closeSheet.addEventListener('click', closeSheet);
    dom.sheetBackdrop.addEventListener('click', closeSheet);
    // Big bottom "Done" button as a redundant escape hatch
    const doneBtn = document.getElementById('doneBtn');
    if (doneBtn) {
        doneBtn.addEventListener('click', closeSheet);
        doneBtn.textContent = state.uiLang === 'ar' ? 'تم' : 'Done';
    }

    dom.resetBtn.addEventListener('click', resetChat);

    dom.langToggle.forEach(btn => {
        btn.addEventListener('click', () => applyLang(btn.dataset.lang));
    });

    // Suggestion chips: send their localized text
    dom.suggestions.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const msg = chip.dataset[state.uiLang] || chip.textContent.trim();
            sendQuickMessage(msg);
        });
    });

    // Escape closes sheet
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !dom.sheet.hidden) closeSheet();
    });
}

// ----- Boot -----
document.addEventListener('DOMContentLoaded', () => {
    applyLang('ar');
    setState('idle');
    renderVoiceGrid();
    wire();
    connect();
    // initRecorder is lazy — runs on the first mic click so the permission
    // prompt happens in response to a user gesture (browser requirement).
});
