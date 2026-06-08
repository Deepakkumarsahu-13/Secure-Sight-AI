import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';

// 💡 If deploying frontend to Netlify, host your Flask backend on Render.com and paste your Render URL below!
const PRODUCTION_BACKEND_URL = 'https://secure-sight-ai-1.onrender.com'; 

const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000'
  : PRODUCTION_BACKEND_URL;

// ── Helpers ────────────────────────────────────────────────────────────────
const fmtTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

const confColor = (score) => {
  if (score >= 70) return '#ff3d6e';
  if (score >= 40) return '#ffb300';
  return '#00e5a0';
};

const renderPointWiseText = (text) => {
  if (!text) return '[No clear text extracted]';
  let lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length <= 1) {
    lines = text.split(/\.\s+/).map(l => l.trim()).filter(l => l.length > 0);
  }
  return (
    <ul style={{ margin: 0, paddingLeft: 18, listStyleType: 'square' }}>
      {lines.map((line, idx) => {
        const displayLine = line.endsWith('.') ? line : line + '.';
        return (
          <li key={idx} style={{ marginBottom: 6, color: 'var(--text-dim)' }}>
            {displayLine}
          </li>
        );
      })}
    </ul>
  );
};

const downloadFile = async (url, filename) => {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    console.error("Secure download failed:", error);
    // Fallback: Open in new tab if blob fetch fails
    window.open(url, '_blank');
  }
};

// ── Default AI chat messages ───────────────────────────────────────────────
const WELCOME_MSG = {
  role: 'bot', 
  id: 0,
  text: '👋 Hi! I\'m the Secure Sight AI assistant. Ask me about your scan history, privacy tips, Indian DPDP Act guidelines, what sensitive PII to watch for, or anything about offline image security.',
  time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
};

const QUICK_QUESTIONS = [
  'Show me scan summary',
  'What is Aadhaar card?',
  'Privacy tips for sharing images',
  'How does targeted blur work?',
  'What are the most risky PII types?'
];

// ── Donut SVG ──────────────────────────────────────────────────────────────
function Donut({ sensitive, clean, illegal }) {
  const total = sensitive + clean || 1;
  const r = 52, cx = 70, cy = 70, stroke = 14;
  const circ = 2 * Math.PI * r;
  
  const dangerRatio = sensitive / total;
  const safeRatio = clean / total;
  
  const dangerDash = dangerRatio * circ;
  const safeDash = safeRatio * circ;
  
  return (
    <div className="donut-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx={cx} cy={cy} r={r} fill="none" strokeWidth={stroke} stroke="#0b1b38" />
        <circle cx={cx} cy={cy} r={r} fill="none" strokeWidth={stroke}
          stroke="#00e5a0" strokeDasharray={`${safeDash} ${circ - safeDash}`}
          strokeDashoffset={circ / 4} strokeLinecap="butt" />
        <circle cx={cx} cy={cy} r={r} fill="none" strokeWidth={stroke}
          stroke="#ff3d6e" strokeDasharray={`${dangerDash} ${circ - dangerDash}`}
          strokeDashoffset={circ / 4 - safeDash} strokeLinecap="butt" />
        <text x={cx} y={cy - 8} textAnchor="middle" fill="#e1ebf5" fontSize="22" fontWeight="700">{sensitive + clean}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill="#7da0c4" fontSize="10">SCANS</text>
      </svg>
      <div className="donut-legend">
        <span><span className="legend-dot" style={{ background: '#ff3d6e' }} />Sensitive PII: {sensitive}</span>
        <span><span className="legend-dot" style={{ background: '#00e5a0' }} />Clean Files: {clean}</span>
        {illegal > 0 && (
          <span><span className="legend-dot" style={{ background: '#ff3d6e', boxShadow: '0 0 8px #ff3d6e' }} />Illegal Weapons: {illegal}</span>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
function App() {
  const [activeTab, setActiveTab] = useState('scan');

  // ── Scanner state ──────────────────────────────────────────────────────────
  const [file, setFile]                   = useState(null);
  const [previewUrl, setPreviewUrl]       = useState(null);
  const [filename, setFilename]           = useState('');
  const [status, setStatus]               = useState('');
  const [statusType, setStatusType]       = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [blurredImageUrl, setBlurredImageUrl] = useState(null);
  const [showPopup, setShowPopup]         = useState(false);
  const [loading, setLoading]             = useState(false);
  const [progress, setProgress]           = useState(0);
  const fileInputRef = useRef();

  // ── History state ──────────────────────────────────────────────────────────
  const [history, setHistory]             = useState([]);
  const [histSearch, setHistSearch]       = useState('');
  const [histFilter, setHistFilter]       = useState('all');

  // ── Stats state ────────────────────────────────────────────────────────────
  const [stats, setStats]                 = useState(null);

  // ── Settings state ────────────────────────────────────────────────────────
  const [settings, setSettings]           = useState(null);
  const [settingsSaved, setSettingsSaved] = useState(false);

  // ── Chat state ─────────────────────────────────────────────────────────────
  const [chatMsgs, setChatMsgs]           = useState([WELCOME_MSG]);
  const [chatInput, setChatInput]         = useState('');
  const [chatLoading, setChatLoading]     = useState(false);
  const chatEndRef = useRef();

  // ── Live Guard Camera state ────────────────────────────────────────────────
  const [isGuardActive, setIsGuardActive] = useState(false);
  const [detectedRegions, setDetectedRegions] = useState([]);
  const [threatCount, setThreatCount]     = useState(0);
  const [piiCount, setPiiCount]           = useState(0);
  const [isThreatActive, setIsThreatActive] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);
  const intervalRef = useRef(null);
  const regionsRef = useRef([]);

  // Keep regionsRef updated for the animation frame loop
  useEffect(() => {
    regionsRef.current = detectedRegions;
  }, [detectedRegions]);

  // Deactivate camera on tab change or unmount
  useEffect(() => {
    if (activeTab !== 'camera') {
      stopCamera();
    }
  }, [activeTab]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // ── Load data on tab change ────────────────────────────────────────────────
  useEffect(() => {
    if (activeTab === 'history') fetchHistory();
    if (activeTab === 'stats')   fetchStats();
    if (activeTab === 'settings' && !settings) fetchSettings();
  }, [activeTab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMsgs]);

  // ── Fetch helpers ──────────────────────────────────────────────────────────
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API}/history`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch { setHistory([]); }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API}/stats`);
      const data = await res.json();
      setStats(data);
    } catch { setStats(null); }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API}/settings`);
      const data = await res.json();
      setSettings(data);
    } catch {
      setSettings({
        blur_strength: 99, confidence_threshold: 40,
        auto_blur: true, save_redacted: true,
        ocr_fallback: true, watermark: true,
        max_history: 50, language: 'eng'
      });
    }
  };

  // ── Scanner logic ──────────────────────────────────────────────────────────
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) loadFile(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) loadFile(dropped);
  };

  const loadFile = (f) => {
    setFile(f); 
    setPreviewUrl(URL.createObjectURL(f));
    setAnalysisResult(null); 
    setBlurredImageUrl(null);
    setShowPopup(false); 
    setProgress(0);
    log(`Selected target: ${f.name}`, '');
  };

  const log = (msg, type = '') => { setStatus(msg); setStatusType(type); };

  const runPipeline = async () => {
    if (!file || loading) return;
    setLoading(true); 
    setAnalysisResult(null); 
    setBlurredImageUrl(null); 
    setShowPopup(false);
    
    try {
      setProgress(20); 
      log('Securing connection and uploading document target...', 'warn');
      const fname = await uploadImage();
      if (!fname) { setLoading(false); return; }

      setProgress(50); 
      log('Scanning payload for sensitive details & weapons/hazards...', 'warn');
      const analysis = await checkImage(fname);
      if (!analysis) { setLoading(false); return; }

      setAnalysisResult(analysis);

      // Explicit alert if weapon or illegal item detected
      if (analysis.is_illegal) {
        setProgress(70);
        log(`🚨 SECURITY ALERT: Threat detected! Analyzing hazard type...`, 'error');
        setShowPopup(true);
        // We blur whatever sensitive region/keyword matched
        await blurImageReq(fname, analysis.regions || []);
      } else if (analysis.is_sensitive) {
        setProgress(75);
        log(`⚠ Sensitive PII identified (${analysis.analysis_method}). Commencing targeted pixel redaction...`, 'warn');
        await blurImageReq(fname, analysis.regions || []);
      } else {
        log('✓ Analysis complete — File is clean, verified, and safe to share.', 'success');
      }
      setProgress(100);
    } catch (err) {
      log('Execution crashed: ' + err.message, 'error');
    }
    setLoading(false);
  };

  const uploadImage = async () => {
    const formData = new FormData();
    formData.append('image', file);
    try {
      const res = await fetch(`${API}/upload-image`, { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok) { log('Upload failed: ' + data.error, 'error'); return null; }
      setFilename(data.filename);
      return data.filename;
    } catch { 
      log('Offline Alert: Cannot communicate with the scan service. Ensure backend is running.', 'error'); 
      return null; 
    }
  };

  const checkImage = async (fname) => {
    try {
      const res = await fetch(`${API}/check-image`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: fname }),
      });
      const data = await res.json();
      if (!res.ok) { log('Analysis failed: ' + data.error, 'error'); return null; }
      return data;
    } catch { 
      log('Verification failure: Scan engine crashed.', 'error'); 
      return null; 
    }
  };

  const blurImageReq = async (fname, regions = []) => {
    try {
      const res = await fetch(`${API}/blur-image`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: fname, regions }),
      });
      const data = await res.json();
      if (!res.ok) { log('Blur failed: ' + data.error, 'error'); return; }
      setBlurredImageUrl(data.blurred_url);
      log(`✓ Targeted Redaction Complete — Blurred ${data.regions_blurred} precise regions. Rest of document remains visible.`, 'success');
    } catch { 
      log('Offline Redaction Failure: Cannot process OpenCV Gaussian blur.', 'error'); 
    }
  };

  // ── History logic ──────────────────────────────────────────────────────────
  const filteredHistory = history.filter(r => {
    const matchSearch = r.original_name?.toLowerCase().includes(histSearch.toLowerCase()) ||
                        r.document_type?.toLowerCase().includes(histSearch.toLowerCase());
    
    const matchFilter = histFilter === 'all' ? true
                      : histFilter === 'sensitive' ? r.is_sensitive
                      : histFilter === 'threats' ? r.is_illegal
                      : !r.is_sensitive;
    return matchSearch && matchFilter;
  });

  const deleteHistoryItem = async (id) => {
    try {
      await fetch(`${API}/history/${id}`, { method: 'DELETE' });
      setHistory(h => h.filter(r => r.id !== id));
    } catch {}
  };

  const clearHistory = async () => {
    if (!window.confirm('Delete all scan records permanently?')) return;
    try {
      await fetch(`${API}/history`, { method: 'DELETE' });
      setHistory([]);
    } catch {}
  };

  // ── Live Guard Camera logic ────────────────────────────────────────────────
  const startCamera = async () => {
    setDetectedRegions([]);
    setThreatCount(0);
    setPiiCount(0);
    setIsThreatActive(false);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().then(() => {
            setIsGuardActive(true);
            startRenderLoop();
            startAnalysisLoop();
          }).catch(err => {
            console.error("Video play failed:", err);
          });
        };
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("Could not access webcam. Please check camera permissions in your browser.");
    }
  };

  const stopCamera = () => {
    setIsGuardActive(false);
    setIsThreatActive(false);
    setDetectedRegions([]);
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startRenderLoop = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const render = () => {
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        ctx.filter = 'none';
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const currentRegions = regionsRef.current;
        currentRegions.forEach(r => {
          const rx = r.x * canvas.width;
          const ry = r.y * canvas.height;
          const rw = r.w * canvas.width;
          const rh = r.h * canvas.height;
          
          ctx.save();
          ctx.beginPath();
          ctx.rect(rx, ry, rw, rh);
          ctx.clip();
          ctx.filter = 'blur(15px)';
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          ctx.restore();
          
          ctx.strokeStyle = r.isIllegal ? '#ff3d6e' : '#ffb300';
          ctx.lineWidth = 3;
          ctx.strokeRect(rx, ry, rw, rh);
          
          ctx.fillStyle = r.isIllegal ? 'rgba(255, 61, 110, 0.85)' : 'rgba(255, 179, 0, 0.85)';
          const text = `${r.label.toUpperCase()} (${r.confidence}%)`;
          ctx.font = 'bold 12px monospace';
          const textWidth = ctx.measureText(text).width;
          const labelY = ry - 20 >= 0 ? ry - 20 : ry;
          ctx.fillRect(rx, labelY, textWidth + 10, 20);
          
          ctx.fillStyle = '#030812';
          ctx.fillText(text, rx + 5, labelY + 14);
        });
      }
      animationFrameRef.current = requestAnimationFrame(render);
    };
    animationFrameRef.current = requestAnimationFrame(render);
  };

  const startAnalysisLoop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    intervalRef.current = setInterval(async () => {
      const canvas = canvasRef.current;
      if (!canvas || !streamRef.current) return;
      
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        
        const formData = new FormData();
        formData.append('image', blob, 'live_frame.jpg');
        
        try {
          const uploadRes = await fetch(`${API}/upload-image`, {
            method: 'POST',
            body: formData
          });
          if (!uploadRes.ok) return;
          const uploadData = await uploadRes.json();
          const fname = uploadData.filename;
          
          const checkRes = await fetch(`${API}/check-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: fname })
          });
          if (!checkRes.ok) return;
          const checkData = await checkRes.json();
          
          if (checkData.regions && checkData.regions.length > 0) {
            const mappedRegions = checkData.regions.map(r => {
              const labelLower = r.label.toLowerCase();
              const isIllegal = checkData.is_illegal || labelLower.includes('weapon') || labelLower.includes('hazard') || labelLower.includes('contraband');
              return {
                label: r.label,
                x: r.x,
                y: r.y,
                w: r.w,
                h: r.h,
                confidence: checkData.confidence_score || 90,
                isIllegal: isIllegal
              };
            });
            
            setDetectedRegions(mappedRegions);
            
            const illegalCount = mappedRegions.filter(r => r.isIllegal).length;
            const sensitiveCount = mappedRegions.filter(r => !r.isIllegal).length;
            setThreatCount(illegalCount);
            setPiiCount(sensitiveCount);
            
            if (illegalCount > 0) {
              setIsThreatActive(true);
            }
          } else {
            setDetectedRegions([]);
            setThreatCount(0);
            setPiiCount(0);
          }
        } catch (err) {
          console.error("Error analyzing camera frame:", err);
        }
      }, 'image/jpeg', 0.6);
    }, 700);
  };

  // ── Settings logic ─────────────────────────────────────────────────────────
  const saveSettings = async () => {
    try {
      await fetch(`${API}/settings`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      setSettingsSaved(true);
      setTimeout(() => setSettingsSaved(false), 2000);
    } catch {}
  };
  
  const setSetting = (key, val) => setSettings(s => ({ ...s, [key]: val }));

  // ── AI Chat logic ──────────────────────────────────────────────────────────
  const sendChat = useCallback(async (text) => {
    const msg = text || chatInput.trim();
    if (!msg || chatLoading) return;
    setChatInput('');

    const userMsg = {
      role: 'user', 
      id: Date.now(), 
      text: msg,
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    };
    
    setChatMsgs(m => [...m, userMsg]);
    setChatLoading(true);

    try {
      const response = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          history: chatMsgs.filter(m => m.id !== 0) // exclude welcome message
        }),
      });
      
      const data = await response.json();
      const reply = data.reply || 'Sorry, I could not get a response.';
      
      setChatMsgs(m => [...m, {
        role: 'bot', 
        id: Date.now() + 1, 
        text: reply,
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch {
      setChatMsgs(m => [...m, {
        role: 'bot', 
        id: Date.now() + 1,
        text: '❌ Network Failure: Unable to contact the Chat service. Make sure the local backend server is running.',
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
      }]);
    }
    setChatLoading(false);
  }, [chatInput, chatLoading, chatMsgs]);

  // ══════════════════════════════════════════════════════════════════════════
  return (
    <div className="app">
      <div className="scanline" />

      {/* Critical Threat Fullscreen Warning */}
      {isThreatActive && (
        <div className="critical-fullscreen-alarm">
          <div className="alarm-flash-box">
            <div className="alarm-flash-icon">🚨</div>
            <h2 className="alarm-flash-title">CRITICAL SECURITY BREACH</h2>
            <p className="alarm-flash-text">
              WEAPON DETECTED IN CAMERA FEED. LOCAL PRIVACY PERIMETER ENGAGED.
            </p>
            <div className="alarm-flash-sub">
              REDACTION SHIELD ACTIVE · TELEMETRY LOGGED
            </div>
            <button className="btn-confirm" onClick={() => setIsThreatActive(false)} style={{ marginTop: '20px' }}>
              ACKNOWLEDGE WARNING
            </button>
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-brand">
          <span className="nav-icon">🛡</span>
          <div>
            <div className="nav-title">SECURE SIGHT AI</div>
            <div className="nav-sub">OFFLINE SYSTEM · TAILORED PII BLUR · WEAPONS SAFETY SCREEN</div>
          </div>
        </div>
        <div className="nav-badge"><span className="dot" /> SECURE NODE ONLINE</div>
      </nav>

      {/* Tab Navigation */}
      <div className="tab-nav">
        {[
          { key: 'scan',     label: '🔍 SCANNER' },
          { key: 'camera',   label: '🎥 LIVE GUARD' },
          { key: 'history',  label: '📋 HISTORY',  badge: history.length || null },
          { key: 'stats',    label: '📊 ANALYTICS' },
          { key: 'chat',     label: '🤖 AI CHAT' },
          { key: 'settings', label: '⚙ SETTINGS' },
        ].map(t => (
          <button
            key={t.key}
            className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
            {t.badge ? <span className="tab-badge">{t.badge}</span> : null}
          </button>
        ))}
      </div>

      {/* Security Threat Alert Overlay Popup */}
      {showPopup && (
        <div className="popup-overlay">
          <div className="popup-box">
            <div className="popup-icon">🚨</div>
            <h3 className="popup-title">CRITICAL SECURITY ALERT</h3>
            <p className="popup-body">
              {analysisResult?.reason || 'Dangerous content or safety violation identified.'}<br /><br />
              Secure Sight AI strictly prohibits illegal uploads or weapons. Sensitive components and details have been blurred using precision targeting.
            </p>
            <button className="btn-confirm" onClick={() => setShowPopup(false)}>ACKNOWLEDGE &amp; VIEW REDACTED FILE</button>
          </div>
        </div>
      )}

      <main className="container">

        {/* ── SCANNER TAB ───────────────────────────────────────────────── */}
        {activeTab === 'scan' && (
          <>
            <section className={`panel upload-panel ${analysisResult?.is_illegal ? 'weapon-alarm-card' : ''}`}>
              <div className="panel-label">SECURE TARGET INPUT</div>
              
              {analysisResult?.is_illegal && (
                <div className="alarm-banner">
                  <span className="alarm-icon">🚨</span>
                  <div>
                    <div className="alarm-title">HAZARDOUS WEAPON/CONTENT FLAGGED</div>
                    <div className="alarm-desc">{analysisResult.reason}. Redaction protocols initialized.</div>
                  </div>
                </div>
              )}

              <div className="drop-zone" onDragOver={e => e.preventDefault()} onDrop={handleDrop} onClick={() => fileInputRef.current.click()}>
                <div className="drop-icon">📁</div>
                <div className="drop-title">{file ? file.name : 'Drop document image here or click to browse'}</div>
                <div className="drop-sub">ACCEPTED: PNG · JPG · JPEG (OFFLINE VERIFIED)</div>
              </div>
              <input type="file" accept="image/*" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileChange} />
              
              {file && (
                <div style={{ textAlign: 'center', marginTop: 20 }}>
                  <button className="btn-primary" onClick={runPipeline} disabled={loading}>
                    {loading ? '⏳ SHIELDING...' : '▶ DISARM & SAFEGUARD'}
                  </button>
                </div>
              )}
              
              {progress > 0 && (
                <div className="progress-wrap">
                  <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
                  <div className="progress-label">{progress}%</div>
                </div>
              )}
              
              {status && (
                <div className="log-terminal">
                  <span className="log-prefix">&gt;&gt;</span>
                  <span className={`log-msg ${statusType}`}>{status}</span>
                </div>
              )}
            </section>

            {previewUrl && (
              <section className="images-grid">
                <div className="img-card">
                  <div className="img-card-header">◈ RAW INPUT TARGET</div>
                  <div className="img-card-body"><img src={previewUrl} alt="Original" className="preview-img" /></div>
                </div>
                <div className={`img-card ${blurredImageUrl ? 'protected' : ''}`}>
                  <div className="img-card-header protected-h">✓ DISARMED REDACTED OUTPUT</div>
                  <div className="img-card-body">
                    {blurredImageUrl ? (
                      <>
                        <img src={blurredImageUrl} alt="Redacted" className="preview-img" />
                        <button onClick={() => downloadFile(blurredImageUrl, `secure_${filename}`)} className="btn-download" style={{ border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}>
                          ⬇ DOWNLOAD REDACTED FILE
                        </button>
                      </>
                    ) : analysisResult && !analysisResult.is_sensitive ? (
                      <div className="placeholder safe-msg">✓ NO THREAT DETECTED — REVEALING FULL IMAGE</div>
                    ) : (
                      <div className="placeholder">[ AWAITING PROCESS ]</div>
                    )}
                  </div>
                </div>
              </section>
            )}

            {analysisResult && (
              <section className="panel analysis-panel">
                <div className="panel-label">DIAGNOSTIC INTEGRITY REPORT</div>

                {analysisResult.document_type && analysisResult.document_type !== 'unknown' && (
                  <div style={{ marginBottom: 16, padding: '10px 16px', background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.2)', borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: '.78rem', color: 'var(--accent)' }}>
                    📄 VERIFIED CLASSIFICATION: {analysisResult.document_type.toUpperCase()}
                    {analysisResult.reason && <span style={{ color: 'var(--text)', marginLeft: 16 }}>— {analysisResult.reason}</span>}
                  </div>
                )}

                <div className="metrics-grid">
                  <div className="metric-box">
                    <div className="metric-label">PII LEAK THREAT</div>
                    <div className={`metric-value ${analysisResult.is_sensitive ? 'danger' : 'safe'}`}>{analysisResult.is_sensitive ? '⚠ YES' : '✓ NO'}</div>
                  </div>
                  <div className="metric-box">
                    <div className="metric-label">WEAPON / ILLEGAL CONTENT</div>
                    <div className={`metric-value ${analysisResult.is_illegal ? 'danger' : 'safe'}`}>{analysisResult.is_illegal ? '🚨 DETECTED' : '✓ NONE'}</div>
                  </div>
                  <div className="metric-box">
                    <div className="metric-label">REDACTED REGIONS</div>
                    <div className={`metric-value ${(analysisResult.regions || []).length > 0 ? 'danger' : 'safe'}`}>{(analysisResult.regions || []).length}</div>
                  </div>
                </div>

                <div className="conf-wrap">
                  <div className="conf-label-row"><span>THREAT POTENTIAL SCORE</span><span>{analysisResult.confidence_score}%</span></div>
                  <div className="conf-bar">
                    <div className="conf-fill" style={{ width: `${analysisResult.confidence_score}%`, background: confColor(analysisResult.confidence_score) }} />
                  </div>
                </div>

                <div className="section-label">DETECTED CRITICAL METRIC TAGS:</div>
                <div className="kw-row">
                  {analysisResult.detected_keywords?.length > 0
                    ? analysisResult.detected_keywords.map((k, i) => <span className="kw-tag" key={i}>{k.toUpperCase()}</span>)
                    : <span className="kw-none">NO EXPOSURES FOUND</span>}
                </div>

                {analysisResult.regions?.length > 0 && (
                  <>
                    <div className="section-label">PRECISE REDACTED REGIONS:</div>
                    <div style={{ marginBottom: 18 }}>
                      {analysisResult.regions.map((r, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0', borderBottom: '1px solid rgba(0, 229, 255, 0.05)', fontFamily: 'var(--font-mono)', fontSize: '.72rem' }}>
                          <span style={{ background: 'rgba(255,61,110,.15)', border: '1px solid rgba(255,61,110,.4)', color: 'var(--danger)', padding: '2px 8px', borderRadius: 4, minWidth: 24, textAlign: 'center' }}>{i + 1}</span>
                          <span style={{ color: 'var(--text)', flex: 1 }}>{r.label}</span>
                          <span style={{ color: 'var(--text-dim)' }}>x:{(r.x * 100).toFixed(0)}% y:{(r.y * 100).toFixed(0)}% w:{(r.w * 100).toFixed(0)}% h:{(r.h * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                <div className="section-label">RAW EXPOSURES EXTRACTED:</div>
                <div className="ocr-box">{renderPointWiseText(analysisResult.extracted_text)}</div>
                <div style={{ marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: '.65rem', color: 'var(--text-dim)', textAlign: 'right' }}>
                  ANALYSIS ENGINE: {(analysisResult.analysis_method || 'LOCAL-OFFLINE-OCR').toUpperCase()}
                </div>
              </section>
            )}
          </>
        )}

        {/* ── LIVE GUARD TAB ─────────────────────────────────────────────── */}
        {activeTab === 'camera' && (
          <section className={`panel camera-panel ${isThreatActive ? 'weapon-alarm-card' : ''}`}>
            <div className="panel-label">🎥 LIVE GUARD WEBCAM SCREEN</div>

            {isThreatActive && (
              <div className="alarm-banner live-alarm">
                <span className="alarm-icon">🚨</span>
                <div>
                  <div className="alarm-title">CRITICAL SAFETY THREAT DECLARED</div>
                  <div className="alarm-desc">Visual weapon detection alert active! Real-time redacting applied.</div>
                </div>
              </div>
            )}

            <div className="camera-grid">
              <div className="camera-feed-card">
                <div className="img-card-header">
                  LIVE CAPTURE &amp; REDACTION FEED
                  <span style={{ float: 'right', color: isGuardActive ? 'var(--safe)' : 'var(--text-dim)' }}>
                    ● {isGuardActive ? 'ACTIVE GUARD PROTOCOL' : 'STANDBY'}
                  </span>
                </div>
                <div className="img-card-body camera-body">
                  <video
                    ref={videoRef}
                    style={{ display: 'none' }}
                    autoPlay
                    playsInline
                    muted
                  />
                  <canvas
                    ref={canvasRef}
                    width="640"
                    height="480"
                    style={{
                      width: '100%',
                      maxWidth: '640px',
                      height: 'auto',
                      borderRadius: '8px',
                      border: '1px solid var(--border)',
                      display: isGuardActive ? 'block' : 'none'
                    }}
                  />
                  {!isGuardActive && (
                    <div className="camera-placeholder" style={{ textAlign: 'center', padding: '40px 20px' }}>
                      <div className="drop-icon" style={{ fontSize: '3rem', marginBottom: '15px' }}>📷</div>
                      <div className="drop-title" style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>Camera Guard is Deactivated</div>
                      <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', maxWidth: '400px', margin: '12px auto', lineHeight: '1.5' }}>
                        Activate Live Guard to establish a local visual privacy perimeter. Weapon detection and PII scanning will run in real-time.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="camera-info-card">
                <div className="img-card-header">GUARD DIAGNOSTICS &amp; THREATS</div>
                <div className="img-card-body" style={{ display: 'block', padding: '20px' }}>
                  <div style={{ marginBottom: '20px' }}>
                    <button
                      id="btn-toggle-camera"
                      className={isGuardActive ? 'btn-danger' : 'btn-primary'}
                      onClick={isGuardActive ? stopCamera : startCamera}
                      style={{ width: '100%', padding: '14px', fontSize: '0.9rem', cursor: 'pointer' }}
                    >
                      {isGuardActive ? '🔴 DEACTIVATE LIVE GUARD' : '⚡ ACTIVATE LIVE GUARD'}
                    </button>
                  </div>

                  <div className="metrics-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '10px', display: 'grid' }}>
                    <div className="metric-box">
                      <div className="metric-label">Threats Detected</div>
                      <div className={`metric-value ${threatCount > 0 ? 'danger' : 'safe'}`}>
                        {threatCount}
                      </div>
                    </div>
                    <div className="metric-box">
                      <div className="metric-label">PII Redactions</div>
                      <div className="metric-value" style={{ color: 'var(--accent)' }}>
                        {piiCount}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '20px' }}>
                    <div className="section-label">Active Redacted Items</div>
                    <div className="ocr-box" style={{ minHeight: '120px', background: 'rgba(3, 8, 18, 0.8)' }}>
                      {detectedRegions.length === 0 ? (
                        <span className="placeholder">No threats or PII detected in view.</span>
                      ) : (
                        <ul style={{ margin: 0, paddingLeft: '20px', listStyleType: 'square' }}>
                          {detectedRegions.map((r, idx) => (
                            <li key={idx} style={{ color: r.isIllegal ? 'var(--danger)' : 'var(--warning)', marginBottom: '5px' }}>
                              <strong>{r.label}</strong>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>

                  <div style={{ marginTop: '20px', fontSize: '0.75rem', color: 'var(--text-dim)', lineHeight: '1.5' }}>
                    <div className="section-label">Redaction Status</div>
                    <p>
                      🎥 Zero-latency canvas filter blur is applied directly to detected bounding boxes.
                      Frame telemetry scans the local backend node every 700ms.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── HISTORY TAB ───────────────────────────────────────────────── */}
        {activeTab === 'history' && (
          <section className="panel history-panel">
            <div className="panel-label purple">LOCAL SECURITY LOGS</div>

            <div className="history-toolbar">
              <input className="history-search" placeholder="🔍 Search by target name or document type..."
                value={histSearch} onChange={e => setHistSearch(e.target.value)} />
              <select className="history-filter" value={histFilter} onChange={e => setHistFilter(e.target.value)}>
                <option value="all">ALL SHIELDS</option>
                <option value="sensitive">SENSITIVE PII</option>
                <option value="threats">CRITICAL WEAPONS</option>
                <option value="clean">CLEAN FILES</option>
              </select>
              <button className="btn-secondary" onClick={fetchHistory}>↻ REFRESH</button>
              {history.length > 0 && <button className="btn-danger" onClick={clearHistory}>🗑 WIPE RECORDS</button>}
            </div>

            {filteredHistory.length === 0 ? (
              <div className="history-empty">
                {history.length === 0
                  ? '📭 No operations completed yet.'
                  : '🔍 Search returned no logged records.'}
              </div>
            ) : (
              <div className="history-list">
                {filteredHistory.map(rec => (
                  <div key={rec.id} className={`history-item ${rec.is_illegal ? 'threat-item' : (rec.is_sensitive ? 'sensitive-item' : 'clean-item')}`}>
                    <div className="history-icon">{rec.is_illegal ? '🚨' : (rec.is_sensitive ? '🔐' : '✅')}</div>
                    <div className="history-info">
                      <div className="history-name">{rec.original_name || rec.filename}</div>
                      <div className="history-meta">
                        <span>🕐 {fmtTime(rec.timestamp)}</span>
                        <span>📄 {rec.document_type || 'unknown'}</span>
                        <span>🔍 {rec.method || 'ocr'}</span>
                        {rec.regions_count > 0 && <span>📍 {rec.regions_count} Redacted Zones</span>}
                        {rec.blurred && <span style={{ color: 'var(--safe)' }}>✓ Redacted</span>}
                      </div>
                      {rec.keywords?.length > 0 && (
                        <div style={{ marginTop: 6 }}>
                          {rec.keywords.slice(0, 4).map((k, i) => <span key={i} className="kw-tag" style={{ fontSize: '.62rem', padding: '2px 8px' }}>{k}</span>)}
                        </div>
                      )}
                    </div>
                    <div className="history-actions">
                      {rec.blurred && (
                        <button onClick={() => downloadFile(`${API}/uploads/${rec.blurred_file}`, `secure_${rec.original_name}`)} className="btn-history-dl" style={{ border: 'none', cursor: 'pointer' }}>
                          ⬇ DOWNLOAD
                        </button>
                      )}
                      <button className="btn-danger" style={{ padding: '6px 10px' }} onClick={() => deleteHistoryItem(rec.id)}>🗑</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ── ANALYTICS TAB ─────────────────────────────────────────────── */}
        {activeTab === 'stats' && (
          <section className="panel stats-panel">
            <div className="panel-label">SCAN STATISTICS & THREAT METRICS</div>

            <div className="stats-cards-grid">
              <div className="stats-card">
                <div className="metric-label">TOTAL SCANS</div>
                <div className="stats-card-val accent">{stats?.total_scans || 0}</div>
              </div>
              <div className="stats-card">
                <div className="metric-label">SENSITIVE FLAGGED</div>
                <div className="stats-card-val danger">{stats?.sensitive_count || 0}</div>
              </div>
              <div className="stats-card">
                <div className="metric-label">WEAPON THREATS</div>
                <div className="stats-card-val danger" style={{ textShadow: '0 0 10px var(--danger)' }}>{stats?.illegal_count || 0}</div>
              </div>
              <div className="stats-card">
                <div className="metric-label">CLEAN VERIFIED</div>
                <div className="stats-card-val safe">{stats?.clean_count || 0}</div>
              </div>
            </div>

            <div className="analytics-main">
              <div className="stats-card">
                <div className="section-label" style={{ marginBottom: 16 }}>SCANS SUMMARY</div>
                <Donut 
                  sensitive={stats?.sensitive_count || 0} 
                  clean={stats?.clean_count || 0} 
                  illegal={stats?.illegal_count || 0}
                />
              </div>

              <div className="stats-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div className="section-label" style={{ marginBottom: 16, textAlign: 'left' }}>DOCUMENT TYPES SCAN DENSITY</div>
                <div className="dist-list">
                  {stats && Object.entries(stats.document_types || {}).map(([type, val], i) => {
                    const ratio = ((val / stats.total_scans) * 100).toFixed(0);
                    return (
                      <div key={i} className="dist-item">
                        <div className="dist-label-row">
                          <span>{type.toUpperCase()}</span>
                          <span>{val} ({ratio}%)</span>
                        </div>
                        <div className="dist-bar">
                          <div className="dist-fill" style={{ width: `${ratio}%` }} />
                        </div>
                      </div>
                    );
                  })}
                  {!stats || Object.keys(stats.document_types || {}).length === 0 ? (
                    <div className="history-empty" style={{ padding: 0 }}>No scan ratios aggregated yet.</div>
                  ) : null}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── AI CHAT TAB ───────────────────────────────────────────────── */}
        {activeTab === 'chat' && (
          <section className="panel chat-panel">
            <div className="panel-label">AI SECURITY CONVERSATION NODE</div>

            <div className="chat-wrap">
              <div className="chat-msgs">
                {chatMsgs.map((m) => (
                  <div key={m.id} className={`chat-bubble ${m.role}`}>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{m.text}</p>
                    <span className="chat-time">{m.time}</span>
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-typing">
                    <span>AI is formulating response</span>
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="chat-suggestions">
                {QUICK_QUESTIONS.map((q, i) => (
                  <button key={i} className="chat-sug-btn" onClick={() => sendChat(q)}>
                    {q}
                  </button>
                ))}
              </div>

              <div className="chat-input-bar">
                <input 
                  className="chat-input" 
                  placeholder="Ask about Aadhaar privacy, weapons screening, or data tips..."
                  value={chatInput} 
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') sendChat(); }}
                  disabled={chatLoading}
                />
                <button className="chat-send-btn" onClick={() => sendChat()} disabled={chatLoading || !chatInput.trim()}>
                  TRANSMIT
                </button>
              </div>
            </div>
          </section>
        )}

        {/* ── SETTINGS TAB ───────────────────────────────────────────────── */}
        {activeTab === 'settings' && settings && (
          <section className="panel settings-panel">
            <div className="panel-label">SHIELD CONFIGURATION PARAMETERS</div>

            <div className="settings-grid">
              <div className="settings-box">
                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">AUTOMATIC REDACTION</div>
                    <div className="settings-desc">Instantly apply OpenCV Gaussian blur to identified targets.</div>
                  </div>
                  <label className="switch">
                    <input type="checkbox" checked={settings.auto_blur} onChange={e => setSetting('auto_blur', e.target.checked)} />
                    <span className="slider" />
                  </label>
                </div>

                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">GAUSSIAN BLUR RADIUS</div>
                    <div className="settings-desc">Adjust the density level of redaction blurring.</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <input type="range" min="15" max="150" className="range-slider" value={settings.blur_strength} onChange={e => setSetting('blur_strength', parseInt(e.target.value))} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '.78rem', minWidth: 24 }}>{settings.blur_strength}px</span>
                  </div>
                </div>

                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">SAFETY HAZARD ALERTS</div>
                    <div className="settings-desc">Activate weapon/illegal upload block warning panels.</div>
                  </div>
                  <label className="switch">
                    <input type="checkbox" checked={settings.ocr_fallback} onChange={e => setSetting('ocr_fallback', e.target.checked)} />
                    <span className="slider" />
                  </label>
                </div>
              </div>

              <div className="settings-box">
                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">ANTHROPIC API KEY</div>
                    <div className="settings-desc">Activate Claude Vision for visual weapon redaction.</div>
                  </div>
                  <input type="password" className="settings-input" style={{ width: '180px' }} value={settings.api_key || ''} onChange={e => setSetting('api_key', e.target.value)} placeholder="sk-ant-..." />
                </div>

                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">LOG HISTORY MAX LIMIT</div>
                    <div className="settings-desc">Maximum scan logs kept in local index.</div>
                  </div>
                  <input type="number" className="settings-input" value={settings.max_history} onChange={e => setSetting('max_history', parseInt(e.target.value))} />
                </div>

                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">PREVENTATIVE WATERMARK</div>
                    <div className="settings-desc">Embed a cyber-security watermark in the redacted output.</div>
                  </div>
                  <label className="switch">
                    <input type="checkbox" checked={settings.watermark} onChange={e => setSetting('watermark', e.target.checked)} />
                    <span className="slider" />
                  </label>
                </div>

                <div className="settings-row">
                  <div className="settings-label-wrap">
                    <div className="settings-title">OCR ENGINE LANGUAGE</div>
                    <div className="settings-desc">Default language pack for local Tesseract.</div>
                  </div>
                  <select className="settings-select" value={settings.language} onChange={e => setSetting('language', e.target.value)}>
                    <option value="eng">English (eng)</option>
                    <option value="hin">Hindi (hin)</option>
                    <option value="ind">Indonesian (ind)</option>
                  </select>
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: 30 }}>
              <button className="btn-primary" onClick={saveSettings}>
                SAVE SHIELD CONFIG
              </button>
              {settingsSaved && <div className="toast-saved">✓ SHELL SETTINGS SYNCHRONIZED SECURELY</div>}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
