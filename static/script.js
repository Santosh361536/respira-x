let mediaRecorder, audioChunks = [], recordTimer, recordedAudioBlob = null;
const recordBtn = document.getElementById('recordBtn'), analyzeBtn = document.getElementById('analyzeBtn'),
    audioInput = document.getElementById('audioInput'), loading = document.getElementById('loading'),
    result = document.getElementById('result'), statusIcon = document.getElementById('recordStatus');

recordBtn.addEventListener('click', async () => {
    if (mediaRecorder?.state === 'recording') { stopRecording(); return; }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); mediaRecorder = new MediaRecorder(stream);
        recordBtn.classList.add('recording'); recordBtn.classList.remove('completed'); statusIcon.textContent = 'mic'; statusIcon.className = 'material-icons status-icon mic'; audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data); mediaRecorder.onstop = () => { recordedAudioBlob = new Blob(audioChunks, { type: 'audio/wav' }); showRecordingComplete(); };
        mediaRecorder.start(); recordTimer = setTimeout(() => mediaRecorder?.stop(), 3000);
    } catch (err) { alert('Microphone access denied'); }
});

function stopRecording() { mediaRecorder?.stop(); mediaRecorder?.stream.getTracks().forEach(track => track.stop()); clearTimeout(recordTimer); }
function showRecordingComplete() { recordBtn.classList.remove('recording'); recordBtn.classList.add('completed'); statusIcon.textContent = 'check'; statusIcon.className = 'material-icons status-icon tick'; analyzeBtn.disabled = false; setTimeout(resetRecordingUI, 3000); }
function resetRecordingUI() { recordBtn.classList.remove('recording', 'completed'); statusIcon.textContent = ''; statusIcon.className = 'status-icon'; analyzeBtn.disabled = true; }

audioInput.addEventListener('change', e => { const file = e.target.files[0]; if (file) { recordedAudioBlob = file; analyzeBtn.disabled = false; } });

analyzeBtn.addEventListener('click', async () => {
    if (!recordedAudioBlob) return; loading.classList.remove('hidden'); result.classList.add('hidden'); analyzeBtn.disabled = true;
    try {
        const wavBlob = await convertToWav(recordedAudioBlob); const formData = new FormData(); formData.append('cough_audio', wavBlob, 'cough.wav');
        const response = await fetch('/analyze', { method: 'POST', body: formData }); const data = await response.json();
        console.log('API Response:', data); displayResult(data);
    } catch (error) { console.error('Analysis error:', error); result.innerHTML = '<p class="error">Analysis failed</p>'; result.classList.remove('hidden'); } finally { loading.classList.add('hidden'); resetRecordingUI(); audioInput.value = ''; recordedAudioBlob = null; analyzeBtn.disabled = true; }
});

async function convertToWav(blob) { const arrayBuffer = await blob.arrayBuffer(); const audioContext = new (window.AudioContext || window.webkitAudioContext)(); const audioBuffer = await audioContext.decodeAudioData(arrayBuffer); return new Blob([audioBufferToWav(audioBuffer)], { type: 'audio/wav' }); }

function audioBufferToWav(buffer) {
    const numChannels = buffer.numberOfChannels, sampleRate = buffer.sampleRate, format = 1, bitDepth = 16, result = new Float32Array(buffer.length * numChannels);
    for (let channel = 0; channel < numChannels; channel++)for (let i = 0; i < buffer.length; i++)result[i * numChannels + channel] = buffer.getChannelData(channel)[i];
    const dataSize = result.length * (bitDepth / 8), arrayBuffer = new ArrayBuffer(44 + dataSize), view = new DataView(arrayBuffer);
    writeString(view, 0, 'RIFF'); view.setUint32(4, 36 + dataSize, true); writeString(view, 8, 'WAVE'); writeString(view, 12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, format, true); view.setUint16(22, numChannels, true); view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true); view.setUint16(32, numChannels * (bitDepth / 8), true); view.setUint16(34, bitDepth, true); writeString(view, 36, 'data'); view.setUint32(40, dataSize, true);
    let offset = 44; for (let i = 0; i < result.length; i++, offset += 2) { let s = Math.max(-1, Math.min(1, result[i])); view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true); } return arrayBuffer;
}

function writeString(view, offset, string) { for (let i = 0; i < string.length; i++)view.setUint8(offset + i, string.charCodeAt(i)); }

function displayResult(data) {
    result.classList.remove('hidden');
    const severityClass = data.severity === 'low' ? 'low' : data.severity === 'medium' ? 'medium' : 'high';
    result.className = `result ${severityClass}`;

    // ✅ NO toFixed() - confidence is already "87.3%" string
    result.innerHTML = `
        <h3>${data.status}</h3>
        <p><strong>Prediction:</strong> <span style="color: ${severityClass === 'low' ? '#28a745' : severityClass === 'high' ? '#dc3545' : '#ffc107'}">${data.prediction}</span></p>
        <p><strong>Confidence:</strong> ${data.confidence || 'N/A%'}</p>
        <p><strong>Details:</strong> ${data.details}</p>
    `;
}
