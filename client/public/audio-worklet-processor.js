/**
 * AudioWorklet processor for capturing microphone audio
 * and sending it to the main thread as PCM16 chunks.
 * 
 * Note: This is a fallback - the main hook uses ScriptProcessor
 * for broader browser compatibility.
 */

class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.bufferSize = 4096
    this.buffer = new Float32Array(this.bufferSize)
    this.bufferIndex = 0
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const inputChannel = input[0]
    
    for (let i = 0; i < inputChannel.length; i++) {
      this.buffer[this.bufferIndex++] = inputChannel[i]
      
      if (this.bufferIndex >= this.bufferSize) {
        const pcm16 = this.float32ToPcm16(this.buffer)
        this.port.postMessage({ type: 'audio', data: pcm16 })
        this.bufferIndex = 0
      }
    }

    return true
  }

  float32ToPcm16(float32Array) {
    const pcm16 = new Int16Array(float32Array.length)
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]))
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return pcm16
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor)
