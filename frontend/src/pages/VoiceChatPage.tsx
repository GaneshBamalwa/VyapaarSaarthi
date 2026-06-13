import React, { useState, useRef, useEffect, useCallback } from "react";
import { Mic, MicOff, Send, Volume2, VolumeX, Radio, Zap, ZapOff } from "lucide-react";
import * as api from "@/services/vyapaarApi";
import { clsx } from "clsx";
import ReactMarkdown from "react-markdown";

const SESSION_ID = `session_${Date.now()}`;

// ── AudioStreamer — exact port of google-gemini/live-api-web-console audio-streamer.ts ──
class AudioStreamer {
  private context: AudioContext;
  private sampleRate = 24000;
  private bufferSize = 7680;
  private audioQueue: Float32Array[] = [];
  private isPlaying = false;
  private isStreamComplete = false;
  private checkInterval: number | null = null;
  private scheduledTime = 0;
  private initialBufferTime = 0.1;
  private endOfQueueAudioSource: AudioBufferSourceNode | null = null;
  public onComplete: () => void = () => {};
  private gainNode: GainNode;

  constructor(context: AudioContext) {
    this.context = context;
    this.gainNode = this.context.createGain();
    this.gainNode.connect(this.context.destination);
    this.addPCM16 = this.addPCM16.bind(this);
  }

  private _processPCM16Chunk(chunk: Uint8Array): Float32Array {
    const float32Array = new Float32Array(chunk.length / 2);
    const dataView = new DataView(chunk.buffer);
    for (let i = 0; i < chunk.length / 2; i++) {
      float32Array[i] = dataView.getInt16(i * 2, true) / 32768;
    }
    return float32Array;
  }

  public addPCM16(chunk: Uint8Array) {
    this.isStreamComplete = false;
    let buf = this._processPCM16Chunk(chunk);
    while (buf.length >= this.bufferSize) {
      this.audioQueue.push(buf.slice(0, this.bufferSize));
      buf = buf.slice(this.bufferSize);
    }
    if (buf.length > 0) this.audioQueue.push(buf);
    if (!this.isPlaying) {
      this.isPlaying = true;
      this.scheduledTime = this.context.currentTime + this.initialBufferTime;
      this.scheduleNextBuffer();
    }
  }

  private _createAudioBuffer(audioData: Float32Array): AudioBuffer {
    const ab = this.context.createBuffer(1, audioData.length, this.sampleRate);
    ab.getChannelData(0).set(audioData);
    return ab;
  }

  private scheduleNextBuffer() {
    const SCHEDULE_AHEAD_TIME = 0.2;
    while (
      this.audioQueue.length > 0 &&
      this.scheduledTime < this.context.currentTime + SCHEDULE_AHEAD_TIME
    ) {
      const audioData = this.audioQueue.shift();
      if (!audioData) continue;
      const audioBuffer = this._createAudioBuffer(audioData);
      const source = this.context.createBufferSource();
      if (this.audioQueue.length === 0) {
        if (this.endOfQueueAudioSource) this.endOfQueueAudioSource.onended = null;
        this.endOfQueueAudioSource = source;
        source.onended = () => {
          if (!this.audioQueue.length && this.endOfQueueAudioSource === source) {
            this.endOfQueueAudioSource = null;
            this.onComplete();
          }
        };
      }
      source.buffer = audioBuffer;
      source.connect(this.gainNode);
      const startTime = Math.max(this.scheduledTime, this.context.currentTime);
      source.start(startTime);
      this.scheduledTime = startTime + audioBuffer.duration;
    }
    if (this.audioQueue.length === 0) {
      if (this.isStreamComplete) {
        this.isPlaying = false;
        if (this.checkInterval !== null) {
          clearInterval(this.checkInterval);
          this.checkInterval = null;
        }
      } else {
        if (!this.checkInterval) {
          this.checkInterval = window.setInterval(() => {
            if (this.audioQueue.length > 0) this.scheduleNextBuffer();
          }, 100);
        }
      }
    } else {
      const nextCheckTime = (this.scheduledTime - this.context.currentTime) * 1000;
      setTimeout(() => this.scheduleNextBuffer(), Math.max(0, nextCheckTime - 50));
    }
  }

  public stop() {
    this.isPlaying = false;
    this.isStreamComplete = true;
    this.audioQueue = [];
    this.scheduledTime = this.context.currentTime;
    if (this.checkInterval !== null) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.gainNode.gain.linearRampToValueAtTime(0, this.context.currentTime + 0.1);
    setTimeout(() => {
      this.gainNode.disconnect();
      this.gainNode = this.context.createGain();
      this.gainNode.connect(this.context.destination);
    }, 200);
  }

  public async resume() {
    if (this.context.state === "suspended") await this.context.resume();
    this.isStreamComplete = false;
    this.scheduledTime = this.context.currentTime + this.initialBufferTime;
    this.gainNode.gain.setValueAtTime(1, this.context.currentTime);
  }

  public complete() {
    this.isStreamComplete = true;
    this.onComplete();
  }
}

const QUICK_PROMPTS = [
  { label: "📦 New Order", text: "Ramesh bhai ko bol do 100 kilo steel rod chahiye kal tak, rate 85 rupaye kilo" },
  { label: "💵 Cash Flow", text: "Mera cash flow aur overdue invoices dikhao" },
  { label: "⚠️ Overdue", text: "Kaun se buyers ka payment overdue hai aur kitna?" },
  { label: "🧾 GST Notice", text: "Mujhe ek GST notice mila hai, kya karna chahiye?" },
  { label: "📊 Weekly Summary", text: "Is hafte ka business summary batao" },
  { label: "🏛️ Loan Scheme", text: "Mujhe MUDRA loan eligibility check karni hai" },
];

const Typewriter = ({ text, speed = 15, onComplete, render }: { text: string, speed?: number, onComplete?: () => void, render: (displayed: string) => React.ReactNode }) => {
  const [displayed, setDisplayed] = useState("");
  
  useEffect(() => {
    setDisplayed("");
    let i = 0;
    const interval = setInterval(() => {
      setDisplayed(text.substring(0, i));
      i++;
      if (i > text.length) {
        clearInterval(interval);
        onComplete?.();
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed, onComplete]);

  return <>{render(displayed + (displayed.length < text.length ? " ▋" : ""))}</>;
};

export default function VoiceChatPage() {
  const [messages, setMessages] = useState<any[]>([
    {
      id: 1,
      role: "assistant",
      content:
        "नमस्ते! मैं VyapaarOS AI हूँ — Gemini से powered। आप orders, invoices, GST, cash flow — कुछ भी पूछ सकते हैं। Hindi, English, या Hinglish — जैसे आप चाहें।",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [briefingLoading, setBriefingLoading] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

  // Gemini Live state
  const [liveMode, setLiveMode] = useState(false);
  const [liveStatus, setLiveStatus] = useState("idle"); // idle | connecting | connected | listening | thinking | speaking | error
  const [liveTranscript, setLiveTranscript] = useState("");

  const recognitionRef = useRef<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRef = useRef<any>(null);
  const recCtxRef = useRef<AudioContext | null>(null);
  const outCtxRef = useRef<AudioContext | null>(null);
  const audioStreamerRef = useRef<AudioStreamer | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = useCallback((role: string, content: string, audioUrl: string | null = null, extra: any = null) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role,
        content,
        audioUrl,
        extra,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  // Text / STT chat
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      const userText = text.trim();
      setInput("");
      addMessage("user", userText);
      setLoading(true);
      try {
        const result = await api.chat(userText, SESSION_ID, audioEnabled);
        addMessage(
          "assistant",
          result.response,
          result.audio_url,
          result.action_result ? { label: "Order created", data: result.action_result } : null
        );
        if (audioEnabled && !result.audio_url) {
          const utterance = new SpeechSynthesisUtterance(result.response);
          utterance.lang = "hi-IN";
          window.speechSynthesis.speak(utterance);
        }
      } catch (e: any) {
        addMessage("assistant", `Error: ${e?.response?.data?.detail || e.message || "Backend unreachable"}`);
      } finally {
        setLoading(false);
      }
    },
    [loading, audioEnabled, addMessage]
  );

  const toggleListening = useCallback(async () => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (chunks.length === 0) return;

        const blob = new Blob(chunks, { type: "audio/webm" });
        const file = new File([blob], "chat_audio.webm", { type: "audio/webm" });

        setTranscribing(true);
        try {
          const fd = new FormData();
          fd.append("audio", file);
          fd.append("language", "hi-IN");
          const res = await api.transcribe(fd);
          if (res?.transcript) {
            sendMessage(res.transcript);
          } else {
            addMessage("assistant", "Sorry, I could not transcribe that.");
          }
        } catch (e: any) {
          const detail = e?.response?.data?.detail;
          const msg = typeof detail === "string" ? detail : (Array.isArray(detail) ? detail[0]?.msg : (detail ? JSON.stringify(detail) : null));
          addMessage("assistant", `Transcription error: ${msg || e.message || "Failed to connect to backend"}`);
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
      recognitionRef.current = recorder;
      setListening(true);
    } catch (e: any) {
      addMessage("assistant", `Microphone error: ${e.message}`);
    }
  }, [listening, sendMessage, addMessage]);

  const loadWeeklyBriefing = async () => {
    setBriefingLoading(true);
    try {
      const result = await api.weeklyBriefing();
      addMessage("assistant", `📻 **साप्ताहिक व्यापार सारांश**\n\n${result.script}`, result.audio_url);
      if (!result.audio_url) {
        const utterance = new SpeechSynthesisUtterance(result.script);
        utterance.lang = "hi-IN";
        window.speechSynthesis.speak(utterance);
      }
    } catch (e: any) {
      addMessage("assistant", `Weekly briefing error: ${e.message}`);
    } finally {
      setBriefingLoading(false);
    }
  };

  // Gemini Live AudioWorklet string
  const RECORDER_WORKLET = `
class AudioProcessingWorklet extends AudioWorkletProcessor {
  buffer = new Int16Array(2048);
  bufferWriteIndex = 0;
  process(inputs) {
    if (inputs[0].length) {
      const channel0 = inputs[0][0];
      this.processChunk(channel0);
    }
    return true;
  }
  sendAndClearBuffer() {
    this.port.postMessage({
      event: "chunk",
      data: { int16arrayBuffer: this.buffer.slice(0, this.bufferWriteIndex).buffer }
    });
    this.bufferWriteIndex = 0;
  }
  processChunk(float32Array) {
    const l = float32Array.length;
    for (let i = 0; i < l; i++) {
      this.buffer[this.bufferWriteIndex++] = float32Array[i] * 32768;
      if (this.bufferWriteIndex >= this.buffer.length) this.sendAndClearBuffer();
    }
    if (this.bufferWriteIndex >= this.buffer.length) this.sendAndClearBuffer();
  }
}
registerProcessor('audio-recorder-worklet', AudioProcessingWorklet);
`;

  const stopLiveMode = useCallback(() => {
    audioStreamerRef.current?.stop();
    audioStreamerRef.current = null;
    if (mediaRef.current) {
      mediaRef.current.srcNode?.disconnect();
      mediaRef.current.worklet?.disconnect();
      mediaRef.current.stream?.getTracks().forEach((t: any) => t.stop());
      mediaRef.current.ctx?.close();
      mediaRef.current = null;
    }
    if (outCtxRef.current) {
      outCtxRef.current.close();
      outCtxRef.current = null;
    }
    recCtxRef.current = null;
    try {
      wsRef.current?.send(JSON.stringify({ type: "close" }));
      wsRef.current?.close();
    } catch {
      // Ignored
    }
    wsRef.current = null;
    setLiveMode(false);
    setLiveStatus("idle");
    setLiveTranscript("");
  }, []);

  const startLiveMode = useCallback(async () => {
    if (wsRef.current) return;
    setLiveMode(true);
    setLiveStatus("connecting");
    setLiveTranscript("");

    const outCtx = new AudioContext({ sampleRate: 24000 });
    outCtxRef.current = outCtx;
    await outCtx.resume();
    const streamer = new AudioStreamer(outCtx);
    audioStreamerRef.current = streamer;
    streamer.onComplete = () => setLiveStatus("listening");

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${window.location.host}/ws/live`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "status") {
        setLiveStatus(msg.data);
      } else if (msg.type === "interrupted") {
        audioStreamerRef.current?.stop();
        setLiveStatus("listening");
        setLiveTranscript((prev) => {
          if (prev.trim()) addMessage("assistant", prev);
          return "";
        });
      } else if (msg.type === "text") {
        setLiveTranscript((t) => t + msg.data);
      } else if (msg.type === "turn_complete") {
        setLiveTranscript((prev) => {
          if (prev.trim()) addMessage("assistant", prev);
          return "";
        });
      } else if (msg.type === "audio") {
        const binary = atob(msg.data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        audioStreamerRef.current?.addPCM16(bytes);
        setLiveStatus("speaking");
      } else if (msg.type === "error") {
        addMessage("assistant", `Gemini Live error: ${msg.data}`);
        stopLiveMode();
      }
    };
    ws.onerror = () => {
      setLiveStatus("error");
      stopLiveMode();
    };
    ws.onclose = () => {
      setLiveMode(false);
      setLiveStatus("idle");
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recCtx = new AudioContext({ sampleRate: 16000 });
      recCtxRef.current = recCtx;

      const blob = new Blob([RECORDER_WORKLET], { type: "application/javascript" });
      const url = URL.createObjectURL(blob);
      await recCtx.audioWorklet.addModule(url);
      URL.revokeObjectURL(url);

      const srcNode = recCtx.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(recCtx, "audio-recorder-worklet");
      worklet.port.onmessage = (ev) => {
        if (ev.data?.event !== "chunk" || !ev.data?.data?.int16arrayBuffer) return;
        if (ws.readyState !== WebSocket.OPEN) return;
        const b64 = btoa(String.fromCharCode(...new Uint8Array(ev.data.data.int16arrayBuffer)));
        ws.send(JSON.stringify({ type: "audio", data: b64, rate: 16000 }));
      };
      srcNode.connect(worklet);
      mediaRef.current = { stream, ctx: recCtx, worklet, srcNode };
    } catch (e: any) {
      addMessage("assistant", `Mic access error: ${e.message}`);
      stopLiveMode();
    }
  }, [addMessage, stopLiveMode]);

  const sendLiveText = useCallback(() => {
    if (!input.trim() || !wsRef.current) return;
    const text = input.trim();
    setInput("");
    addMessage("user", text);
    wsRef.current.send(JSON.stringify({ type: "text", data: text }));
  }, [input, addMessage]);

  // Cleanup on unmount
  useEffect(() => () => stopLiveMode(), [stopLiveMode]);

  const LIVE_STATUS_LABEL: Record<string, string> = {
    idle: "",
    connecting: "Connecting...",
    connected: "Ready",
    listening: "Listening...",
    thinking: "Thinking...",
    speaking: "Speaking...",
    error: "Error",
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Voice & Chat</h1>
          <p className="text-sm text-slate-400">Gemini-powered Hinglish assistant — writes to your live DB</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadWeeklyBriefing}
            disabled={briefingLoading}
            className="flex items-center gap-2 px-3 py-2 bg-brand/20 border border-brand/40 text-brand rounded-lg text-sm hover:bg-brand/30 transition disabled:opacity-50"
          >
            <Radio size={14} className={briefingLoading ? "animate-spin" : ""} />
            {briefingLoading ? "Generating..." : "Weekly Briefing"}
          </button>
          <button
            onClick={() => setAudioEnabled((v) => !v)}
            className={clsx(
              "p-2 rounded-lg border transition",
              audioEnabled ? "bg-brand/20 border-brand/40 text-brand" : "bg-card border-border text-slate-400 hover:text-white"
            )}
            title="Toggle TTS audio responses"
          >
            {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
        </div>
      </div>

      {/* Gemini Live banner */}
      <div
        className={clsx(
          "rounded-xl border p-3 flex items-center justify-between transition-colors",
          liveMode ? "bg-green-500/10 border-green-500/40" : "bg-card border-border"
        )}
      >
        <div className="flex items-center gap-3">
          {liveMode ? (
            <Zap size={16} className="text-green-400 animate-pulse" />
          ) : (
            <ZapOff size={16} className="text-slate-400" />
          )}
          <div>
            <p className="text-sm font-medium text-white">Gemini Live — Bidirectional Voice</p>
            <p className="text-xs text-slate-400">
              {liveMode ? LIVE_STATUS_LABEL[liveStatus] || liveStatus : "Real-time voice conversation with sub-500ms latency"}
            </p>
          </div>
        </div>
        <button
          onClick={liveMode ? stopLiveMode : startLiveMode}
          className={clsx(
            "px-4 py-2 rounded-lg text-sm font-medium transition",
            liveMode
              ? "bg-red-500/20 text-red-400 border border-red-500/40 hover:bg-red-500/30"
              : "bg-green-500/20 text-green-400 border border-green-500/40 hover:bg-green-500/30"
          )}
        >
          {liveMode ? "Stop Live" : "Start Live"}
        </button>
      </div>

      {/* Chat area */}
      <div className="flex-1 bg-card rounded-xl border border-border overflow-y-auto scrollbar-thin p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-full bg-brand/20 border border-brand/40 flex items-center justify-center text-sm shrink-0 mt-0.5">
                🤖
              </div>
            )}
            <div
              className={clsx(
                "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                msg.role === "user" ? "bg-brand text-white rounded-tr-sm" : "bg-slate-700/60 text-slate-100 rounded-tl-sm"
              )}
            >
              <div className="markdown-body space-y-2">
                {msg.role === "assistant" && msg.id === messages[messages.length - 1].id ? (
                  <Typewriter 
                    text={msg.content} 
                    render={(displayed) => (
                      <ReactMarkdown 
                        components={{
                          p: ({node, ...props}) => <p className="leading-relaxed inline" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-5 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-5 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li {...props} />,
                          h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-2" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-base font-bold mt-2" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-1" {...props} />,
                          a: ({node, ...props}) => <a className="text-blue-400 hover:underline" {...props} />,
                        }}
                      >
                        {displayed}
                      </ReactMarkdown>
                    )}
                  />
                ) : (
                  <ReactMarkdown 
                    components={{
                      p: ({node, ...props}) => <p className="leading-relaxed" {...props} />,
                      strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc pl-5 space-y-1" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal pl-5 space-y-1" {...props} />,
                      li: ({node, ...props}) => <li {...props} />,
                      h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-2" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-base font-bold mt-2" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-1" {...props} />,
                      a: ({node, ...props}) => <a className="text-blue-400 hover:underline" {...props} />,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
              {msg.extra && (
                <div className="mt-2 text-xs bg-green-500/10 border border-green-500/30 rounded-lg px-2 py-1 text-green-400">
                  ✅ {msg.extra.label} — Order #{msg.extra.data?.order_id}
                </div>
              )}
              {msg.audioUrl && (
                <div className="mt-3 pt-2 border-t border-slate-600/50">
                  <audio controls autoPlay src={msg.audioUrl} className="w-full h-9 rounded-md grayscale contrast-125 opacity-90 hover:opacity-100 transition-opacity" />
                </div>
              )}
              <p className="text-[10px] opacity-50 mt-1.5">{new Date(msg.timestamp).toLocaleTimeString()}</p>
            </div>
            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-full bg-slate-600 flex items-center justify-center text-sm shrink-0 mt-0.5">
                👨‍💼
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-brand/20 border border-brand/40 flex items-center justify-center text-sm shrink-0">
              🤖
            </div>
            <div className="bg-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center h-5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {liveTranscript.trim() && (
          <div className="flex gap-3 justify-start">
            <div className="w-7 h-7 rounded-full bg-brand/20 border border-brand/40 flex items-center justify-center text-sm shrink-0 mt-0.5 animate-pulse">
              🤖
            </div>
            <div className="max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed bg-slate-700/60 text-slate-100 rounded-tl-sm border border-brand/20">
              <div className="markdown-body space-y-2">
                <ReactMarkdown 
                  components={{
                    p: ({node, ...props}) => <p className="leading-relaxed inline" {...props} />,
                  }}
                >
                  {liveTranscript + " ▋"}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      <div className="flex gap-2 flex-wrap">
        {QUICK_PROMPTS.map((p) => (
          <button
            key={p.label}
            onClick={() =>
              liveMode ? wsRef.current?.send(JSON.stringify({ type: "text", data: p.text })) : sendMessage(p.text)
            }
            disabled={loading}
            className="text-xs px-3 py-1.5 bg-card border border-border rounded-full text-slate-300 hover:border-brand/60 hover:text-white transition disabled:opacity-40"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="flex gap-2">
        {!liveMode && (
          <button
            onClick={toggleListening}
            className={clsx(
              "w-11 h-11 rounded-xl border flex items-center justify-center transition shrink-0",
              listening
                ? "bg-red-500/20 border-red-500/60 text-red-400 animate-pulse"
                : "bg-card border-border text-slate-400 hover:text-white hover:border-slate-500"
            )}
          >
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        )}
        {liveMode && (
          <div
            className={clsx(
              "w-11 h-11 rounded-xl border flex items-center justify-center shrink-0",
              liveStatus === "listening"
                ? "bg-green-500/20 border-green-500/40 text-green-400 animate-pulse"
                : liveStatus === "speaking"
                ? "bg-blue-500/20 border-blue-500/40 text-blue-400"
                : "bg-card border-border text-slate-400"
            )}
          >
            <Mic size={16} />
          </div>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (liveMode ? sendLiveText() : sendMessage(input))}
          placeholder={
            liveMode
              ? "Type to Gemini Live... या बोलें (mic auto on)"
              : "Type in Hindi, English, या Hinglish... 🎙️"
          }
          disabled={loading && !liveMode}
          className="flex-1 bg-card border border-border rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-brand/60 disabled:opacity-60"
        />
        <button
          onClick={() => (liveMode ? sendLiveText() : sendMessage(input))}
          disabled={(loading || !input.trim()) && !liveMode}
          className="w-11 h-11 rounded-xl bg-brand hover:bg-brand-dark flex items-center justify-center transition disabled:opacity-40 shrink-0"
        >
          <Send size={16} className="text-white" />
        </button>
      </div>

      {listening && (
        <div className="flex items-center gap-2 text-xs text-red-400 animate-pulse px-1">
          <span className="w-2 h-2 rounded-full bg-red-400" />
          सुन रहा हूँ... (Recording, click Mic to stop & send)
        </div>
      )}
      {transcribing && <div className="flex items-center gap-2 text-xs text-brand animate-pulse px-1">Transcribing audio...</div>}
      {liveMode && liveTranscript && <div className="text-xs text-slate-400 px-1 truncate">Live: {liveTranscript}</div>}
    </div>
  );
}
