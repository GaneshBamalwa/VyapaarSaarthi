import { useState, useRef } from 'react'
import { api } from '../hooks/useApi'

export default function SpeechAgentPage() {
  const [file, setFile] = useState(null)
  const [language, setLanguage] = useState('hi-IN')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recording, setRecording] = useState(false)
  const mediaRef = useRef(null)
  const chunksRef = useRef([])
  const inputRef = useRef()

  async function startRecord() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    chunksRef.current = []
    recorder.ondataavailable = e => chunksRef.current.push(e.data)
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      setFile(new File([blob], 'recording.webm', { type: 'audio/webm' }))
      stream.getTracks().forEach(t => t.stop())
    }
    recorder.start()
    mediaRef.current = recorder
    setRecording(true)
  }

  function stopRecord() {
    mediaRef.current?.stop()
    setRecording(false)
  }

  async function handleSubmit() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('language', language)
      const res = await api.speechTranscribe(fd)
      setResult(res)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Speech Agent</h1>
        <span className="text-sm text-gray-500">Transcribes Hindi / Hinglish voice orders</span>
      </div>

      {/* Language selector */}
      <div className="flex gap-2">
        {['hi-IN', 'en-IN', 'mr-IN'].map(l => (
          <button key={l} onClick={() => setLanguage(l)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${language === l ? 'bg-teal-600 text-white border-teal-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
            {l}
          </button>
        ))}
      </div>

      {/* Record / Upload */}
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={recording ? stopRecord : startRecord}
          className={`py-8 rounded-xl border-2 border-dashed text-center transition-colors ${recording ? 'border-red-400 bg-red-50' : 'border-gray-300 hover:border-teal-400'}`}>
          <div className="text-3xl mb-2">{recording ? '⏹' : '🎙️'}</div>
          <p className="text-sm font-medium">{recording ? 'Stop Recording' : 'Record Audio'}</p>
          {recording && <p className="text-xs text-red-500 mt-1 animate-pulse">Recording...</p>}
        </button>

        <div
          className="py-8 rounded-xl border-2 border-dashed border-gray-300 hover:border-teal-400 text-center cursor-pointer transition-colors"
          onClick={() => inputRef.current?.click()}>
          <input ref={inputRef} type="file" accept="audio/*" className="hidden"
            onChange={e => setFile(e.target.files[0])} />
          <div className="text-3xl mb-2">📁</div>
          <p className="text-sm font-medium">Upload Audio</p>
          {file && <p className="text-xs text-gray-400 mt-1 truncate px-2">{file.name}</p>}
        </div>
      </div>

      {file && (
        <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 text-sm text-teal-800">
          Ready: {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </div>
      )}

      <button onClick={handleSubmit} disabled={!file || loading}
        className="w-full py-3 bg-teal-600 text-white rounded-xl font-medium hover:bg-teal-700 disabled:opacity-40">
        {loading ? 'Transcribing...' : 'Transcribe'}
      </button>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase">Transcript</p>
          <p className="text-lg text-gray-800 leading-relaxed">
            {result.data?.transcript || 'No transcript'}
          </p>
          <div className="flex gap-3 text-xs text-gray-400">
            <span>Language: {result.data?.language_code}</span>
            <span>•</span>
            <span>Duration: {result.duration_ms}ms</span>
          </div>
        </div>
      )}
    </div>
  )
}
