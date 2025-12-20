import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Database, Zap, Lock } from 'lucide-react';
import styles from './Home.module.css';

const Home = () => {
  return (
    <div className={styles.home}>
      <section className={styles.hero}>
        <div className="container">
          <motion.div 
            className={styles.heroContent}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className={styles.title}>
              Unlock Data from <span className="text-gradient">Scientific Charts</span>
            </h1>
            <p className={styles.subtitle}>
              Automated extraction of numerical data from static images using advanced computer vision and machine learning.
            </p>
            <div className={styles.ctaGroup}>
              <Link to="/upload" className="btn-primary">
                Start Extraction <ArrowRight size={18} style={{ marginLeft: '0.5rem' }} />
              </Link>
              <button className={styles.btnSecondary}>View Demo</button>
            </div>
          </motion.div>
        </div>
      </section>

      <section className={styles.features}>
        <div className="container">
          <div className={styles.featureGrid}>
            <FeatureCard 
              icon={<Zap />}
              title="Instant Extraction"
              description="Get structured data from images in seconds using our optimized pipeline."
            />
            <FeatureCard 
              icon={<Database />}
              title="Structured Output"
              description="Export your data directly to CSV or JSON formats for immediate analysis."
            />
            <FeatureCard 
              icon={<Lock />}
              title="Secure & Private"
              description="Your data is processed locally and never stored permanently."
            />
          </div>
        </div>
      </section>
    </div>
  );
};

const FeatureCard = ({ icon, title, description }) => (
  <motion.div 
    className={`${styles.featureCard} glass-panel`}
    whileHover={{ y: -5 }}
  >
    <div className={styles.iconWrapper}>{icon}</div>
    <h3>{title}</h3>
    <p>{description}</p>
  </motion.div>
);

export default Home;
