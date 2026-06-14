import React, { useState, useRef, useEffect, useCallback } from "react";
import { Mic, MicOff, Send, Volume2, VolumeX, Radio, Zap, ZapOff } from "lucide-react";
import * as api from "@/services/vyapaarApi";
import { clsx } from "clsx";
import ReactMarkdown from "react-markdown";

const SESSION_ID = `session_${Date.now()}`;

let globalMessages: any[] = [
  {
    id: 1,
    role: "assistant",
    content: "नमस्ते! मैं VyapaarOS AI हूँ — Gemini से powered। आप orders, invoices, GST, cash flow — कुछ भी पूछ सकते हैं। Hindi, English, या Hinglish — जैसे आप चाहें।",
    timestamp: new Date().toISOString(),
  },
];
let globalLoading = false;
let globalBriefingLoading = false;
let chatUpdateListener: (() => void) | null = null;

const addGlobalMessage = (role: string, content: string, audioUrl: string | null = null, extra: any = null) => {
  globalMessages = [
    ...globalMessages,
    {
      id: Date.now(),
      role,
      content,
      audioUrl,
      extra,
      timestamp: new Date().toISOString(),
    },
  ];
  chatUpdateListener?.();
};

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
  { label: "New Order", text: "Ramesh bhai ko bol do 100 kilo steel rod chahiye kal tak, rate 85 rupaye kilo" },
  { label: "Cash Flow", text: "Mera cash flow aur overdue invoices dikhao" },
  { label: "Overdue", text: "Kaun se buyers ka payment overdue hai aur kitna?" },
  { label: "GST Notice", text: "Mujhe ek GST notice mila hai, kya karna chahiye?" },
  { label: "Weekly Summary", text: "Is hafte ka business summary batao" },
  { label: "Loan Scheme", text: "Mujhe MUDRA loan eligibility check karni hai" },
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
  const [messages, setMessages] = useState<any[]>(globalMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(globalLoading);
  const [listening, setListening] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [briefingLoading, setBriefingLoading] = useState(globalBriefingLoading);
  const [transcribing, setTranscribing] = useState(false);

  useEffect(() => {
    chatUpdateListener = () => {
      setMessages(globalMessages);
      setLoading(globalLoading);
      setBriefingLoading(globalBriefingLoading);
    };
    return () => {
      chatUpdateListener = null;
    };
  }, []);

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
    addGlobalMessage(role, content, audioUrl, extra);
  }, []);

  // Text / STT chat
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || globalLoading) return;
      const userText = text.trim();
      setInput("");
      addGlobalMessage("user", userText);
      globalLoading = true;
      chatUpdateListener?.();
      try {
        const result = await api.chat(userText, SESSION_ID, audioEnabled);
        addGlobalMessage(
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
        addGlobalMessage("assistant", `Error: ${e?.response?.data?.detail || e.message || "Backend unreachable"}`);
      } finally {
        globalLoading = false;
        chatUpdateListener?.();
      }
    },
    [audioEnabled]
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
            addGlobalMessage("assistant", "Sorry, I could not transcribe that.");
          }
        } catch (e: any) {
          const detail = e?.response?.data?.detail;
          const msg = typeof detail === "string" ? detail : (Array.isArray(detail) ? detail[0]?.msg : (detail ? JSON.stringify(detail) : null));
          addGlobalMessage("assistant", `Transcription error: ${msg || e.message || "Failed to connect to backend"}`);
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
      recognitionRef.current = recorder;
      setListening(true);
    } catch (e: any) {
      addGlobalMessage("assistant", `Microphone error: ${e.message}`);
    }
  }, [listening, sendMessage]);

  const loadWeeklyBriefing = async () => {
    globalBriefingLoading = true;
    chatUpdateListener?.();
    try {
      const result = await api.weeklyBriefing();
      addGlobalMessage("assistant", `**साप्ताहिक व्यापार सारांश**\n\n${result.script}`, result.audio_url);
      if (!result.audio_url) {
        const utterance = new SpeechSynthesisUtterance(result.script);
        utterance.lang = "hi-IN";
        window.speechSynthesis.speak(utterance);
      }
    } catch (e: any) {
      addGlobalMessage("assistant", `Weekly briefing error: ${e.message}`);
    } finally {
      globalBriefingLoading = false;
      chatUpdateListener?.();
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
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
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
      addGlobalMessage("assistant", `Mic access error: ${e.message}`);
      stopLiveMode();
    }
  }, [stopLiveMode]);

  const sendLiveText = useCallback(() => {
    if (!input.trim() || !wsRef.current) return;
    const text = input.trim();
    setInput("");
    addGlobalMessage("user", text);
    wsRef.current.send(JSON.stringify({ type: "text", data: text }));
  }, [input]);

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
            className="flex items-center gap-2 px-[12px] py-[6px] bg-transparent border border-[#27272A] text-[#71717A] text-[12px] font-[400] rounded-[5px] hover:border-[#3F3F46] hover:text-[#A1A1AA] transition disabled:opacity-50"
          >
            <Radio size={14} className={briefingLoading ? "animate-spin" : ""} />
            {briefingLoading ? "Generating..." : "Weekly Briefing"}
          </button>
          <button
            onClick={() => setAudioEnabled((v) => !v)}
            className={clsx(
              "p-2 rounded-[6px] border border-[#27272A] transition",
              audioEnabled ? "bg-[#18181B] text-[#6366F1]" : "bg-transparent text-[#A1A1AA] hover:text-[#E4E4E7] hover:bg-[#18181B]"
            )}
            title="Toggle TTS audio responses"
          >
            {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
        </div>
      </div>

      {/* Gemini Live banner */}
      <div
        className="bg-[#0D0D0F] border border-[#27272A] rounded-[6px] px-[16px] py-[10px] flex items-center justify-between"
      >
        <div className="flex items-center">
          <div className="w-[6px] h-[6px] rounded-full bg-[#10B981]"></div>
          <span className="text-[13px] text-[#71717A] ml-[8px]">Live voice</span>
          <div className="w-[1px] h-[12px] bg-[#27272A] ml-[12px]"></div>
          <span className="text-[11px] text-[#3F3F46] ml-[12px]">Sub-500ms latency</span>
        </div>
        <div className="flex gap-2">
          {liveMode && (
            <button
              onClick={() => {
                wsRef.current?.send(JSON.stringify({ type: "end_turn" }));
                setLiveStatus("thinking");
              }}
              className="px-[16px] py-[7px] rounded-[5px] text-[13px] font-medium transition bg-transparent text-[#A1A1AA] border border-[#27272A] hover:bg-[#18181B]"
            >
              Done Speaking
            </button>
          )}
          <button
            onClick={liveMode ? stopLiveMode : startLiveMode}
            className="px-[16px] py-[7px] rounded-[5px] text-[13px] font-[500] tracking-[0.01em] transition bg-[#6366F1] text-white border-none"
          >
            {liveMode ? "Stop Live" : "Start Live"}
          </button>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 bg-[#111113] rounded-[6px] border border-[#27272A] overflow-y-auto scrollbar-thin p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-xl border border-[#6366F1] text-[#6366F1] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 bg-transparent">
                VS
              </div>
            )}
            <div
              className={clsx(
                "max-w-[75%] px-[16px] py-[14px] text-[14px] leading-[1.7] border border-[#27272A]",
                msg.role === "user" ? "bg-[#111113] text-[#E4E4E7] rounded-[6px]" : "bg-[#111113] border-l-[2px] border-l-[#6366F1] text-[#E4E4E7] rounded-[0_6px_6px_0]"
              )}
            >
              <div className="markdown-body space-y-2">
                {msg.role === "assistant" && msg.id === messages[messages.length - 1].id ? (
                  <Typewriter 
                    text={msg.content} 
                    render={(displayed) => (
                      <ReactMarkdown 
                        components={{
                          p: ({node, ...props}) => <p className="leading-[1.7] inline" {...props} />,
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
                      p: ({node, ...props}) => <p className="leading-[1.7]" {...props} />,
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
                  {msg.extra.label} — Order #{msg.extra.data?.order_id}
                </div>
              )}
              {msg.audioUrl && (
                <div className="mt-3 pt-2 border-t border-slate-600/50">
                  <audio controls autoPlay src={msg.audioUrl} className="w-full h-9 rounded-md grayscale contrast-125 opacity-90 hover:opacity-100 transition-opacity" />
                </div>
              )}
              <span className="text-[11px] text-[#3F3F46] font-mono mt-[8px] block">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-xl border border-[#A1A1AA] text-[#A1A1AA] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 bg-transparent">
                U
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-xl border border-[#6366F1] text-[#6366F1] flex items-center justify-center font-bold text-xs shrink-0 bg-transparent">
              VS
            </div>
            <div className="bg-[#18181B] border border-[#27272A] rounded-[6px] px-4 py-3">
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
            <div className="max-w-[75%] px-[16px] py-[14px] text-[14px] leading-[1.7] bg-[#111113] border border-[#27272A] border-l-[2px] border-l-[#6366F1] text-[#E4E4E7] rounded-[0_6px_6px_0]">
              <div className="markdown-body space-y-2">
                <ReactMarkdown 
                  components={{
                    p: ({node, ...props}) => <p className="leading-[1.7] inline" {...props} />,
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
            className="px-[12px] py-[5px] bg-transparent border border-[#27272A] rounded-[5px] text-[#71717A] text-[12px] font-[400] tracking-[0.01em] hover:bg-[#18181B] hover:border-[#3F3F46] hover:text-[#A1A1AA] transition disabled:opacity-40"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="flex items-center bg-[#0D0D0F] border border-[#27272A] rounded-[6px] px-[4px] pl-[12px] h-[44px] focus-within:border-[#4338CA] transition-colors">
        {!liveMode && (
          <button
            onClick={toggleListening}
            className={clsx(
              "w-[32px] h-[32px] bg-transparent border-none flex items-center justify-center transition shrink-0",
              listening ? "text-red-400 animate-pulse" : "text-[#52525B] hover:text-[#A1A1AA]"
            )}
          >
            {listening ? <MicOff size={16} strokeWidth={2} /> : <Mic size={16} strokeWidth={2} />}
          </button>
        )}
        {liveMode && (
          <div
            className={clsx(
              "w-[32px] h-[32px] bg-transparent border-none flex items-center justify-center shrink-0",
              liveStatus === "listening" ? "text-green-400 animate-pulse" : "text-[#52525B]"
            )}
          >
            <Mic size={16} strokeWidth={2} />
          </div>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (liveMode ? sendLiveText() : sendMessage(input))}
          placeholder={
            liveMode ? "Ask anything..." : "Ask anything..."
          }
          disabled={loading && !liveMode}
          className="flex-1 bg-transparent border-none text-[14px] text-[#E4E4E7] placeholder:text-[#3F3F46] focus:outline-none disabled:opacity-60 px-2"
        />
        <button
          onClick={() => (liveMode ? sendLiveText() : sendMessage(input))}
          disabled={(loading || !input.trim()) && !liveMode}
          className={clsx(
            "w-[32px] h-[32px] rounded-[5px] flex items-center justify-center transition-all duration-150 shrink-0",
            input.trim() ? "bg-[#6366F1]" : "bg-[#18181B]",
            (!input.trim() && !liveMode) ? "opacity-50" : ""
          )}
        >
          <Send size={14} className="text-white" />
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
