import { motion } from 'framer-motion';

// Chart SVG Components
const BarChartIcon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
    <rect x="4" y="13" width="4" height="7" />
    <rect x="10" y="9" width="4" height="11" />
    <rect x="16" y="5" width="4" height="15" />
  </svg>
);

const LineChartIcon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
    <polyline points="3 17 9 11 13 15 21 7" />
    <polyline points="21 7 21 13 15 13" />
  </svg>
);

const PieChartIcon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
    <path d="M21.21 15.89A10 10 0 1 1 8 2.83" />
    <path d="M22 12A10 10 0 0 0 12 2v10z" fill={color} opacity="0.3" />
  </svg>
);

const TrendingUpIcon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
);

const FloatingBackground = () => {
  const chartIcons = [BarChartIcon, LineChartIcon, PieChartIcon, TrendingUpIcon];
  
  // Generate random floating chart elements
  const elements = Array.from({ length: 15 }, (_, i) => {
    const Icon = chartIcons[i % chartIcons.length];
    return {
      id: i,
      Icon,
      size: Math.random() * 60 + 40, // 40-100px
      x: Math.random() * 100,
      y: Math.random() * 100,
      duration: Math.random() * 15 + 20, // 20-35 seconds
      delay: Math.random() * 8,
      color: i % 2 === 0 ? 'rgba(56, 189, 248, 0.3)' : 'rgba(129, 140, 248, 0.3)',
      rotation: Math.random() * 360,
    };
  });

  // Add some gradient blobs for depth
  const blobs = Array.from({ length: 8 }, (_, i) => ({
    id: `blob-${i}`,
    size: Math.random() * 120 + 80,
    x: Math.random() * 100,
    y: Math.random() * 100,
    duration: Math.random() * 12 + 18,
    delay: Math.random() * 5,
  }));

  return (
    <div className="floating-background">
      {/* Gradient blobs for ambient effect */}
      {blobs.map((blob) => (
        <motion.div
          key={blob.id}
          className="floating-shape"
          style={{
            width: blob.size,
            height: blob.size,
            left: `${blob.x}%`,
            top: `${blob.y}%`,
          }}
          animate={{
            y: [0, -40, 0],
            x: [0, 20, -20, 0],
            scale: [1, 1.15, 0.9, 1],
          }}
          transition={{
            duration: blob.duration,
            repeat: Infinity,
            delay: blob.delay,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* Chart icons */}
      {elements.map((element) => (
        <motion.div
          key={element.id}
          className="floating-chart"
          style={{
            left: `${element.x}%`,
            top: `${element.y}%`,
          }}
          animate={{
            y: [0, -50, 0],
            x: [0, Math.sin(element.id) * 30, 0],
            rotate: [element.rotation, element.rotation + 360],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: element.duration,
            repeat: Infinity,
            delay: element.delay,
            ease: "easeInOut",
          }}
        >
          <element.Icon size={element.size} color={element.color} />
        </motion.div>
      ))}
    </div>
  );
};

export default FloatingBackground;
