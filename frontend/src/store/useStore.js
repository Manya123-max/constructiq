import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useStore = create(
  persist(
    (set) => ({
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
      monitorProjectId: 'HP-001',
      setMonitorProjectId: (id) => set({ monitorProjectId: id }),

      // Projects
      projects: [],
      setProjects: (p) => set({ projects: p }),
    }),
    {
      name: 'constructiq-store',
      partialize: (state) => ({
        activePage: state.activePage,
        estimationResult: state.estimationResult,
        estimationError: state.estimationError,
        currentForm: state.currentForm,
        activeMonitorTab: state.activeMonitorTab,
        monitorProjectId: state.monitorProjectId,
      }),
    }
  )
)
