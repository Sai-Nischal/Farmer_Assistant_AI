document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('leaf-image-input');
    const captureBox = document.getElementById('capture-box');
    const loader = document.getElementById('loader-wrapper');
    const resultSection = document.getElementById('result-section');
    const uploadSection = document.getElementById('upload-section');

    // UI Elements inside result card
    const cropText = document.getElementById('res-crop');
    const conditionText = document.getElementById('res-condition');
    const confidenceMeter = document.getElementById('res-confidence-bar');
    const confidenceText = document.getElementById('res-confidence-val');
    const symptomsText = document.getElementById('res-symptoms');
    const organicTreatmentText = document.getElementById('res-organic');
    const chemicalTreatmentText = document.getElementById('res-chemical');
    const irrigationAdviceText = document.getElementById('res-irrigation');
    const sprayBadge = document.getElementById('res-spray-badge');
    const sprayText = document.getElementById('res-spray');
    const audioBtn = document.getElementById('play-advisory-voice');

    let latestAdvisoryReply = ""; // Holds the reply text for TTS playbacks

    if (captureBox && fileInput) {
        captureBox.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                uploadImage(file);
            }
        });
    }

    function uploadImage(file) {
        const formData = new FormData();
        formData.append('image', file);

        // UI transitions
        uploadSection.style.display = 'none';
        loader.style.display = 'block';
        if (resultSection) resultSection.style.display = 'none';

        fetch('/diagnose', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Server diagnosis request failed.");
            }
            return response.json();
        })
        .then(data => {
            loader.style.display = 'none';
            
            if (data.is_success) {
                // Populate results UI
                const diag = data.diagnosis;
                const adv = data.advisory;
                const weather = data.weather;
                const schemes = data.schemes;

                cropText.textContent = diag.crop_type || "N/A";
                conditionText.textContent = diag.likely_condition || "Healthy / Unknown";
                
                const confidence = diag.confidence || 0;
                confidenceText.textContent = `${confidence}%`;
                confidenceMeter.style.width = `${confidence}%`;

                // Update class colors based on confidence
                confidenceMeter.className = "progress-bar";
                if (confidence >= 75) {
                    confidenceMeter.classList.add("bg-success");
                } else if (confidence >= 50) {
                    confidenceMeter.classList.add("bg-warning");
                } else {
                    confidenceMeter.classList.add("bg-danger");
                }

                symptomsText.textContent = diag.symptoms_noted || "";
                
                // Advisory details
                organicTreatmentText.textContent = adv.organic_treatment || "";
                chemicalTreatmentText.textContent = adv.chemical_treatment || "";
                irrigationAdviceText.textContent = adv.irrigation_advice || "";
                
                // Spray status badge colors
                const sprayStatus = adv.spray_status || "yellow";
                sprayBadge.textContent = sprayStatus.toUpperCase() === "GREEN" ? "Safe to Spray / పిచికారీ చేయవచ్చు" : 
                                         (sprayStatus.toUpperCase() === "RED" ? "Do Not Spray / పిచికారీ చేయవద్దు" : "Caution / జాగ్రత్త");
                
                sprayBadge.className = "status-badge";
                if (sprayStatus === "green") {
                    sprayBadge.classList.add("status-green");
                } else if (sprayStatus === "red") {
                    sprayBadge.classList.add("status-red");
                } else {
                    sprayBadge.classList.add("status-yellow");
                }
                
                sprayText.textContent = adv.spray_advice || "";

                // TTS audio text setup
                latestAdvisoryReply = data.reply_text;
                if (audioBtn) {
                    audioBtn.style.display = 'inline-flex';
                }

                resultSection.style.display = 'block';
            } else {
                // Render fallback RBK details
                cropText.textContent = "Unclear Crop Photo";
                conditionText.textContent = "Unable to Diagnose confidently";
                confidenceText.textContent = "0%";
                confidenceMeter.style.width = "0%";
                symptomsText.textContent = data.reply_text;
                
                organicTreatmentText.textContent = "N/A";
                chemicalTreatmentText.textContent = "N/A";
                irrigationAdviceText.textContent = "N/A";
                
                sprayBadge.textContent = "UNAVAILABLE";
                sprayBadge.className = "status-badge status-yellow";
                sprayText.textContent = "Please consult a local agri officer.";
                
                if (audioBtn) {
                    audioBtn.style.display = 'none';
                }
                
                resultSection.style.display = 'block';
            }
        })
        .catch(error => {
            console.error("Diagnosis error:", error);
            loader.style.display = 'none';
            uploadSection.style.display = 'block';
            alert("Error analyzing image. Please verify your internet or try a smaller photo.");
        });
    }

    // Audio Playback trigger
    if (audioBtn) {
        audioBtn.addEventListener('click', () => {
            if (!latestAdvisoryReply) return;
            
            // Show dynamic playing state on the button
            const originalHTML = audioBtn.innerHTML;
            audioBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            audioBtn.disabled = true;

            // Fetch TTS voice output file
            fetch('/api/voice-output', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: latestAdvisoryReply, lang: document.body.dataset.lang || "te" })
            })
            .then(res => res.json())
            .then(data => {
                audioBtn.innerHTML = originalHTML;
                audioBtn.disabled = false;
                
                if (data.audio_url) {
                    const audio = new Audio(data.audio_url);
                    audio.play();
                } else {
                    alert("Voice generation failed.");
                }
            })
            .catch(err => {
                audioBtn.innerHTML = originalHTML;
                audioBtn.disabled = false;
                console.error("TTS audio failure:", err);
            });
        });
    }
    
    // Fallback escalation button click
    const escalateBtn = document.getElementById('escalate-rbk-btn');
    if (escalateBtn) {
        escalateBtn.addEventListener('click', () => {
            alert("Escalating to Rythu Bharosa Kendra (RBK)... Please call Toll Free: 155251 for direct guidance from AP Agricultural Officers.");
        });
    }
});
