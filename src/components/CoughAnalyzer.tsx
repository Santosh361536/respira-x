import React, { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Mic, Upload, Activity, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertIcon, AlertTitle } from './ui/alert';
import { Bell, CheckCircle, Info } from 'lucide-react';

export default function CoughAnalyzer() {
    const [isRecording, setIsRecording] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
    const [result, setResult] = useState<any>(null);
    const [hasAnalyzedCurrent, setHasAnalyzedCurrent] = useState(false);
    const [currentTip, setCurrentTip] = useState<string>("");
    const [alertState, setAlertState] = useState<{ variant: "primary" | "success" | "warning" | "destructive" | "info", title: string } | null>(null);
    
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<BlobPart[]>([]);
    const timerRef = useRef<any>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationFrameRef = useRef<number | null>(null);

    const healthTips = [
        "Drink hot water with honey and lemon to soothe your throat.",
        "Stay well-hydrated by drinking plenty of warm fluids throughout the day.",
        "Gargling with warm salt water can help reduce throat irritation.",
        "Rest your voice and get plenty of sleep to help your body recover.",
        "Steam inhalation can help clear nasal congestion and soothe airways.",
        "Avoid cold drinks and irritants like smoke or strong odors."
    ];

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setAudioBlob(blob);
                setHasAnalyzedCurrent(false);
                setIsRecording(false);
                setAlertState({ variant: 'primary', title: "Recording complete. Ready for analysis." });
            };

            mediaRecorder.start();
            setIsRecording(true);
            setResult(null);
            setAlertState(null);

            // Set up AudioContext for visualization
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 2048;

            audioContextRef.current = audioContext;
            analyserRef.current = analyser;

            drawVisualizer();

            timerRef.current = setTimeout(() => {
                if (mediaRecorderRef.current?.state === 'recording') {
                    stopRecording();
                }
            }, 3000); // 3 seconds max

        } catch (err) {
            setAlertState({ variant: 'destructive', title: 'Microphone access denied or unavailable.' });
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
        if (timerRef.current) clearTimeout(timerRef.current);

        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioContextRef.current?.state !== 'closed') {
            audioContextRef.current?.close();
        }

        // Clear canvas
        const canvas = canvasRef.current;
        if (canvas) {
            const canvasCtx = canvas.getContext('2d');
            if (canvasCtx) {
                canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
    };

    const drawVisualizer = () => {
        if (!canvasRef.current || !analyserRef.current) return;

        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext('2d');
        if (!canvasCtx) return;

        const analyser = analyserRef.current;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            animationFrameRef.current = requestAnimationFrame(draw);
            analyser.getByteTimeDomainData(dataArray);

            canvasCtx.fillStyle = 'white'; // Solid white background
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

            canvasCtx.lineWidth = 3;
            canvasCtx.strokeStyle = '#22c55e'; // green-500
            canvasCtx.beginPath();

            const sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * (canvas.height / 2);

                if (i === 0) {
                    canvasCtx.moveTo(x, y);
                } else {
                    canvasCtx.lineTo(x, y);
                }

                x += sliceWidth;
            }

            canvasCtx.stroke();
        };

        draw();
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setAudioBlob(file);
            setHasAnalyzedCurrent(false);
            setResult(null);
            setAlertState({ variant: 'primary', title: "Audio file uploaded successfully." });
        }
    };

    const convertToWav = async (blob: Blob): Promise<Blob> => {
        const arrayBuffer = await blob.arrayBuffer();
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        return new Blob([audioBufferToWav(audioBuffer)], { type: 'audio/wav' });
    };

    const audioBufferToWav = (buffer: AudioBuffer) => {
        const numChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const format = 1;
        const bitDepth = 16;
        const result = new Float32Array(buffer.length * numChannels);
        for (let channel = 0; channel < numChannels; channel++) {
            const channelData = buffer.getChannelData(channel);
            for (let i = 0; i < buffer.length; i++) {
                result[i * numChannels + channel] = channelData[i];
            }
        }
        const dataSize = result.length * (bitDepth / 8);
        const arrayBuffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(arrayBuffer);
        const writeString = (view: DataView, offset: number, string: string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + dataSize, true);
        writeString(view, 8, 'WAVE');
        writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, format, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true);
        view.setUint16(32, numChannels * (bitDepth / 8), true);
        view.setUint16(34, bitDepth, true);
        writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true);
        let offset = 44;
        for (let i = 0; i < result.length; i++, offset += 2) {
            let s = Math.max(-1, Math.min(1, result[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return arrayBuffer;
    };

    const analyzeAudio = async () => {
        if (!audioBlob) {
            setAlertState({ variant: 'warning', title: "Please record or upload an audio file first." });
            return;
        }
        if (hasAnalyzedCurrent) {
            setAlertState({ variant: 'warning', title: "Please record or upload new audio for another analysis." });
            return;
        }
        setIsAnalyzing(true);
        setResult(null);
        
        // Select a random health tip
        const randomTip = healthTips[Math.floor(Math.random() * healthTips.length)];
        setCurrentTip(randomTip);

        try {
            const wavBlob = await convertToWav(audioBlob);
            const formData = new FormData();
            formData.append('cough_audio', wavBlob, 'cough.wav');

            const response = await fetch((import.meta.env.VITE_API_URL || 'https://respira-x.onrender.com') + '/analyze', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            setResult(data);
            setHasAnalyzedCurrent(true);
            if (data.status.includes('ERROR')) {
                setAlertState({ variant: 'destructive', title: "Analysis returned an error." });
            } else {
                setAlertState({ variant: 'success', title: "Analysis complete." });
            }
        } catch (err) {
            setAlertState({ variant: 'info', title: "Analysis failed. Check your connection or the backend." });
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <Card className="w-full max-w-2xl mx-auto backdrop-blur-sm bg-background/50 border-white/10 shadow-2xl relative z-20">
            <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary-foreground">
                    Cough Pattern Analyzer
                </CardTitle>
                <CardDescription className="text-lg mt-2">
                    Record your cough or upload an audio file to intelligently analyze respiratory patterns.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
                {alertState && typeof document !== 'undefined' && createPortal(
                    <div className="fixed bottom-6 right-6 z-[100] w-auto min-w-[300px] max-w-sm">
                        <Alert
                            variant={alertState.variant}
                            appearance="solid"
                            size="sm"
                            close
                            onClose={() => setAlertState(null)}
                            className="flex items-center justify-between animate-in fade-in slide-in-from-bottom-5 duration-300 shadow-xl pr-2 py-2"
                        >
                            <AlertIcon>
                                {alertState.variant === 'primary' && <Bell className="h-5 w-5" />}
                                {alertState.variant === 'success' && <CheckCircle className="h-5 w-5" />}
                                {alertState.variant === 'warning' && <AlertTriangle className="h-5 w-5" />}
                                {alertState.variant === 'destructive' && <AlertCircle className="h-5 w-5" />}
                                {alertState.variant === 'info' && <Info className="h-5 w-5" />}
                            </AlertIcon>
                            <AlertTitle className="flex-1 mr-4">{alertState.title}</AlertTitle>
                        </Alert>
                    </div>,
                    document.body
                )}

                <div className="flex flex-col items-center gap-2">
                    <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full">
                        <Button
                            onClick={isRecording ? stopRecording : startRecording}
                            variant={isRecording ? "destructive" : "default"}
                            className={`w-full sm:w-auto h-14 px-8 text-lg font-semibold transition-all duration-300 ${isRecording ? 'animate-pulse ring-4 ring-destructive/50' : ''}`}
                        >
                            <Mic className={`mr-2 h-6 w-6 ${isRecording ? 'animate-bounce' : ''}`} />
                            {isRecording ? 'Recording (3s)...' : 'Record Cough'}
                        </Button>

                        <div className="relative w-full sm:w-auto">
                            <input
                                type="file"
                                accept="audio/*"
                                onChange={handleFileUpload}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                title="Upload Audio"
                            />
                            <Button variant="outline" className="w-full h-14 px-8 text-lg font-semibold border-2 hover:bg-muted/50 pointer-events-none">
                                <Upload className="mr-2 h-6 w-6" />
                                Upload Audio
                            </Button>
                        </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 italic flex items-center gap-1">
                        <Info className="h-3 w-3" />
                        Best results with a single clear cough.
                    </p>
                </div>

                <div className={`transition-all duration-300 overflow-hidden flex justify-center ${isRecording ? 'h-32 opacity-100 scale-100 mt-4' : 'h-0 opacity-0 scale-95 mt-0'}`}>
                    <canvas
                        ref={canvasRef}
                        width="400"
                        height="128"
                        className="rounded-lg bg-white border border-gray-200 shadow-inner w-full max-w-sm"
                    />
                </div>

                {audioBlob && !isRecording && (
                    <div className="flex justify-center mt-2 fade-in zoom-in duration-300">
                        <Button
                            onClick={analyzeAudio}
                            disabled={isAnalyzing}
                            className="w-full sm:w-64 h-16 text-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white border-0 shadow-lg shadow-blue-500/25 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                        >
                            {isAnalyzing ? (
                                <span className="flex items-center">
                                    <Activity className="mr-3 h-6 w-6 animate-spin" />
                                    Analyzing...
                                </span>
                            ) : (
                                <span className="flex items-center">
                                    <Activity className="mr-3 h-6 w-6 animate-pulse" />
                                    Analyze Pattern
                                </span>
                            )}
                        </Button>
                    </div>
                )}

                {result && (
                    <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500 mt-8">
                        <div className={`p-6 rounded-xl border ${result.severity === 'low' ? 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400' :
                            result.severity === 'medium' ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-400' :
                                'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400'
                            }`}>
                            <div className="flex items-start gap-4">
                                {result.severity === 'low' ? <CheckCircle2 className="h-8 w-8 mt-1" /> :
                                    result.severity === 'medium' ? <AlertTriangle className="h-8 w-8 mt-1" /> :
                                        <AlertCircle className="h-8 w-8 mt-1" />}

                                <div className="space-y-2 flex-1">
                                    <h3 className="text-2xl font-bold">{result.prediction}</h3>
                                    <div className="flex flex-wrap gap-4 text-sm font-medium opacity-80 pt-1">
                                        <span className="bg-background/50 px-3 py-1 rounded-full backdrop-blur-sm">Confidence: {result.confidence}</span>
                                        <span className="bg-background/50 px-3 py-1 rounded-full backdrop-blur-sm">Status: {result.status}</span>
                                    </div>
                                    <p className="pt-3 opacity-90 leading-relaxed text-base border-t border-current/10 mt-2 whitespace-pre-line">
                                        {result.details}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Health Tip Section */}
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex items-start gap-3">
                            <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                            <div>
                                <h4 className="font-bold text-blue-700 dark:text-blue-400 text-sm uppercase tracking-wider">Health Tip</h4>
                                <p className="text-blue-600 dark:text-blue-300 text-sm mt-1">{currentTip}</p>
                            </div>
                        </div>

                        {/* Medical Disclaimer Section */}
                        <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                            <p className="text-xs text-amber-700 dark:text-amber-500/80 leading-relaxed font-medium">
                                <span className="font-bold uppercase">Medical Disclaimer:</span> This analysis is for informational purposes only and is not accurate enough to replace professional medical diagnosis. Consulting a doctor is <span className="underline">mandatory</span> for any respiratory health concerns.
                            </p>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
