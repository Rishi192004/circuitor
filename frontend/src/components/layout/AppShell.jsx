import React from 'react'
import Toolbar from './Toolbar.jsx'
import ComponentSidebar from '../sidebar/ComponentSidebar.jsx'
import CircuitCanvas from '../canvas/CircuitCanvas.jsx'
import ValidationPanel from '../panel/ValidationPanel.jsx'

export default function AppShell() {
  return (
    <div className="app-shell">
      <Toolbar />
      <ComponentSidebar />
      <CircuitCanvas />
      <ValidationPanel />
    </div>
  )
}
