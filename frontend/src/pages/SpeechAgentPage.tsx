import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Mic, Upload, Loader2, FileAudio, X, Square, Send, CheckCircle, AlertCircle } from "lucide-react";
import { runSpeech, runIntake } from "@/services/vyapaarApi";
import { cn, confidenceToPercent } from "@/lib/utils";

const LANGUAGES = [
  { code: "hi-IN", label: "Hindi (India)" },
  { code: "en-IN", label: "English (India)" },
  { code: "mr-IN", label: "Marathi" },
  { code: "gu-IN", label: "Gujarati" },
  { code: "pa-IN", label: "Punjabi" },
];

export function SpeechAgentPage() {
  const [activeTab, setActiveTab] = useState<"record" | "upload">("record");
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("hi-IN");
  const [result, setResult] = useState<unknown>(null);
  const [intakeResult, setIntakeResult] = useState<unknown>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Recording states
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const speechMutation = useMutation({
    mutationFn: ({ file, lang }: { file: File; lang: string }) => runSpeech(file, lang),
    onSuccess: (data) => {
      setResult(data);
      setIntakeResult(null); // Reset intake when new transcription is done
    },
  });

  const intakeMutation = useMutation({
    mutationFn: (text: string) => runIntake(text),
    onSuccess: (data) => setIntakeResult(data),
  });

  const handleFile = (f: File) => {
    setFile(f);
    setResult(null);
    setIntakeResult(null);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const recordedFile = new File([audioBlob], "recorded_voice.webm", { type: "audio/webm" });
        handleFile(recordedFile);
        
        // Stop all tracks in the stream
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Could not access microphone. Please ensure permissions are granted.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const r = result as Record<string, unknown> | null;
  const data = r?.data as Record<string, unknown> | undefined;

  const ir = intakeResult as Record<string, unknown> | null;
  const parsedOrder = ir?.parsed as Record<string, unknown> | undefined;

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
          <Mic size={20} className="text-green-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Speech Agent</h1>
          <p className="text-muted-foreground text-sm">
            Record voice or upload audio to transcribe and extract structured orders
          </p>
        </div>
      </div>

      <div className="glass-card p-5 space-y-5">
        {/* Language selector */}
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">Language</label>
          <div className="flex gap-2 flex-wrap">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setLanguage(lang.code)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 ${
                  language === lang.code
                    ? "bg-green-500/20 border-green-500/40 text-green-400"
                    : "bg-muted/40 border-border/50 text-muted-foreground hover:text-foreground"
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex border-b border-border/50 animate-fade-in">
          <button
            onClick={() => {
              setActiveTab("record");
              setFile(null);
              setResult(null);
              setIntakeResult(null);
            }}
            className={`pb-2.5 px-4 text-sm font-medium border-b-2 transition-all ${
              activeTab === "record"
                ? "border-green-500 text-green-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Record Voice
          </button>
          <button
            onClick={() => {
              setActiveTab("upload");
              setFile(null);
              setResult(null);
              setIntakeResult(null);
            }}
            className={`pb-2.5 px-4 text-sm font-medium border-b-2 transition-all ${
              activeTab === "upload"
                ? "border-green-500 text-green-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Upload File
          </button>
        </div>

        {/* Tab Contents */}
        {activeTab === "record" ? (
          <div className="flex flex-col items-center justify-center p-8 bg-muted/20 border border-border/40 rounded-xl space-y-4">
            {isRecording ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="relative flex items-center justify-center">
                  <div className="absolute w-16 h-16 bg-red-500/30 rounded-full animate-ping" />
                  <button
                    onClick={stopRecording}
                    className="relative w-16 h-16 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center text-white transition-all shadow-lg"
                  >
                    <Square size={20} fill="white" />
                  </button>
                </div>
                <div className="text-sm font-semibold text-foreground animate-pulse">
                  Recording: {formatTime(recordingTime)}
                </div>
                <p className="text-xs text-muted-foreground">Click the button to stop recording</p>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3 animate-fade-in">
                <button
                  onClick={startRecording}
                  className="w-16 h-16 bg-green-500 hover:bg-green-600 rounded-full flex items-center justify-center text-white transition-all shadow-lg hover:scale-105 active:scale-95"
                >
                  <Mic size={24} />
                </button>
                <div className="text-sm font-semibold text-foreground">Click to start recording</div>
                <p className="text-xs text-muted-foreground">Make sure microphone access is enabled</p>
              </div>
            )}
          </div>
        ) : (
          <div
            onClick={() => inputRef.current?.click()}
            className="border-2 border-dashed border-border/60 rounded-xl p-8 text-center cursor-pointer
                       hover:border-green-500/40 hover:bg-green-500/5 transition-all duration-200 animate-fade-in"
          >
            <input
              ref={inputRef}
              type="file"
              accept="audio/*"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <FileAudio size={40} className="mx-auto text-muted-foreground/40 mb-2" />
            <div className="text-sm text-muted-foreground">Click to upload audio file</div>
            <div className="text-xs text-muted-foreground/60 mt-1">MP3, WAV, FLAC, OGG, WebM · Max 25MB</div>
          </div>
        )}

        {/* Selected / Recorded File Indicator */}
        {file && (
          <div className="space-y-3 animate-slide-up">
            <div className="flex items-center justify-between bg-muted/40 px-4 py-2.5 rounded-lg border border-border/50">
              <div className="flex items-center gap-2 text-sm">
                <FileAudio size={16} className="text-green-400" />
                <span className="text-foreground font-medium truncate max-w-xs">{file.name}</span>
                <span className="text-xs text-muted-foreground font-mono">
                  ({(file.size / 1024).toFixed(0)} KB)
                </span>
              </div>
              <button
                onClick={() => {
                  setFile(null);
                  setResult(null);
                  setIntakeResult(null);
                }}
              >
                <X size={16} className="text-muted-foreground hover:text-foreground" />
              </button>
            </div>
            {/* Audio review */}
            <div className="flex justify-center bg-muted/20 p-2.5 rounded-lg border border-border/30">
              <audio src={URL.createObjectURL(file)} controls className="w-full max-w-md h-9" />
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={() => file && speechMutation.mutate({ file, lang: language })}
          disabled={!file || speechMutation.isPending || isRecording}
          className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm disabled:opacity-50"
        >
          {speechMutation.isPending ? (
            <><Loader2 size={16} className="animate-spin" /> Transcribing...</>
          ) : (
            <><Mic size={16} /> Transcribe Audio</>
          )}
        </button>
      </div>

      {/* Transcript Result & Extract Order Action */}
      {data && (
        <div className="space-y-6">
          <div className="glass-card p-5 space-y-4 animate-slide-up">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-400" />
              <h3 className="text-sm font-semibold">Transcript</h3>
              <span className="tag bg-green-400/10 text-green-400 border border-green-400/20">
                {data.language_code as string}
              </span>
            </div>
            <div className="bg-muted/40 p-4 rounded-lg text-sm text-foreground leading-relaxed">
              {data.transcript as string}
            </div>

            {/* Extract Order Button */}
            <div className="pt-2">
              <button
                onClick={() => data.transcript && intakeMutation.mutate(data.transcript as string)}
                disabled={intakeMutation.isPending || !data.transcript}
                className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm disabled:opacity-50 bg-saffron-500 hover:bg-saffron-600 border-saffron-500/20"
              >
                {intakeMutation.isPending ? (
                  <><Loader2 size={16} className="animate-spin" /> Extracting...</>
                ) : (
                  <><Send size={16} /> Extract Order</>
                )}
              </button>
            </div>
          </div>

          {/* Structured Intake Result */}
          {ir && (
            <div className="glass-card p-5 space-y-4 animate-slide-up border border-saffron-500/20">
              <div className="flex items-center gap-2">
                {ir.status === "success" ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <AlertCircle size={16} className="text-red-400" />
                )}
                <span className="text-sm font-semibold">Structured Order Details</span>
                {ir.requires_hitl === true && (
                  <span className="tag bg-yellow-400/10 text-yellow-400 border border-yellow-400/20">
                    HITL Required
                  </span>
                )}
              </div>

              {parsedOrder && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Customer</div>
                      <div className="text-sm font-medium">{(parsedOrder.customer as string) || "—"}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Delivery Date</div>
                      <div className="text-sm font-medium">{(parsedOrder.delivery_date as string) || "—"}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Confidence Score</div>
                      <div className={cn(
                        "text-sm font-bold",
                        (parsedOrder.confidence as number) >= 0.8 ? "text-green-400" : "text-yellow-400"
                      )}>
                        {confidenceToPercent(parsedOrder.confidence as number)}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-xs text-muted-foreground mb-2">Items Extracted</div>
                    <div className="space-y-1.5">
                      {((parsedOrder.items as unknown[]) || []).map((item: unknown, i: number) => {
                        const it = item as Record<string, unknown>;
                        return (
                          <div key={i} className="flex items-center gap-2 text-xs bg-muted/40 px-3 py-2 rounded-lg border border-border/30">
                            <span className="text-saffron-400 font-mono font-semibold">{String(it.quantity ?? "")}</span>
                            <span className="text-muted-foreground">{String(it.unit ?? "")}</span>
                            <span className="text-foreground font-medium">{String(it.name ?? "")}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* Clarification */}
              {ir.clarification !== null && ir.clarification !== undefined &&
              (ir.clarification as Record<string, unknown>).status === "AMBIGUOUS" && (
                <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
                  <div className="text-xs text-purple-400 font-medium mb-1">🔍 Clarification Needed</div>
                  <div className="text-sm text-foreground">
                    {String((ir.clarification as Record<string, unknown>).clarification_question ?? "")}
                  </div>
                </div>
              )}

              <div>
                <div className="text-xs text-muted-foreground mb-2">Raw JSON Response</div>
                <pre className="text-xs bg-muted/40 p-3 rounded-lg overflow-x-auto text-muted-foreground font-mono">
                  {JSON.stringify(ir, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
