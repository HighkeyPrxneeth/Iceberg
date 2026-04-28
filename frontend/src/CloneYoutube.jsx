import React, { useState, useEffect } from 'react';
import { Menu, Search, Bell, UserCircle, Home, Compass, PlaySquare, Clock, ThumbsUp } from 'lucide-react';

export default function CloneYoutube() {
  const [feed, setFeed] = useState([]);

  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchFeed = async () => {
    const res = await fetch("http://localhost:8000/api/feed/youtube");
    const data = await res.json();
    setFeed(data);
  };

  return (
    <div style={{ backgroundColor: '#0f0f0f', color: '#fff', minHeight: '100vh', fontFamily: 'Roboto, Arial, sans-serif' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px', height: '56px', position: 'sticky', top: 0, backgroundColor: '#0f0f0f', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Menu size={24} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '20px', fontWeight: 'bold' }}>
            <div style={{ width: '30px', height: '20px', backgroundColor: '#FF0000', borderRadius: '4px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <div style={{ width: 0, height: 0, borderTop: '5px solid transparent', borderBottom: '5px solid transparent', borderLeft: '8px solid white' }}></div>
            </div>
            ViewTube
          </div>
        </div>
        
        <div style={{ display: 'flex', flex: 1, maxWidth: '600px', margin: '0 40px' }}>
          <div style={{ display: 'flex', flex: 1, backgroundColor: '#121212', border: '1px solid #303030', borderRadius: '40px 0 0 40px', padding: '0 20px', alignItems: 'center' }}>
            <input type="text" placeholder="Search" style={{ background: 'transparent', border: 'none', color: '#fff', width: '100%', outline: 'none', fontSize: '16px' }} />
          </div>
          <button style={{ backgroundColor: '#222', border: '1px solid #303030', borderLeft: 'none', borderRadius: '0 40px 40px 0', padding: '0 20px', cursor: 'pointer' }}>
            <Search size={20} color="#fff" />
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Bell size={24} />
          <UserCircle size={32} />
        </div>
      </header>
      
      <div style={{ display: 'flex' }}>
        {/* Sidebar */}
        <aside style={{ width: '240px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[
            { icon: Home, text: 'Home', active: true },
            { icon: Compass, text: 'Explore' },
            { icon: PlaySquare, text: 'Subscriptions' },
            { icon: Clock, text: 'History' },
            { icon: ThumbsUp, text: 'Liked videos' }
          ].map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '20px', padding: '10px 12px', borderRadius: '10px', backgroundColor: item.active ? '#272727' : 'transparent', cursor: 'pointer' }}>
              <item.icon size={24} />
              <span style={{ fontSize: '14px', fontWeight: item.active ? 'bold' : 'normal' }}>{item.text}</span>
            </div>
          ))}
        </aside>

        {/* Main Content */}
        <main style={{ flex: 1, padding: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {feed.map(post => (
              <div key={post.post_id} style={{ cursor: 'pointer' }}>
                <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', backgroundColor: '#222', borderRadius: '12px', overflow: 'hidden' }}>
                  <img src="https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&q=80" alt="thumbnail" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }} />
                  <div style={{ position: 'absolute', bottom: '8px', right: '8px', backgroundColor: 'rgba(204, 0, 0, 0.9)', color: 'white', padding: '3px 4px', borderRadius: '4px', fontSize: '12px', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div style={{ width: '6px', height: '6px', backgroundColor: 'white', borderRadius: '50%' }}></div> LIVE
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#444', flexShrink: 0 }}></div>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f1f1f1', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{post.title}</div>
                    <div style={{ fontSize: '14px', color: '#aaa', marginTop: '4px' }}>PirateStreamer99</div>
                    <div style={{ fontSize: '14px', color: '#aaa' }}>{post.views.toLocaleString()} watching</div>
                  </div>
                </div>
              </div>
            ))}
            {feed.length === 0 && <div style={{ color: '#aaa' }}>No streams recommended at this time.</div>}
          </div>
        </main>
      </div>
    </div>
  );
}
