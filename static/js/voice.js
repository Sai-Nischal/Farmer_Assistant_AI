document.addEventListener('DOMContentLoaded', () => {
    const voiceBtn = document.getElementById('btn-voice');
    const queryInput = document.getElementById('chat-query-input');
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    
    // Check if voice is supported in browser
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        // Detect page language or fallback to Telugu
        const userLang = document.body.dataset.lang || 'te';
        recognition.lang = userLang === 'te' ? 'te-IN' : 'en-IN';

        recognition.onstart = () => {
            isListening = true;
            if (voiceBtn) {
                voiceBtn.classList.add('listening');
                voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            }
            console.log("Speech recognition started...");
        };

        recognition.onend = () => {
            isListening = false;
            if (voiceBtn) {
                voiceBtn.classList.remove('listening');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            }
            console.log("Speech recognition ended.");
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log("Transcription result:", transcript);
            
            if (queryInput) {
                queryInput.value = transcript;
                // Auto submit form if input is written
                if (chatForm) {
                    submitChatQuery(transcript);
                }
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            alert("గొంతు వినడంలో సమస్య వచ్చింది. దయచేసి మళ్ళీ ప్రయత్నించండి. (Speech recognition error)");
        };
    } else {
        console.warn("Web Speech API is not supported in this browser. Local speech recognition is disabled.");
    }

    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            if (!recognition) {
                alert("మీ బ్రౌజర్ వాయిస్ రికగ్నిషన్ కి మద్దతు ఇవ్వదు. దయచేసి టైప్ చేయండి. (Voice recognition not supported)");
                return;
            }
            
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    }

    function submitChatQuery(query) {
        if (!query || query.trim() === "") return;
        
        // Clear input field
        if (queryInput) queryInput.value = "";

        // Add user message to UI
        appendMessage(query, 'user');
        
        // Append bot loading message
        const botLoadingId = appendMessage('<i class="fas fa-spinner fa-spin"></i> ఆలోచిస్తున్నాను (Thinking)...', 'bot');

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        })
        .then(res => res.json())
        .then(data => {
            // Remove loading
            const loadingMsg = document.getElementById(botLoadingId);
            if (loadingMsg) loadingMsg.remove();

            // Add bot reply to UI
            const replyText = data.reply_text;
            appendMessage(replyText, 'bot');

            // Auto-speak response if voice is enabled on profile
            const voiceEnabled = document.body.dataset.voice === 'true';
            if (voiceEnabled) {
                speakResponse(replyText);
            }
        })
        .catch(err => {
            const loadingMsg = document.getElementById(botLoadingId);
            if (loadingMsg) loadingMsg.remove();
            appendMessage("క్షమించండి, సర్వర్ కనెక్షన్ లో సమస్య వచ్చింది. (Connection issue)", 'bot');
            console.error("Chat API error:", err);
        });
    }

    function appendMessage(text, sender) {
        if (!chatMessages) return null;
        
        const msgDiv = document.createElement('div');
        const id = 'msg_' + Math.random().toString(36).substr(2, 9);
        msgDiv.id = id;
        msgDiv.className = `chat-msg chat-msg-${sender}`;
        msgDiv.innerHTML = text;
        chatMessages.appendChild(msgDiv);
        
        // Auto scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function speakResponse(text) {
        fetch('/api/voice-output', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, lang: document.body.dataset.lang || 'te' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                audio.play();
            }
        })
        .catch(err => {
            console.error("Speak voice output failure:", err);
        });
    }

    // Direct chat form submit handler
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = queryInput.value;
            submitChatQuery(query);
        });
    }
});
