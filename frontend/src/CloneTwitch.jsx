import React, { useState, useEffect } from 'react';
import { Search, Bell, MessageSquare, Inbox, User, Heart, Video } from 'lucide-react';

export default function CloneTwitch() {
  const [feed, setFeed] = useState([]);

  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchFeed = async () => {
    const res = await fetch("http://localhost:8000/api/feed/twitch");
    const data = await res.json();
    setFeed(data);
  };

  const topPost = feed.length > 0 ? feed[0] : null;
  const otherPosts = feed.slice(1);

  return (
    <div style={{ backgroundColor: '#0e0e10', color: '#efeff1', minHeight: '100vh', fontFamily: 'Inter, Roobert, sans-serif' }}>
      {/* Navbar */}
      <header style={{ height: '50px', backgroundColor: '#18181b', borderBottom: '1px solid #000', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 10px', position: 'sticky', top: 0, zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ color: '#bf94ff', fontWeight: 'bold', fontSize: '24px', letterSpacing: '-1px' }}>Glitch</div>
          <div style={{ fontWeight: '600', fontSize: '18px', color: '#bf94ff', borderBottom: '2px solid #bf94ff', paddingBottom: '14px', paddingTop: '14px' }}>Following</div>
          <div style={{ fontWeight: '600', fontSize: '18px', paddingBottom: '14px', paddingTop: '14px' }}>Browse</div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', backgroundColor: '#3a3a3d', borderRadius: '6px', padding: '5px 10px', width: '400px' }}>
          <input type="text" placeholder="Search" style={{ background: 'transparent', border: 'none', color: '#fff', width: '100%', outline: 'none' }} />
          <Search size={20} color="#adadb8" />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <Bell size={20} />
          <Inbox size={20} />
          <MessageSquare size={20} />
          <div style={{ width: '30px', height: '30px', backgroundColor: '#00f0ff', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <User size={20} color="#000" />
          </div>
        </div>
      </header>
      
      <div style={{ display: 'flex', height: 'calc(100vh - 50px)' }}>
        {/* Left Sidebar */}
        <aside style={{ width: '240px', backgroundColor: '#1f1f23', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '10px', fontWeight: '600', fontSize: '13px', textTransform: 'uppercase' }}>For You</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '10px' }}>
            {[1,2,3].map(i => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '30px', height: '30px', borderRadius: '50%', backgroundColor: '#444' }}></div>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '14px' }}>Streamer_{i}</div>
                    <div style={{ fontSize: '12px', color: '#adadb8' }}>Just Chatting</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ width: '8px', height: '8px', backgroundColor: '#eb0400', borderRadius: '50%' }}></div>
                  <span style={{ fontSize: '13px' }}>1.2K</span>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '30px' }}>
          {topPost ? (
            <div style={{ display: 'flex', gap: '20px', marginBottom: '40px' }}>
              <div style={{ flex: 1, aspectRatio: '16/9', backgroundColor: '#000', position: 'relative' }}>
                <img src="https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1200&q=80" alt="hero" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.7 }} />
                <div style={{ position: 'absolute', top: '10px', left: '10px', backgroundColor: '#eb0400', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold', fontSize: '13px' }}>LIVE</div>
              </div>
              <div style={{ width: '300px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', gap: '15px' }}>
                  <div style={{ width: '50px', height: '50px', borderRadius: '50%', backgroundColor: '#fff', border: '2px solid #bf94ff' }}></div>
                  <div>
                    <div style={{ color: '#bf94ff', fontWeight: 'bold', fontSize: '18px' }}>PirateStreamer</div>
                    <div style={{ color: '#eb0400', fontWeight: 'bold' }}>{topPost.views.toLocaleString()} viewers</div>
                  </div>
                </div>
                <div style={{ marginTop: '15px', fontSize: '18px' }}>{topPost.title}</div>
                <div style={{ marginTop: '10px', color: '#adadb8', fontSize: '14px' }}>Sports • Action</div>
              </div>
            </div>
          ) : (
             <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#adadb8' }}>No featured streams.</div>
          )}

          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '20px' }}>Live channels we think you'll like</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {otherPosts.map(post => (
              <div key={post.post_id} style={{ cursor: 'pointer' }}>
                <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', backgroundColor: '#222' }}>
                  <img src="https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=600&q=80" alt="thumb" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.5 }} />
                  <div style={{ position: 'absolute', top: '8px', left: '8px', backgroundColor: '#eb0400', color: 'white', padding: '2px 4px', borderRadius: '4px', fontWeight: 'bold', fontSize: '12px' }}>LIVE</div>
                  <div style={{ position: 'absolute', bottom: '8px', left: '8px', backgroundColor: 'rgba(0,0,0,0.6)', color: 'white', padding: '2px 4px', borderRadius: '4px', fontSize: '13px' }}>{post.views.toLocaleString()} viewers</div>
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#444' }}></div>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', width: '200px' }}>{post.title}</div>
                    <div style={{ color: '#adadb8', fontSize: '13px' }}>User_{post.post_id.substring(0,4)}</div>
                    <div style={{ color: '#adadb8', fontSize: '13px' }}>Sports</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
