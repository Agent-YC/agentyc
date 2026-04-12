import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import AgentsPage from './pages/AgentsPage';
import AgentDetailPage from './pages/AgentDetailPage';
import ChallengesPage from './pages/ChallengesPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="nav-bar">
          <div className="brand">
            <span>⚡</span>
            <span>Agent YC</span>
          </div>
          <div className="nav-links">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              Agents
            </NavLink>
            <NavLink to="/challenges" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Challenges
            </NavLink>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<AgentsPage />} />
          <Route path="/agents/:id" element={<AgentDetailPage />} />
          <Route path="/challenges" element={<ChallengesPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
