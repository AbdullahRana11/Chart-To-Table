import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Upload from './pages/Upload'
import Results from './pages/Results'
import History from './pages/History'
import FloatingBackground from './components/FloatingBackground'
import './index.css'

function App() {
  return (
    <Router>
      <FloatingBackground />
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/history" element={<History />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
