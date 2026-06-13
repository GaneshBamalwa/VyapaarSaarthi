import { useState, useRef } from 'react'
import { api } from '../hooks/useApi'

export default function OCRAgent() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  async function handleSubmit() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.ocrExtract(fd)
      setResult(res)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const preview = file ? URL.createObjectURL(file) : null
  const isImage = file?.type?.startsWith('image/')

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">OCR Agent</h1>
        <span className="text-sm text-gray-500">Extracts text from invoices, WhatsApp screenshots, challans</span>
      </div>

      {/* Upload area */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
        onClick={() => inputRef.current?.click()}
        onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]) }}
        onDragOver={e => e.preventDefault()}
      >
        <input ref={inputRef} type="file" accept="image/*,.pdf" className="hidden"
          onChange={e => setFile(e.target.files[0])} />
        {file ? (
          <div>
            {isImage && <img src={preview} alt="preview" className="max-h-48 mx-auto mb-3 rounded-lg object-contain" />}
            <p className="text-sm font-medium text-gray-700">{file.name}</p>
            <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div>
            <div className="text-4xl mb-3">📄</div>
            <p className="text-sm text-gray-500">Drop image or PDF here, or click to browse</p>
            <p className="text-xs text-gray-400 mt-1">Supports: JPG, PNG, PDF, WebP</p>
          </div>
        )}
      </div>

      <button onClick={handleSubmit} disabled={!file || loading}
        className="w-full py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 disabled:opacity-40">
        {loading ? 'Extracting text...' : 'Extract Text'}
      </button>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div className="flex gap-4 text-sm">
            <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full font-medium">
              {result.data?.document_type || 'unknown'}
            </span>
            <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full">
              {result.data?.language || '—'}
            </span>
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full">
              {result.data?.confidence ? `${Math.round(result.data.confidence * 100)}% confidence` : '—'}
            </span>
          </div>

          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Extracted Text</p>
            <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-800 whitespace-pre-wrap font-mono overflow-auto max-h-64">
              {result.data?.raw_text || 'No text extracted'}
            </pre>
          </div>

          {result.data?.key_fields && Object.keys(result.data.key_fields).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Key Fields</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(result.data.key_fields).map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded p-2">
                    <p className="text-xs text-gray-500">{k}</p>
                    <p className="text-sm font-medium text-gray-800">{String(v)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400">Duration: {result.duration_ms}ms</p>
        </div>
      )}
    </div>
  )
}
