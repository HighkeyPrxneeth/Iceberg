import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Upload, ShieldAlert, Activity, PlaySquare, Crosshair, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const [assets, setAssets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [distributedTo, setDistributedTo] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

  const fetchAssets = async () => {
    const res = await fetch("http://localhost:8000/api/registered");
    const data = await res.json();
    setAssets(data.reverse());
  };

  const fetchAlerts = async () => {
    const res = await fetch("http://localhost:8000/api/alerts");
    const data = await res.json();
    setAlerts(data.reverse());
  };

  useEffect(() => {
    fetchAssets();
    fetchAlerts();

    const evtSource = new EventSource("http://localhost:8000/api/stream");
    
    evtSource.addEventListener("upload_start", (e) => {
      const newAsset = JSON.parse(e.data);
      setAssets(prev => [newAsset, ...prev]);
    });
    
    evtSource.addEventListener("progress", (e) => {
      const data = JSON.parse(e.data);
      setAssets(prev => prev.map(a => a.id === data.id ? { ...a, progress: data.progress } : a));
    });
    
    evtSource.addEventListener("upload", (e) => {
      const completedAsset = JSON.parse(e.data);
      setAssets(prev => prev.map(a => a.id === completedAsset.id ? completedAsset : a));
    });
    
    evtSource.addEventListener("alert", (e) => {
      const newAlert = JSON.parse(e.data);
      setAlerts(prev => [newAlert, ...prev]);
    });

    return () => evtSource.close();
  }, []);

  const handleUpload = async (e) => {
    if (!e.target.files[0]) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    formData.append("label", "official_broadcast");
    if (distributedTo) {
      formData.append("distributed_to", distributedTo);
    }

    try {
      await fetch("http://localhost:8000/api/register", {
        method: "POST",
        body: formData
      });
    } catch (err) {
      console.error(err);
    }
    setUploading(false);
  };

  const handleVerify = async (e) => {
    if (!e.target.files[0]) return;
    setVerifying(true);
    setVerifyResult(null);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    try {
      const res = await fetch("http://localhost:8000/api/verify", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setVerifyResult(data);
    } catch (err) {
      console.error(err);
    }
    setVerifying(false);
    e.target.value = null;
  };

  const simulatePiracy = async (assetId, platform) => {
    try {
      await fetch("http://localhost:8000/api/simulate-piracy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset_id: assetId, platform })
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Left Panel: Controls */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <Activity size={20} style={{ marginRight: '8px' }} />
          Control Nexus
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label className="label-header">Distributor / Recipient Name</label>
            <input
              type="text"
              className="corporate-input"
              placeholder="e.g. Broadcast Partner Alpha"
              value={distributedTo}
              onChange={e => setDistributedTo(e.target.value)}
            />
          </div>

          <label className="corporate-button primary">
            {uploading ? (
              "Watermarking..."
            ) : (
              <>
                <Upload size={16} />
                Register Broadcast
              </>
            )}
            <input type="file" style={{ display: 'none' }} onChange={handleUpload} accept="video/*,image/*" />
          </label>

          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
            <label className="corporate-button">
              <ShieldAlert size={16} />
              <span style={{marginLeft: '8px'}}>{verifying ? "Verifying..." : "Verify Local Media"}</span>
              <input type="file" style={{ display: 'none' }} onChange={handleVerify} accept="video/*,image/*" />
            </label>
          </div>

          {verifyResult && (
            <div className="verify-result-card">
              <h4>Verification Result</h4>
              <div className="data-row">
                <span className="data-label">C2PA Status</span>
                <span style={{ color: verifyResult.c2pa?.status === 'valid' ? 'var(--accent-success)' : 'var(--accent-danger)', fontWeight: 600 }}>
                  {verifyResult.c2pa?.status === 'valid' ? 'Valid' : (verifyResult.c2pa?.status || 'Invalid/Missing')}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Distributor</span>
                <span>{verifyResult.c2pa?.distributed_to || 'N/A'}</span>
              </div>
              <div className="data-row">
                <span className="data-label">DCT Payload</span>
                <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{verifyResult.dct_payload || verifyResult.cnn_payload || 'Not Found'}</span>
              </div>
              <button className="corporate-button" style={{ marginTop: '12px', padding: '6px' }} onClick={() => setVerifyResult(null)}>
                Dismiss
              </button>
            </div>
          )}

          <div style={{ marginTop: '24px' }}>
            <h3 className="section-label">SIMULATOR ENDPOINTS</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Link to="/youtube" target="_blank" className="corporate-button">Open YouTube Clone</Link>
              <Link to="/twitch" target="_blank" className="corporate-button">Open Twitch Clone</Link>
            </div>
          </div>
        </div>
      </div>

      {/* Center Panel: Assets */}
      <div className="dashboard-panel" style={{ borderLeft: 'none', borderRight: 'none', flex: 1, overflowY: 'auto' }}>
        <div className="panel-header">
          <ShieldAlert size={20} style={{ marginRight: '8px' }} />
          Protected Assets
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {assets.map(asset => (
            <div key={asset.id} className="asset-card">
              <div>
                <div className="asset-title">{asset.original_name}</div>
                <div className="asset-meta">ID: {asset.id}</div>
              </div>
              
              {asset.status === 'processing' ? (
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Embedding 2D Watermark</span>
                    <span>{asset.progress || 0}%</span>
                  </div>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${asset.progress || 0}%` }}></div>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {asset.c2pa_signature === 'signing...' && <span className="badge" style={{ background: '#fff0d4', color: '#834c00', borderColor: '#ffd699' }}>C2PA: SIGNING...</span>}
                    {asset.c2pa_signature === 'valid' && <span className="badge valid-c2pa" title={asset.c2pa_manifest}><CheckCircle size={10} style={{marginRight: '4px'}}/> C2PA: VALID</span>}
                    {asset.c2pa_signature === 'failed' && <span className="badge danger">C2PA: FAILED</span>}
                    <span className="badge valid">Payload: {asset.payload_id}</span>
                    {asset.distributed_to && <span className="badge">To: {asset.distributed_to}</span>}
                  </div>
                  <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button className="corporate-button danger" onClick={() => simulatePiracy(asset.id, 'youtube')} style={{ flex: 1 }}>
                      <PlaySquare size={14} /> Leak to YT
                    </button>
                    <button className="corporate-button danger" onClick={() => simulatePiracy(asset.id, 'twitch')} style={{ flex: 1 }}>
                      <PlaySquare size={14} /> Leak to Twitch
                    </button>
                  </div>
                  <a href={`http://localhost:8000${asset.url}`} download className="corporate-button" style={{ marginTop: '4px' }}>
                    Download Secured Asset
                  </a>
                </>
              )}
            </div>
          ))}
          {assets.length === 0 && <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>No assets registered yet.</div>}
        </div>
      </div>

      {/* Right Panel: Alerts */}
      <div className="dashboard-panel">
        <div className="panel-header" style={{ color: 'var(--accent-danger)' }}>
          <Crosshair size={20} style={{ marginRight: '8px' }} />
          Verification Log
        </div>
        
        <div style={{ overflowY: 'auto' }}>
          {alerts.map(alert => (
            <div key={alert.id} className="alert-item">
              <div className="alert-title">{alert.title}</div>
              <div className="alert-msg">{alert.message}</div>
              {alert.confidence && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--accent-danger)', fontWeight: 500 }}>
                  Confidence: {Number(alert.confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>
          ))}
          {alerts.length === 0 && <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>System nominal. No piracy detected.</div>}
        </div>
      </div>
    </div>
  );
}
