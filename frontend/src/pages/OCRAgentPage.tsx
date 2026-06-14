import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Eye, Upload, Loader2, FileImage, X, Send, CheckCircle, AlertCircle } from "lucide-react";
import { runOCR, runIntake } from "@/services/vyapaarApi";
import { cn, confidenceToPercent } from "@/lib/utils";

export function OCRAgentPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [intakeResult, setIntakeResult] = useState<unknown>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: runOCR,
    onSuccess: (data) => {
      setResult(data);
      setIntakeResult(null); // Reset when new OCR is run
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
    if (f.type.startsWith("image/")) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const r = result as Record<string, unknown> | null;
  const data = r?.data as Record<string, unknown> | undefined;

  const ir = intakeResult as Record<string, unknown> | null;
  const parsedOrder = ir?.parsed as Record<string, unknown> | undefined;

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
          <Eye size={20} className="text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">OCR Agent</h1>
          <p className="text-muted-foreground text-sm">
            Extract text from images, PDFs, WhatsApp screenshots using Gemini Vision
          </p>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="glass-card p-5 space-y-4">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed border-border/60 rounded-xl p-8 text-center cursor-pointer
                     hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-200"
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*,application/pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          {preview ? (
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 mx-auto rounded-lg object-contain"
            />
          ) : (
            <div className="space-y-2">
              <FileImage size={40} className="mx-auto text-muted-foreground/40" />
              <div className="text-sm text-muted-foreground">
                Drop image or PDF here, or click to browse
              </div>
              <div className="text-xs text-muted-foreground/60">
                JPG, PNG, WebP, PDF · Max 10MB
              </div>
            </div>
          )}
        </div>

        {file && (
          <div className="flex items-center justify-between bg-muted/40 px-4 py-2 rounded-lg">
            <div className="flex items-center gap-2 text-sm">
              <FileImage size={16} className="text-blue-400" />
              <span className="text-foreground font-medium truncate max-w-xs">{file.name}</span>
              <span className="text-muted-foreground text-xs">
                ({(file.size / 1024).toFixed(0)} KB)
              </span>
            </div>
            <button
              onClick={() => { setFile(null); setPreview(null); setResult(null); setIntakeResult(null); }}
              className="text-muted-foreground hover:text-foreground"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <button
          onClick={() => file && mutation.mutate(file)}
          disabled={!file || mutation.isPending}
          className="btn-primary flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm disabled:opacity-50"
        >
          {mutation.isPending ? (
            <><Loader2 size={16} className="animate-spin" /> Extracting...</>
          ) : (
            <><Upload size={16} /> Run OCR</>
          )}
        </button>
      </div>

      {/* Result */}
      {data && (
        <div className="space-y-6">
          <div className="glass-card p-5 space-y-4 animate-slide-up">
            <h3 className="text-sm font-semibold">Extraction Result</h3>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="bg-muted/40 p-3 rounded-lg">
                <div className="text-muted-foreground mb-1">Document Type</div>
                <div className="font-medium text-foreground capitalize">
                  {(data.document_type as string)?.replace("_", " ")}
                </div>
              </div>
              <div className="bg-muted/40 p-3 rounded-lg">
                <div className="text-muted-foreground mb-1">Language</div>
                <div className="font-medium text-foreground capitalize">{data.language as string}</div>
              </div>
              <div className="bg-muted/40 p-3 rounded-lg">
                <div className="text-muted-foreground mb-1">Confidence</div>
                <div className={`font-bold ${(data.confidence as number) >= 0.8 ? "text-green-400" : "text-yellow-400"}`}>
                  {Math.round((data.confidence as number) * 100)}%
                </div>
              </div>
            </div>

            <div>
              <div className="text-xs text-muted-foreground mb-2">Extracted Text</div>
              <div className="bg-muted/40 p-4 rounded-lg text-sm text-foreground whitespace-pre-wrap max-h-60 overflow-y-auto font-mono">
                {String(data.raw_text ?? "")}
              </div>
            </div>

            {data.key_fields !== null && data.key_fields !== undefined && Object.keys(data.key_fields as Record<string, unknown>).length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Detected Key Fields</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(data.key_fields as Record<string, unknown>).map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-xs bg-muted/30 px-3 py-2 rounded">
                      <span className="text-muted-foreground">{k}:</span>
                      <span className="text-foreground font-medium truncate">{String(v ?? "")}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extract Order Button */}
            <div className="pt-2">
              <button
                onClick={() => data.raw_text && intakeMutation.mutate(data.raw_text as string)}
                disabled={intakeMutation.isPending || !data.raw_text}
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
                  <div className="text-xs text-purple-400 font-medium mb-1">Clarification Needed</div>
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
