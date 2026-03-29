import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import { MainPage } from './pages/MainPage'; // Existing RAG platform

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-50 font-sans antialiased overflow-x-hidden">
        <Routes>
          {/* Presentation Landing Page */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Functional Hackathon Platform Demo */}
          <Route path="/demo" element={<MainPage />} />
          
          {/* Fallback */}
          <Route path="*" element={<LandingPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
