from __future__ import annotations

import socket
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn

from agent.config import Settings
from agent.pipeline import VoiceAgent


SETTINGS = Settings.from_env()
AGENT = VoiceAgent(SETTINGS)
TEMP_AUDIO_DIR = SETTINGS.output_dir / ".tmp_audio"


INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Voice-Controlled Local AI Agent</title>
  <style>
    :root {
      --bg-a: #f7efe4;
      --bg-b: #e2efe6;
      --card: rgba(255, 255, 255, 0.84);
      --ink: #1a2731;
      --muted: #5c6d7b;
      --accent: #0a6c74;
      --accent-2: #14919b;
      --danger: #a33c2e;
      --danger-bg: rgba(163, 60, 46, 0.08);
      --border: rgba(26, 39, 49, 0.1);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Segoe UI", "Trebuchet MS", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.92), transparent 32%),
        radial-gradient(circle at bottom right, rgba(10,108,116,0.16), transparent 26%),
        linear-gradient(135deg, var(--bg-a), var(--bg-b));
    }

    .page {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 40px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(223,244,241,0.92));
      border: 1px solid rgba(10,108,116,0.12);
      border-radius: 28px;
      padding: 28px;
      box-shadow: 0 22px 60px rgba(26, 39, 49, 0.08);
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3rem);
      letter-spacing: -0.04em;
    }

    .hero p {
      margin: 14px 0 0;
      max-width: 850px;
      color: var(--muted);
      line-height: 1.65;
    }

    .hero .badge {
      display: inline-block;
      margin-top: 16px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(10,108,116,0.1);
      color: var(--accent);
      font-weight: 700;
      font-size: 0.95rem;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.05fr 1.2fr;
      gap: 20px;
      margin-top: 20px;
    }

    .panel {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: 0 18px 48px rgba(26, 39, 49, 0.08);
      backdrop-filter: blur(14px);
      padding: 22px;
    }

    .panel h2 {
      margin: 0 0 16px;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
    }

    .muted {
      color: var(--muted);
      line-height: 1.6;
    }

    .stack {
      display: grid;
      gap: 14px;
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    button,
    .file-label {
      border: none;
      border-radius: 16px;
      padding: 12px 16px;
      font-size: 0.96rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, filter 120ms ease;
    }

    button:hover,
    .file-label:hover {
      transform: translateY(-1px);
      filter: brightness(1.02);
    }

    .primary {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: white;
    }

    .secondary {
      background: rgba(10,108,116,0.12);
      color: var(--accent);
    }

    .ghost {
      background: rgba(26,39,49,0.06);
      color: var(--ink);
    }

    .danger {
      background: rgba(163, 60, 46, 0.12);
      color: var(--danger);
    }

    .file-label {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(10,108,116,0.12);
      color: var(--accent);
    }

    input[type="file"] {
      display: none;
    }

    .status {
      min-height: 24px;
      font-weight: 600;
      color: var(--accent);
    }

    .status.error {
      color: var(--danger);
    }

    .preview {
      width: 100%;
      margin-top: 8px;
    }

    .examples {
      margin: 8px 0 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.55;
    }

    .result-box {
      border: 1px solid rgba(26,39,49,0.08);
      background: rgba(255,255,255,0.62);
      border-radius: 18px;
      padding: 14px 15px;
    }

    .result-box strong {
      display: block;
      margin-bottom: 8px;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }

    .result-box pre,
    .result-box .value {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.6;
      font-family: inherit;
      font-size: 0.98rem;
    }

    .error-card {
      display: none;
      border: 1px solid rgba(163, 60, 46, 0.18);
      background: var(--danger-bg);
      border-radius: 18px;
      padding: 14px 16px;
      color: var(--danger);
      line-height: 1.6;
    }

    .loader {
      display: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 3px solid rgba(10,108,116,0.2);
      border-top-color: var(--accent);
      animation: spin 0.8s linear infinite;
    }

    .processing {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--accent);
      font-weight: 700;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    @media (max-width: 900px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>Voice-Controlled Local AI Agent</h1>
      <p>
        Record your voice directly in the browser or upload an existing audio file, then watch the
        full pipeline run: speech-to-text, intent detection, local tool execution, and the final
        result inside the safe <code>output/</code> folder.
      </p>
      <div class="badge">Supported intents: create file, write code, summarize text, general chat</div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Audio Input</h2>
        <div class="stack">
          <p class="muted">
            Use either option below. For the most reliable local transcription, recorded audio is
            converted to WAV automatically in the browser before upload.
          </p>

          <div class="button-row">
            <label class="file-label" for="audio-upload">Upload Audio File</label>
            <input id="audio-upload" type="file" accept="audio/*" />
            <button id="record-start" class="secondary" type="button">Start Recording</button>
            <button id="record-stop" class="ghost" type="button" disabled>Stop Recording</button>
            <button id="clear-audio" class="danger" type="button">Clear Audio</button>
          </div>

          <div id="audio-status" class="status">No audio selected yet.</div>
          <audio id="audio-preview" class="preview" controls style="display:none;"></audio>

          <div class="button-row">
            <button id="run-agent" class="primary" type="button">Run Agent</button>
            <div id="processing" class="processing" style="display:none;">
              <div class="loader" id="loader"></div>
              <span>Processing audio...</span>
            </div>
          </div>

          <div>
            <p class="muted"><strong>Example prompts</strong></p>
            <ul class="examples">
              <li>Create a Python file with a retry function.</li>
              <li>Create a markdown file called meeting-notes with three bullet points.</li>
              <li>Summarize the following text: machine learning can automate repetitive tasks.</li>
              <li>What can you do for me?</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="panel">
        <h2>Pipeline Result</h2>
        <div id="error-card" class="error-card"></div>
        <div class="stack">
          <div class="result-box">
            <strong>Transcribed Text</strong>
            <div id="transcript" class="value">Waiting for audio input.</div>
          </div>
          <div class="result-box">
            <strong>Detected Intent</strong>
            <div id="intent" class="value">Not processed yet.</div>
          </div>
          <div class="result-box">
            <strong>Action Taken</strong>
            <div id="action" class="value">No action yet.</div>
          </div>
          <div class="result-box">
            <strong>Final Output</strong>
            <pre id="result">The result of the selected tool will appear here.</pre>
          </div>
          <div class="result-box">
            <strong>Saved File / Folder Path</strong>
            <div id="file-path" class="value">Nothing has been written yet.</div>
          </div>
          <div class="result-box">
            <strong>Pipeline Trace</strong>
            <pre id="trace">{}</pre>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const audioUpload = document.getElementById("audio-upload");
    const recordStart = document.getElementById("record-start");
    const recordStop = document.getElementById("record-stop");
    const clearAudio = document.getElementById("clear-audio");
    const runAgent = document.getElementById("run-agent");
    const audioStatus = document.getElementById("audio-status");
    const audioPreview = document.getElementById("audio-preview");
    const errorCard = document.getElementById("error-card");
    const transcriptEl = document.getElementById("transcript");
    const intentEl = document.getElementById("intent");
    const actionEl = document.getElementById("action");
    const resultEl = document.getElementById("result");
    const filePathEl = document.getElementById("file-path");
    const traceEl = document.getElementById("trace");
    const processingEl = document.getElementById("processing");
    const loaderEl = document.getElementById("loader");

    let mediaStream = null;
    let audioContext = null;
    let processorNode = null;
    let sourceNode = null;
    let recordedChunks = [];
    let recordedBlob = null;
    let recordedName = "recording.wav";
    let recordingSampleRate = 44100;

    function setStatus(message, isError = false) {
      audioStatus.textContent = message;
      audioStatus.classList.toggle("error", isError);
    }

    function resetResults() {
      errorCard.style.display = "none";
      errorCard.textContent = "";
      transcriptEl.textContent = "Waiting for audio input.";
      intentEl.textContent = "Not processed yet.";
      actionEl.textContent = "No action yet.";
      resultEl.textContent = "The result of the selected tool will appear here.";
      filePathEl.textContent = "Nothing has been written yet.";
      traceEl.textContent = "{}";
    }

    function showAudio(blob, label) {
      const url = URL.createObjectURL(blob);
      audioPreview.src = url;
      audioPreview.style.display = "block";
      setStatus(label);
    }

    function clearAudioSelection() {
      audioUpload.value = "";
      recordedBlob = null;
      recordedChunks = [];
      audioPreview.pause();
      audioPreview.removeAttribute("src");
      audioPreview.load();
      audioPreview.style.display = "none";
      setStatus("No audio selected yet.");
    }

    function mergeBuffers(chunks) {
      let totalLength = 0;
      for (const chunk of chunks) {
        totalLength += chunk.length;
      }
      const result = new Float32Array(totalLength);
      let offset = 0;
      for (const chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
      }
      return result;
    }

    function writeString(view, offset, text) {
      for (let i = 0; i < text.length; i += 1) {
        view.setUint8(offset + i, text.charCodeAt(i));
      }
    }

    function encodeWav(samples, sampleRate) {
      const bytesPerSample = 2;
      const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
      const view = new DataView(buffer);

      writeString(view, 0, "RIFF");
      view.setUint32(4, 36 + samples.length * bytesPerSample, true);
      writeString(view, 8, "WAVE");
      writeString(view, 12, "fmt ");
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * bytesPerSample, true);
      view.setUint16(32, bytesPerSample, true);
      view.setUint16(34, 16, true);
      writeString(view, 36, "data");
      view.setUint32(40, samples.length * bytesPerSample, true);

      let offset = 44;
      for (let i = 0; i < samples.length; i += 1) {
        const sample = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
        offset += bytesPerSample;
      }

      return new Blob([view], { type: "audio/wav" });
    }

    async function startRecording() {
      try {
        clearAudioSelection();
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContextClass();
        recordingSampleRate = audioContext.sampleRate;
        sourceNode = audioContext.createMediaStreamSource(mediaStream);
        processorNode = audioContext.createScriptProcessor(4096, 1, 1);
        recordedChunks = [];

        processorNode.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          recordedChunks.push(new Float32Array(input));
        };

        sourceNode.connect(processorNode);
        processorNode.connect(audioContext.destination);

        recordStart.disabled = true;
        recordStop.disabled = false;
        setStatus("Recording from microphone...");
      } catch (error) {
        setStatus("Could not access microphone. Please allow microphone permissions.", true);
      }
    }

    async function stopRecording() {
      if (!audioContext || !processorNode || !sourceNode) {
        return;
      }

      processorNode.disconnect();
      sourceNode.disconnect();

      if (mediaStream) {
        for (const track of mediaStream.getTracks()) {
          track.stop();
        }
      }

      await audioContext.close();

      const merged = mergeBuffers(recordedChunks);
      recordedBlob = encodeWav(merged, recordingSampleRate);
      recordedName = "recorded-input.wav";
      showAudio(recordedBlob, "Microphone recording is ready.");

      mediaStream = null;
      audioContext = null;
      processorNode = null;
      sourceNode = null;
      recordStart.disabled = false;
      recordStop.disabled = true;
    }

    audioUpload.addEventListener("change", (event) => {
      const file = event.target.files && event.target.files[0];
      recordedBlob = null;
      if (!file) {
        clearAudioSelection();
        return;
      }
      showAudio(file, `Selected file: ${file.name}`);
    });

    recordStart.addEventListener("click", startRecording);
    recordStop.addEventListener("click", stopRecording);

    clearAudio.addEventListener("click", () => {
      resetResults();
      clearAudioSelection();
      recordStart.disabled = false;
      recordStop.disabled = true;
    });

    async function runPipeline() {
      errorCard.style.display = "none";
      errorCard.textContent = "";

      const uploadedFile = audioUpload.files && audioUpload.files[0] ? audioUpload.files[0] : null;
      const audioFile = recordedBlob || uploadedFile;
      const filename = recordedBlob ? recordedName : (uploadedFile ? uploadedFile.name : "");

      if (!audioFile) {
        setStatus("Please record audio or upload an audio file before running the agent.", true);
        return;
      }

      processingEl.style.display = "flex";
      loaderEl.style.display = "inline-block";
      runAgent.disabled = true;
      setStatus("Uploading audio and running the pipeline...");

      const formData = new FormData();
      formData.append("audio", audioFile, filename || "input.wav");

      try {
        const response = await fetch("/api/process", {
          method: "POST",
          body: formData,
        });

        const payload = await response.json();

        if (!response.ok || !payload.success) {
          throw new Error(payload.error || "The agent request failed.");
        }

        transcriptEl.textContent = payload.transcript || "";
        intentEl.textContent = payload.intent || "";
        actionEl.textContent = payload.action || "";
        resultEl.textContent = payload.result || "";
        filePathEl.textContent = payload.file_path || "No file was written for this request.";
        traceEl.textContent = JSON.stringify(payload.trace || {}, null, 2);
        setStatus("Pipeline finished successfully.");
      } catch (error) {
        errorCard.style.display = "block";
        errorCard.textContent = error.message || "Something went wrong while processing the audio.";
        setStatus("The request failed. Check the error panel for details.", true);
      } finally {
        processingEl.style.display = "none";
        loaderEl.style.display = "none";
        runAgent.disabled = false;
      }
    }

    runAgent.addEventListener("click", runPipeline);
    resetResults();
  </script>
</body>
</html>
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    SETTINGS.output_dir.mkdir(parents=True, exist_ok=True)
    TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Voice-Controlled Local AI Agent",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


def choose_open_port(host: str, preferred_port: int, attempts: int = 20) -> int:
    for port in range(preferred_port, preferred_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
        return port
    raise RuntimeError(
        f"Could not find an open port between {preferred_port} and {preferred_port + attempts - 1}."
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)


@app.post("/api/process")
async def process_audio(audio: UploadFile = File(...)) -> JSONResponse:
    suffix = Path(audio.filename or "input.wav").suffix or ".wav"
    temp_path: Path | None = None

    try:
        suffix = suffix.lower()
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=TEMP_AUDIO_DIR,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(await audio.read())

        result = AGENT.run(temp_path)
        final_output = result.tool_result.content or result.tool_result.message

        payload = {
            "success": True,
            "transcript": result.transcript,
            "intent": result.decision.intent.value,
            "action": result.tool_result.action,
            "result": final_output,
            "file_path": str(result.tool_result.file_path) if result.tool_result.file_path else "",
            "trace": {
                "transcript": result.transcript,
                "intent": result.decision.intent.value,
                "confidence": result.decision.confidence,
                "target_path": result.decision.target_path,
                "language": result.decision.language,
                "create_folder": result.decision.create_folder,
                "router_payload": result.decision.raw_payload,
            },
        }
        return JSONResponse(payload)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
    finally:
        await audio.close()
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    port = choose_open_port(SETTINGS.app_host, SETTINGS.app_port)
    if port != SETTINGS.app_port:
        print(
            f"Port {SETTINGS.app_port} is busy. Starting the app on http://{SETTINGS.app_host}:{port} instead."
        )
    uvicorn.run(
        app,
        host=SETTINGS.app_host,
        port=port,
        log_level="info",
    )
