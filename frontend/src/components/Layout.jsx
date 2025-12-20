import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BarChart3, Upload, FileText, Github, History } from 'lucide-react';
import styles from './Layout.module.css';

const Layout = ({ children }) => {
  const location = useLocation();

  // Dynamic background elements
  const backgroundElements = Array.from({ length: 20 }).map((_, i) => ({
    id: i,
    size: Math.random() * 30 + 20, // Larger icons
    x: Math.random() * 100,
    duration: Math.random() * 15 + 10, // Slower, smoother falling
    delay: Math.random() * 5,
    Icon: [BarChart3, FileText, Upload, Github][Math.floor(Math.random() * 4)] // Random icon
  }));

  return (
    <div className={styles.layout}>
      {/* Dynamic Background */}
      <div className={styles.background}>
        {backgroundElements.map((el) => (
          <motion.div
            key={el.id}
            className={styles.bgElement}
            style={{
              left: `${el.x}%`,
            }}
            initial={{ top: -50, opacity: 0 }}
            animate={{ 
              top: '100vh', 
              opacity: [0, 0.4, 0], // Higher max opacity for visibility
              rotate: 360
            }}
            transition={{ 
              duration: el.duration, 
              repeat: Infinity, 
              delay: el.delay,
              ease: "linear"
            }}
          >
            <el.Icon size={el.size} strokeWidth={1.5} />
          </motion.div>
        ))}
      </div>

      <header className={styles.header}>
        <div className={`container ${styles.navContainer}`}>
          <Link to="/" className={styles.logo}>
            <BarChart3 className={styles.logoIcon} />
            <span>ChartExtract</span>
          </Link>
          <nav className={styles.nav}>
            <Link to="/" className={`${styles.navLink} ${location.pathname === '/' ? styles.active : ''}`}>Home</Link>
            <Link to="/upload" className={`${styles.navLink} ${location.pathname === '/upload' ? styles.active : ''}`}>Upload</Link>
            <Link to="/history" className={`${styles.navLink} ${location.pathname === '/history' ? styles.active : ''}`}>History</Link>
            <Link to="/about" className={styles.navLink}>About</Link>
          </nav>
        </div>
      </header>

      <main className={styles.main}>
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </main>

      <footer className={styles.footer}>
        <div className="container">
          <p>&copy; 2025 Victreat / NSTP. All rights reserved.</p>
          <div className={styles.socials}>
            <a href="#" aria-label="GitHub"><Github size={20} /></a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
