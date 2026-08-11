import { create } from 'zustand'

export const useStore = create((set) => ({
  // Navigation
  activePage: 'estimate',
  setActivePage: (page) => set({ activePage: page }),

  // Estimation
  estimationResult: null,
  isEstimating: false,
  estimationError: null,
  currentForm: null,
  setEstimationResult: (result) => set({ estimationResult: result, estimationError: null }),
  setIsEstimating: (v) => set({ isEstimating: v }),
  setEstimationError: (e) => set({ estimationError: e }),
  setCurrentForm: (form) => set({ currentForm: form }),

  // Monitoring
  activeMonitorTab: 'status',
  setActiveMonitorTab: (tab) => set({ activeMonitorTab: tab }),
  monitorProjectId: 'H001',
  setMonitorProjectId: (id) => set({ monitorProjectId: id }),

  // Projects
  projects: [],
  setProjects: (p) => set({ projects: p }),
}))
