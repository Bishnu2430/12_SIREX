"""
Comprehensive Audio Analysis
Extracts speech, acoustics, and environmental intelligence from audio
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import wave
from loguru import logger

try:
    import librosa
    import numpy as np
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available. Install: pip install librosa soundfile")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not available")


class AudioAnalyzer:
    """
    Comprehensive audio analysis:
    - Speech-to-text
    - Acoustic features
    - Language detection
    - Speaker characteristics
    - Environmental sounds
    - Audio forensics
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Comprehensive audio analysis
        
        Returns:
            {
                "transcription": {...},
                "acoustic_features": {...},
                "speech_characteristics": {...},
                "environmental_analysis": {...},
                "forensics": {...}
            }
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return {"error": "Audio file not found"}
        
        results = {
            "file_info": self._get_file_info(audio_path)
        }
        
        try:
            # Convert to wav if needed for speech recognition
            wav_path = self._ensure_wav_format(audio_path)
            
            # Speech-to-text analysis
            if SPEECH_RECOGNITION_AVAILABLE:
                results["transcription"] = self._transcribe_audio(wav_path)
            
            # Acoustic analysis
            if LIBROSA_AVAILABLE:
                results["acoustic_features"] = self._extract_acoustic_features(audio_path)
                results["speech_characteristics"] = self._analyze_speech_characteristics(audio_path)
                results["environmental_analysis"] = self._analyze_environment(audio_path)
            
            # Audio forensics
            results["forensics"] = self._audio_forensics(audio_path)
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _get_file_info(self, audio_path: Path) -> Dict[str, Any]:
        """Get basic audio file information"""
        try:
            stat = audio_path.stat()
            
            info = {
                "name": audio_path.name,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "format": audio_path.suffix.lower()
            }
            
            # Try to get detailed info with ffprobe
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format', '-show_streams',
                    str(audio_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    
                    if 'format' in data:
                        info['duration_seconds'] = float(data['format'].get('duration', 0))
                        info['bit_rate'] = int(data['format'].get('bit_rate', 0))
                    
                    if 'streams' in data:
                        for stream in data['streams']:
                            if stream.get('codec_type') == 'audio':
                                info['codec'] = stream.get('codec_name')
                                info['sample_rate'] = int(stream.get('sample_rate', 0))
                                info['channels'] = stream.get('channels')
                                break
            
            except Exception as e:
                logger.debug(f"FFprobe info extraction failed: {e}")
            
            return info
        
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}
    
    def _ensure_wav_format(self, audio_path: Path) -> Path:
        """Convert audio to WAV format for speech recognition"""
        if audio_path.suffix.lower() == '.wav':
            return audio_path
        
        # Convert using ffmpeg
        wav_path = audio_path.with_suffix('.wav')
        
        try:
            cmd = [
                'ffmpeg', '-i', str(audio_path),
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',       # Mono
                '-y',             # Overwrite
                str(wav_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            return wav_path
        
        except Exception as e:
            logger.warning(f"Failed to convert to WAV: {e}")
            return audio_path
    
    def _transcribe_audio(self, wav_path: Path) -> Dict[str, Any]:
        """Transcribe speech to text using multiple engines"""
        transcriptions = {}
        
        try:
            with sr.AudioFile(str(wav_path)) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
                
                # Try Google Speech Recognition
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    transcriptions["google"] = {
                        "text": text,
                        "language": "en-US",
                        "confidence": "high",
                        "engine": "Google Speech Recognition"
                    }
                except sr.UnknownValueError:
                    transcriptions["google"] = {
                        "error": "Speech unintelligible",
                        "engine": "Google Speech Recognition"
                    }
                except sr.RequestError as e:
                    logger.error(f"Google SR failed: {e}")
                
                # Try Sphinx (offline)
                try:
                    text = self.recognizer.recognize_sphinx(audio_data)
                    transcriptions["sphinx"] = {
                        "text": text,
                        "language": "en-US",
                        "engine": "CMU Sphinx (offline)"
                    }
                except:
                    pass
                
                # Extract best transcription
                best_text = ""
                if "google" in transcriptions and "text" in transcriptions["google"]:
                    best_text = transcriptions["google"]["text"]
                elif "sphinx" in transcriptions and "text" in transcriptions["sphinx"]:
                    best_text = transcriptions["sphinx"]["text"]
                
                transcriptions["best_transcription"] = best_text
                transcriptions["word_count"] = len(best_text.split()) if best_text else 0
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            transcriptions["error"] = str(e)
        
        return transcriptions
    
    def _extract_acoustic_features(self, audio_path: Path) -> Dict[str, Any]:
        """Extract acoustic features using librosa"""
        if not LIBROSA_AVAILABLE:
            return {}
        
        try:
            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)
            
            features = {
                "duration_seconds": float(len(y) / sr),
                "sample_rate": int(sr),
                "total_samples": len(y),
            }
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features["spectral_centroid_mean"] = float(np.mean(spectral_centroids))
            features["spectral_centroid_std"] = float(np.std(spectral_centroids))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features["zero_crossing_rate_mean"] = float(np.mean(zcr))
            
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            features["rms_energy_mean"] = float(np.mean(rms))
            features["rms_energy_max"] = float(np.max(rms))
            
            # Tempo estimation
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features["estimated_tempo_bpm"] = float(tempo)
            
            # Mel-frequency cepstral coefficients (MFCCs)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(min(5, mfccs.shape[0])):
                features[f"mfcc_{i+1}_mean"] = float(np.mean(mfccs[i]))
            
            # Chroma features (for music/pitch)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features["chroma_mean"] = float(np.mean(chroma))
            
            return features
        
        except Exception as e:
            logger.error(f"Acoustic feature extraction failed: {e}")
            return {"error": str(e)}
    
    def _analyze_speech_characteristics(self, audio_path: Path) -> Dict[str, Any]:
        """Analyze speech-specific characteristics"""
        if not LIBROSA_AVAILABLE:
            return {}
        
        try:
            y, sr = librosa.load(str(audio_path), sr=None)
            
            characteristics = {}
            
            # Pitch analysis
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Get average pitch
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                characteristics["pitch_mean_hz"] = float(np.mean(pitch_values))
                characteristics["pitch_std_hz"] = float(np.std(pitch_values))
                characteristics["pitch_min_hz"] = float(np.min(pitch_values))
                characteristics["pitch_max_hz"] = float(np.max(pitch_values))
                
                # Rough gender estimation based on pitch
                avg_pitch = np.mean(pitch_values)
                if avg_pitch < 165:
                    characteristics["estimated_speaker_gender"] = "likely male"
                elif avg_pitch > 165:
                    characteristics["estimated_speaker_gender"] = "likely female"
                else:
                    characteristics["estimated_speaker_gender"] = "uncertain"
            
            # Speech rate estimation (rough)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            characteristics["speech_rate_estimate"] = float(tempo)
            
            # Voice activity detection
            rms = librosa.feature.rms(y=y)[0]
            threshold = np.mean(rms) * 0.5
            voice_segments = np.sum(rms > threshold) / len(rms)
            characteristics["voice_activity_ratio"] = float(voice_segments)
            
            return characteristics
        
        except Exception as e:
            logger.error(f"Speech characteristics analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_environment(self, audio_path: Path) -> Dict[str, Any]:
        """Analyze environmental sounds and background"""
        if not LIBROSA_AVAILABLE:
            return {}
        
        try:
            y, sr = librosa.load(str(audio_path), sr=None)
            
            environment = {}
            
            # Noise level analysis
            rms = librosa.feature.rms(y=y)[0]
            environment["noise_level"] = "low" if np.mean(rms) < 0.02 else "medium" if np.mean(rms) < 0.05 else "high"
            
            # Spectral rolloff (frequency distribution)
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            environment["spectral_rolloff_mean"] = float(np.mean(rolloff))
            
            # Environment estimation based on acoustic features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            
            if spectral_centroid < 2000:
                environment["estimated_setting"] = "indoor/enclosed space"
            elif spectral_centroid > 4000:
                environment["estimated_setting"] = "outdoor/open space"
            else:
                environment["estimated_setting"] = "mixed/uncertain"
            
            return environment
        
        except Exception as e:
            logger.error(f"Environmental analysis failed: {e}")
            return {"error": str(e)}
    
    def _audio_forensics(self, audio_path: Path) -> Dict[str, Any]:
        """Audio forensics - detect editing, splicing, etc."""
        forensics = {}
        
        if not LIBROSA_AVAILABLE:
            return forensics
        
        try:
            y, sr = librosa.load(str(audio_path), sr=None)
            
            # Check for discontinuities (possible editing)
            diff = np.diff(y)
            large_jumps = np.sum(np.abs(diff) > np.std(diff) * 5)
            forensics["discontinuities_detected"] = int(large_jumps)
            forensics["editing_likelihood"] = "high" if large_jumps > 10 else "low"
            
            # Dynamic range
            forensics["dynamic_range_db"] = float(20 * np.log10(np.max(np.abs(y)) / (np.mean(np.abs(y)) + 1e-10)))
            
            # Clipping detection
            clipping_ratio = np.sum(np.abs(y) > 0.99) / len(y)
            forensics["clipping_ratio"] = float(clipping_ratio)
            forensics["clipping_detected"] = clipping_ratio > 0.001
            
            return forensics
        
        except Exception as e:
            logger.error(f"Audio forensics failed: {e}")
            return {"error": str(e)}
    
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Extract audio track from video"""
        try:
            video_path = Path(video_path)
            
            if output_path is None:
                output_path = video_path.with_suffix('.wav')
            
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            logger.info(f"✓ Audio extracted: {output_path}")
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None