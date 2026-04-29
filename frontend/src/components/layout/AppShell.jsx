import React from 'react'
import Toolbar from './Toolbar.jsx'
import ComponentSidebar from '../sidebar/ComponentSidebar.jsx'
import CircuitCanvas from '../canvas/CircuitCanvas.jsx'
import AnalysisSidebar from '../sidebar/AnalysisSidebar.jsx'

export default function AppShell() {
  return (
    <div className="app-shell">
      <Toolbar />
      <ComponentSidebar />
      <CircuitCanvas />
      <AnalysisSidebar />
    </div>
  )
}
