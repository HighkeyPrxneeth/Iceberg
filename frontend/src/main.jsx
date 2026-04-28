import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './Dashboard'
import CloneYoutube from './CloneYoutube'
import CloneTwitch from './CloneTwitch'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/youtube" element={<CloneYoutube />} />
        <Route path="/twitch" element={<CloneTwitch />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
