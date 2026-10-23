import '@testing-library/jest-dom';

// Mock ResizeObserver for Recharts in jsdom environment
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
