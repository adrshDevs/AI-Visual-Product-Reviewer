import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Upload,
  Search,
  ShoppingBag,
  Info,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Package,
  Layers,
  X,
  Sparkles,
  Camera
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect } from 'react';

const LoadingSkeleton = () => (
  <div className="container" style={{ maxWidth: '1000px' }}>
    <div className="card loading-skeleton" style={{ height: '300px', marginBottom: '32px' }} />
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
      <div className="card loading-skeleton" style={{ height: '200px' }} />
      <div className="card loading-skeleton" style={{ height: '200px' }} />
    </div>
  </div>
);

const LoadingDots = ({ color = "white", size = 4 }) => (
  <div style={{ display: 'flex', gap: '4px', alignItems: 'center', justifyContent: 'center' }}>
    {[0, 1, 2].map((i) => (
      <motion.div
        key={i}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background: color,
        }}
        animate={{
          opacity: [0.2, 1, 0.2],
          scale: [0.8, 1.2, 0.8],
        }}
        transition={{
          duration: 0.8,
          repeat: Infinity,
          delay: i * 0.2,
          ease: "easeInOut"
        }}
      />
    ))}
  </div>
);

const App = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [query, setQuery] = useState('');
  const [showSearchBar, setShowSearchBar] = useState(true);
  const [typedText, setTypedText] = useState('');

  useEffect(() => {
    if (result) {
      document.body.classList.add('no-scroll');
    } else {
      document.body.classList.remove('no-scroll');
    }
  }, [result]);

  useEffect(() => {
    const text = 'Amazon Nova Pro';
    let index = 0;
    let deleting = false;
    let timeoutId;

    const tick = () => {
      setTypedText(text.slice(0, index));

      const atBoundary = index === 0 || index === text.length;
      const delay = atBoundary ? 400 : 70;

      if (!deleting) {
        if (index === text.length) {
          deleting = true;
          timeoutId = window.setTimeout(tick, delay);
          return;
        }
        index += 1;
      } else {
        if (index === 0) {
          deleting = false;
          timeoutId = window.setTimeout(tick, delay);
          return;
        }
        index -= 1;
      }

      timeoutId = window.setTimeout(tick, delay);
    };

    tick();
    return () => window.clearTimeout(timeoutId);
  }, []);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = (e) => {
    e.stopPropagation();
    setImage(null);
    setImagePreview(null);
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleNew = () => {
    setResult(null);
    setPrompt('');
    setQuery('');
    setImage(null);
    setImagePreview(null);
  };

  const handleAnalyze = async () => {
    const activePrompt = query || prompt;
    if (!image && !activePrompt) return;
    setLoading(true);

    const formData = new FormData();
    if (image) formData.append('image', image);
    if (activePrompt) formData.append('prompt', activePrompt);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);

      // Dynamic Context Sync: If AI identifies a new product search
      if (data.is_new_product) {
        setImage(null); // Clear the uploaded file state
        if (data.product_image_url) {
          setImagePreview(data.product_image_url);
        }
      } else if (!image && data.product_image_url) {
        // Just a refinement, keep existing image if any, otherwise use placeholder
        setImagePreview(data.product_image_url);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Analysis failed. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {!result && (
        <header>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ background: 'var(--accent-color)', width: '36px', height: '36px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifySelf: 'center', justifyContent: 'center' }}>
              <ShoppingBag size={20} color="white" />
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.04em' }}>AI Product Reviewer</h2>
          </div>
          <div style={{ display: 'flex', gap: '40px', fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
            <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = 'var(--text-primary)'} onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}>Discover</span>
            <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = 'var(--text-primary)'} onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}>Trends</span>
            <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = 'var(--text-primary)'} onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}>Support</span>
          </div>
        </header>
      )}

      <main className="container" style={{ padding: result ? '0' : '60px 40px', maxWidth: result ? '100%' : '1400px' }}>
        <AnimatePresence mode="wait">
          {!result ? (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
              transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            >
              {/* Cinematic Hero */}
              <section className="animate-fade-in" style={{ textAlign: 'center', marginBottom: '80px', paddingTop: '40px' }}>
                <h1 style={{
                  fontSize: '5rem',
                  marginBottom: '24px',
                  fontWeight: 800,
                  lineHeight: 1.2,
                  letterSpacing: '-0.05em',
                  backgroundImage: 'linear-gradient(135deg, #FFFFFF 0%, #A1A1A6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  paddingBottom: '0.1em'
                }}>
                  Intelligence<br />for what you buy.
                </h1>
                <p style={{ fontSize: '1.5rem', color: 'var(--text-secondary)', marginBottom: '60px', maxWidth: '750px', margin: '0 auto 60px auto', lineHeight: 1.4 }}>
                  Pro-grade product analysis powered by <span style={{color: 'var(--accent-color)'}}>{typedText}<motion.span animate={{opacity: [1,0]}} transition={{repeat: Infinity, duration: 0.5}}>|</motion.span></span> <br />Upload an image or describe your query to begin.
                </p>

                <div className="card" style={{ padding: '0', maxWidth: '1000px', margin: '0 auto', overflow: 'hidden', background: 'linear-gradient(145deg, rgba(32, 32, 34, 0.6) 0%, rgba(18, 18, 18, 0.6) 100%)', borderRadius: '28px' }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                    <div
                      style={{
                        flex: '1.2',
                        minWidth: '350px',
                        height: '320px',
                        borderRight: '1px solid var(--border-subtle)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        position: 'relative',
                        overflow: 'hidden',
                        background: imagePreview ? '#000' : 'transparent',
                        transition: 'background 0.4s'
                      }}
                      onClick={() => !imagePreview && document.getElementById('file-input').click()}
                      onMouseEnter={e => !imagePreview && (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                      onMouseLeave={e => !imagePreview && (e.currentTarget.style.background = 'transparent')}
                    >
                      {imagePreview ? (
                        <>
                          <img src={imagePreview} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'contain', padding: '20px' }} />
                          <button
                            onClick={(e) => {
                              handleRemoveImage(e);
                            }}
                            style={{
                              position: 'absolute',
                              top: '16px',
                              right: '16px',
                              background: 'rgba(255, 255, 255, 0.1)',
                              backdropFilter: 'blur(10px)',
                              WebkitBackdropFilter: 'blur(10px)',
                              color: 'white',
                              width: '32px',
                              height: '32px',
                              borderRadius: '50%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              padding: '0',
                              border: '1px solid rgba(255,255,255,0.1)',
                              zIndex: 10
                            }}
                            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 59, 48, 0.8)'}
                            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
                          >
                            <X size={18} />
                          </button>
                        </>
                      ) : (
                        <>
                          <Upload color="var(--accent-color)" size={48} style={{ marginBottom: '16px' }} />
                          <span style={{ color: 'white', fontSize: '1.1rem', fontWeight: 500 }}>Drop product image</span>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>to analyze details instantly</span>
                        </>
                      )}
                      <input id="file-input" type="file" hidden onChange={handleImageChange} accept="image/*" />
                    </div>

                    <div style={{ flex: 1, minWidth: '350px', display: 'flex', flexDirection: 'column', padding: '32px' }}>
                      <div style={{ textAlign: 'left', marginBottom: '12px' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-color)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Contextual Search</span>
                      </div>
                      <textarea
                        placeholder="Ask a specific question or describe the product..."
                        style={{
                          flex: 1,
                          background: 'transparent',
                          border: 'none',
                          color: 'white',
                          padding: '0',
                          resize: 'none',
                          fontFamily: 'inherit',
                          outline: 'none',
                          fontSize: '1.2rem',
                          lineHeight: 1.5
                        }}
                        value={prompt}
                        onChange={e => setPrompt(e.target.value)}
                      />
                      <button
                        className="primary"
                        style={{ width: '100%', marginTop: '32px', height: '64px', fontSize: '1.2rem', fontWeight: 700, borderRadius: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}
                        onClick={handleAnalyze}
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <span style={{ opacity: 0.8 }}>Synthesizing</span>
                            <LoadingDots color="white" size={6} />
                          </>
                        ) : 'Analyze Product'}
                      </button>
                    </div>
                  </div>
                </div>
              </section>
            </motion.div>
          ) : (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
              className="results-grid"
            >
              <div className="results-sidebar">
                <div className="sidebar-scroll-area">
                  {/* Sidebar Category Badge */}
                  <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '8px 16px',
                    borderRadius: '12px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: 'var(--accent-color)',
                    display: 'inline-block',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    marginBottom: '24px',
                    border: '1px solid rgba(41, 151, 255, 0.2)'
                  }}>
                    {result.category}
                  </div>

                  <div className="sidebar-image-card" style={{ marginBottom: '24px' }}>
                    {imagePreview ? (
                      <div style={{ position: 'relative' }}>
                        <img src={imagePreview} alt="Product Source" />
                        <button
                          onClick={handleNew}
                          style={{
                            position: 'absolute',
                            top: '12px',
                            right: '12px',
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            border: '1px solid rgba(255,255,255,0.15)',
                            background: 'rgba(0,0,0,0.4)',
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            padding: 0,
                            zIndex: 10,
                          }}
                          onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,0,0,0.6)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'rgba(0,0,0,0.4)'}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <Package size={48} color="rgba(255,255,255,0.1)" />
                    )}
                  </div>

                  {/* Product Identity in Sidebar */}
                  <div style={{ marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'white', letterSpacing: '-0.02em', lineHeight: 1.2, marginBottom: '16px' }}>
                      {result.product_name}
                    </h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34C759' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        color: 'var(--text-secondary)',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginRight: '4px'
                      }}>Rating</span>
                      <CheckCircle size={20} color="#34C759" />
                      <span style={{ fontSize: '1.4rem', fontWeight: 800 }}>{result.rating}/5</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="results-content">
                <div className="content-scroll-area">
                  {/* AI Insight Highlight */}
                  <div className="card" style={{
                    background: 'linear-gradient(135deg, rgba(41, 151, 255, 0.15) 0%, rgba(28, 28, 30, 0.4) 100%)',
                    border: '1px solid rgba(41, 151, 255, 0.3)',
                    padding: '32px',
                    marginBottom: '32px'
                  }}>
                    <div style={{ display: 'flex', gap: '20px' }}>
                      <div style={{
                        width: '48px', height: '48px', borderRadius: '14px',
                        background: 'var(--accent-color)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        boxShadow: '0 0 20px rgba(41, 151, 255, 0.4)'
                      }}>
                        <Sparkles size={24} color="white" />
                      </div>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'var(--accent-color)', marginBottom: '12px', fontWeight: 700 }}>AI Insight</h3>
                        <p style={{ fontSize: '1.4rem', lineHeight: 1.5, fontWeight: 500, color: '#FFFFFF' }}>
                          {result.specific_answer}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Features Grid restored */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
                    <div className="card">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                        <Layers size={24} color="var(--accent-color)" />
                        <h3 style={{ fontSize: '1.4rem' }}>Engineered Details</h3>
                      </div>
                      <div>
                        <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '12px' }}>Build Architecture</h4>
                        <p style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: '24px' }}>{result.build_and_features?.build_quality}</p>
                        <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '12px' }}>Materials</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                          {result.build_and_features?.materials?.map(m => (
                            <span key={m} style={{ background: 'rgba(255,255,255,0.06)', padding: '6px 14px', borderRadius: '12px', fontSize: '0.9rem', fontWeight: 500 }}>{m}</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="card" style={{ background: 'linear-gradient(135deg, rgba(41, 151, 255, 0.08) 0%, rgba(0,0,0,0) 100%)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                        <Info size={24} color="var(--accent-color)" />
                        <h3 style={{ fontSize: '1.4rem' }}>Innovation</h3>
                      </div>
                      <p style={{ fontSize: '1.1rem', lineHeight: 1.6, color: 'rgba(255,255,255,0.8)' }}>{result.build_and_features?.special_details}</p>
                    </div>
                  </div>

                  {/* Capabilities & Lists */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                    <div className="card">
                      <h3 style={{ marginBottom: '20px', fontSize: '1.2rem' }}>Capabilities</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {result.key_features?.map(f => (
                          <div key={f} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            <div style={{ width: '6px', height: '6px', borderRadius: '2px', background: 'var(--accent-color)', marginTop: '8px', shrink: 0 }} />
                            <span style={{ fontSize: '1rem', opacity: 0.9 }}>{f}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="card">
                      <h3 style={{ marginBottom: '20px', fontSize: '1.2rem', color: '#34C759' }}>Strengths</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {result.pros?.map(p => (
                          <div key={p} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            <CheckCircle size={18} color="#34C759" style={{ marginTop: '2px', shrink: 0 }} />
                            <span style={{ fontSize: '1rem', opacity: 0.9 }}>{p}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="card">
                      <h3 style={{ marginBottom: '20px', fontSize: '1.2rem', color: '#FF3B30' }}>Limitations</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {result.cons?.map(c => (
                          <div key={c} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            <AlertCircle size={18} color="#FF3B30" style={{ marginTop: '2px', shrink: 0 }} />
                            <span style={{ fontSize: '1rem', opacity: 0.9 }}>{c}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Valuation */}
                  <div className="card" style={{ padding: '40px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                      <div>
                        <h3 style={{ fontSize: '1.6rem', letterSpacing: '-0.04em' }}>Price Trends</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginTop: '4px' }}>Pricing analysis across 12 months</p>
                      </div>
                      <TrendingUp size={28} color="var(--accent-color)" />
                    </div>
                    <div style={{ height: '350px', width: '100%' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={result.price_history}>
                          <defs>
                            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="var(--accent-color)" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#86868B' }} dy={10} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#86868B' }} dx={-10} tickFormatter={(val) => `$${val}`} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1C1C1E',
                              borderRadius: '16px',
                              border: '1px solid var(--border-subtle)',
                              boxShadow: 'var(--shadow-lg)',
                              fontSize: '0.9rem',
                              color: '#FFF'
                            }}
                            itemStyle={{ color: 'var(--accent-color)' }}
                          />
                          <Area type="monotone" dataKey="price" stroke="var(--accent-color)" strokeWidth={3} fillOpacity={1} fill="url(#colorPrice)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '32px', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '32px' }}>
                    {/* Integrity Assessment Summary */}
                    {result.review_authenticity && (
                      <div className="card" style={{ flex: '1', minWidth: '400px', marginBottom: 0, height: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                          <ShieldCheck size={28} color="var(--accent-color)" />
                          <h3 style={{ fontSize: '1.4rem', letterSpacing: '-0.03em' }}>Integrity Assessment</h3>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                          <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                            <div style={{ width: '120px', height: '120px', position: 'relative', flexShrink: 0 }}>
                              <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                  <Pie
                                    data={[
                                      { value: result.review_authenticity.confidence_score },
                                      { value: 100 - result.review_authenticity.confidence_score }
                                    ]}
                                    innerRadius={45}
                                    outerRadius={60}
                                    paddingAngle={0}
                                    dataKey="value"
                                    stroke="none"
                                    startAngle={90}
                                    endAngle={450}
                                  >
                                    <Cell fill="var(--accent-color)" />
                                    <Cell fill="rgba(255,255,255,0.05)" />
                                  </Pie>
                                </PieChart>
                              </ResponsiveContainer>
                              <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                                <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{result.review_authenticity.confidence_score}%</div>
                                <div style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Genuine</div>
                              </div>
                            </div>
                            <div style={{ display: 'flex', gap: '24px' }}>
                              <div>
                                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34C759' }}>{result.review_authenticity.genuine_count}</div>
                                <div style={{ fontSize: '0.7rem', color: '#86868B', textTransform: 'uppercase', fontWeight: 600 }}>Verified</div>
                              </div>
                              <div>
                                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#FF3B30' }}>{result.review_authenticity.fake_count}</div>
                                <div style={{ fontSize: '0.7rem', color: '#86868B', textTransform: 'uppercase', fontWeight: 600 }}>Suspicious</div>
                              </div>
                            </div>
                          </div>

                          <div style={{ background: 'rgba(41, 151, 255, 0.05)', padding: '20px', borderRadius: '16px', border: '1px solid rgba(41, 151, 255, 0.1)', marginBottom: '20px' }}>
                            <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'rgba(255,255,255,0.9)' }}>
                              {result.review_authenticity.summary}
                            </p>
                          </div>

                          {result.review_authenticity.key_signals && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                                Audit Signals
                              </div>
                              {result.review_authenticity.key_signals.map((signal, idx) => (
                                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
                                  <div style={{ marginTop: '4px', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-color)', flexShrink: 0 }} />
                                  {signal}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Audited Source Reviews */}
                    {result.reviews && result.reviews.length > 0 && (
                      <div className="card" style={{ flex: '1.2', minWidth: '400px', marginBottom: 0, height: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                          <ShoppingBag size={24} color="var(--accent-color)" />
                          <h3 style={{ fontSize: '1.4rem' }}>Verified Reviews</h3>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          {result.reviews.map((rev, idx) => {
                            const audit = result.review_authenticity?.per_review?.find(
                              p => p.user?.toLowerCase() === rev.user?.toLowerCase() ||
                                rev.text?.includes(p.text?.substring(0, 10))
                            );
                            const isFake = audit?.verdict === 'fake';

                            return (
                              <div key={idx} style={{
                                padding: '14px 18px',
                                background: isFake ? 'rgba(255, 59, 48, 0.03)' : 'rgba(255, 255, 255, 0.02)',
                                borderRadius: '14px',
                                border: `1px solid ${isFake ? 'rgba(255, 59, 48, 0.12)' : 'var(--border-subtle)'}`,
                                position: 'relative',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '6px',
                                transition: 'var(--transition-smooth)'
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <div>
                                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '1px' }}>{rev.user}</div>
                                    <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                                      {rev.platform}
                                    </div>
                                  </div>
                                  <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div style={{ color: 'var(--accent-color)', fontWeight: 700, fontSize: '0.8rem' }}>{rev.rating}/5 ⭐</div>
                                    {audit && (
                                      <div style={{
                                        fontSize: '0.55rem',
                                        fontWeight: 900,
                                        padding: '1px 5px',
                                        borderRadius: '3px',
                                        background: isFake ? '#FF3B30' : '#34C759',
                                        color: 'white'
                                      }}>
                                        {audit.verdict.toUpperCase()}
                                      </div>
                                    )}
                                  </div>
                                </div>

                                <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.75)', lineHeight: 1.4, fontStyle: 'italic' }}>
                                  "{rev.text}"
                                </p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '32px', alignItems: 'stretch', flexWrap: 'wrap' }}>
                    {/* Trusted Platforms */}
                    <div className="card" style={{ flex: '1', minWidth: '400px', marginBottom: 0, display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                        <ExternalLink size={24} color="var(--accent-color)" />
                        <h3 style={{ fontSize: '1.4rem' }}>Trusted Platforms to Buy</h3>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                        {result.platforms?.map(platform => {
                          const domains = {
                            'Amazon': 'amazon.com',
                            'Best Buy': 'bestbuy.com',
                            'Walmart': 'walmart.com',
                            'Target': 'target.com',
                            'eBay': 'ebay.com',
                            'Newegg': 'newegg.com',
                            'B&H Photo': 'bhphotovideo.com'
                          };
                          const domain = domains[platform.name] || `${platform.name.toLowerCase().replace(/\s+/g, '')}.com`;
                          const logoUrl = `https://www.google.com/s2/favicons?sz=64&domain=${domain}`;

                          return (
                            <div key={platform.name} style={{
                              padding: '14px 18px',
                              borderRadius: '14px',
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid var(--border-subtle)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              transition: 'var(--transition-smooth)'
                            }}>
                              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '16px' }}>
                                <img
                                  src={logoUrl}
                                  alt={platform.name}
                                  style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'white', padding: '2px' }}
                                  onError={(e) => e.target.style.display = 'none'}
                                />
                                <div style={{ flex: 1 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>{platform.name}</h4>
                                    <span style={{ fontWeight: 800, color: '#34C759', fontSize: '0.85rem' }}>${platform.price}</span>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{
                                      height: '4px',
                                      width: '60px',
                                      background: 'rgba(255,255,255,0.05)',
                                      borderRadius: '2px',
                                      overflow: 'hidden'
                                    }}>
                                      <div style={{
                                        height: '100%',
                                        width: `${platform.trust_score * 10}%`,
                                        background: 'var(--accent-color)'
                                      }} />
                                    </div>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                      Trust: {platform.trust_score}/10
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <a href={platform.url} target="_blank" rel="noreferrer" style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: '8px',
                                background: 'rgba(255,255,255,0.05)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                marginLeft: '16px'
                              }}>
                                <ChevronRight size={16} />
                              </a>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Alternatives */}
                    <div className="card" style={{ flex: '1', minWidth: '400px', marginBottom: 0, display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                        <Layers size={24} color="var(--accent-color)" />
                        <h3 style={{ fontSize: '1.4rem' }}>Alternate Options</h3>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                        {result.better_alternatives?.map(alt => (
                          <div key={alt.name} style={{
                            padding: '14px 18px',
                            borderRadius: '14px',
                            background: 'rgba(255,255,255,0.02)',
                            border: '1px solid var(--border-subtle)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'var(--transition-smooth)'
                          }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                                <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>{alt.name}</h4>
                                <span style={{ fontWeight: 800, color: '#34C759', fontSize: '0.85rem' }}>${alt.price}</span>
                              </div>
                              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{alt.reason}</p>
                            </div>
                            <a href={alt.url} target="_blank" rel="noreferrer" style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: '8px',
                              background: 'rgba(255,255,255,0.05)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'white',
                              marginLeft: '16px'
                            }}>
                              <ChevronRight size={16} />
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* DASHBOARD SEARCH INPUT */}
                {typeof document !== 'undefined' && createPortal(
                  showSearchBar ? (
                    <motion.div
                      className="dashboard-input-container"
                      layout
                      initial={{ opacity: 0, scale: 0.95, y: 20 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95, y: 20 }}
                      transition={{ duration: 0.22, ease: 'easeOut' }}
                      style={{ overflow: 'hidden' }}
                    >
                      <button
                        onClick={() => setShowSearchBar(false)}
                        style={{
                          background: 'transparent',
                          padding: '8px',
                          marginRight: '8px',
                          color: 'var(--text-secondary)',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                        title="Dismiss Search"
                      >
                        <X size={16} />
                      </button>
                      <input
                        type="text"
                        className="dashboard-input"
                        placeholder="Ask about this product or search another..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                      />
                      <div className="dashboard-input-actions">
                        <label className="icon-btn" title="Upload Image" style={{ background: 'transparent', cursor: 'pointer' }}>
                          <Camera size={18} color="var(--text-secondary)" />
                          <input type="file" hidden accept="image/*" onChange={handleImageUpload} />
                        </label>
                        <button
                          className="primary"
                          onClick={handleAnalyze}
                          disabled={loading}
                          style={{
                            padding: '8px 16px',
                            fontSize: '0.85rem',
                            width: '52px',
                            height: '34px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: loading ? 'rgba(255,255,255,0.05)' : 'var(--accent-color)'
                          }}
                        >
                          {loading ? <LoadingDots color="var(--accent-color)" size={4} /> : <Search size={16} />}
                        </button>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.button
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      onClick={() => setShowSearchBar(true)}
                      style={{
                        position: 'fixed',
                        bottom: '40px',
                        right: '40px',
                        width: '68px',
                        height: '68px',
                        borderRadius: '50%',
                        background: 'rgba(255, 255, 255, 0.06)',
                        backdropFilter: 'blur(14px)',
                        WebkitBackdropFilter: 'blur(14px)',
                        border: '2px solid rgba(255, 255, 255, 0.25)',
                        boxShadow: '0 14px 50px rgba(0, 0, 0, 0.45)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        zIndex: 1000,
                        cursor: 'pointer'
                      }}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      title="Search Product"
                    >
                      <span style={{ fontSize: '22px' }}>🔍</span>
                    </motion.button>
                  ),
                  document.body
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {!result && (
        <footer style={{ background: '#000', padding: '100px 60px', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '1rem' }}>
          <div className="container" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '60px' }}>
            <div style={{ maxWidth: '300px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                <div style={{ background: 'var(--accent-color)', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ShoppingBag size={18} color="white" />
                </div>
                <h3 style={{ color: 'white', fontSize: '1.4rem' }}>AI Product Reviewer</h3>
              </div>
              <p style={{ lineHeight: 1.6 }}>Sophisticated AI-driven analysis for the modern consumer. Precision, integrity, and depth.</p>
            </div>
            <div style={{ display: 'flex', gap: '80px' }}>
              <div>
                <b style={{ color: 'white', display: 'block', marginBottom: '20px', fontSize: '1.1rem' }}>Intelligence</b>
                <p style={{ marginBottom: '12px' }}>Nova Pro AI</p>
                <p style={{ marginBottom: '12px' }}>Market Logic</p>
                <p style={{ marginBottom: '12px' }}>Integrity Check</p>
              </div>
              <div>
                <b style={{ color: 'white', display: 'block', marginBottom: '20px', fontSize: '1.1rem' }}>Legal</b>
                <p style={{ marginBottom: '12px' }}>Privacy Policy</p>
                <p style={{ marginBottom: '12px' }}>Terms of Service</p>
                <p style={{ marginBottom: '12px' }}>Accessibility</p>
              </div>
            </div>
          </div>
          <div className="container" style={{ paddingTop: '60px', color: '#48484A', fontSize: '0.9rem' }}>
            © 2026 AI Visual Lab. All rights reserved.
          </div>
        </footer>
      )}
    </div>
  );
};

export default App;
