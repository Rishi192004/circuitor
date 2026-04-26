/**
 * circuitStore.js — Zustand store for the Circuitor canvas.
 *
 * Internal circuit state shape (matches the spec):
 * {
 *   circuit_id: string,          ← UUID, generated once per session
 *   templates: Template[],       ← static TEMPLATES constant, always full list
 *   instances: Instance[],       ← placed components: { id, type, position:{x,y}, properties }
 *   nets: Net[],                 ← wires: { id, pins: ["CompId.pinName", ...] }
 * }
 *
 * Autosaved to localStorage["circuit_autosave"] after every mutation.
 * Rehydrated from localStorage on first store creation.
 */

import { create } from 'zustand'
import { COMPONENT_LIBRARY, TEMPLATES } from '../constants/components.js'
import { toBackendFormat } from '../serializer/toCircuitJSON.js'
import { validateCircuit } from '../api/validateCircuit.js'
import { parseSuggestionsFromResult } from '../serializer/parseSuggestions.js'

// ── Constants ──────────────────────────────────────────────────────────────

const GRID = 20
const LS_KEY = 'circuit_autosave'

// ── Helpers ────────────────────────────────────────────────────────────────

function snap(v) {
  return Math.round(v / GRID) * GRID
}

/** Reference-designator counters (R1, R2, C1 …) — module-scoped so they
 *  survive store resets but NOT page reloads (intentional: rehydration
 *  will re-parse IDs from the saved state). */
const counters = {}
function generateId(type) {
  const sym = COMPONENT_LIBRARY[type]?.symbol ?? 'X'
  counters[sym] = (counters[sym] ?? 0) + 1
  return `${sym}${counters[sym]}`
}

/** Bump the counter high enough that new IDs won't collide with
 *  the IDs already present in a rehydrated circuit. */
function syncCountersFromInstances(instances) {
  instances.forEach(inst => {
    const lib = COMPONENT_LIBRARY[inst.type]
    if (!lib) return
    const sym = lib.symbol
    // Extract the numeric suffix from "R2" → 2
    const match = inst.id.match(/^([A-Z]+)(\d+)$/)
    if (match && match[1] === sym) {
      const n = parseInt(match[2], 10)
      counters[sym] = Math.max(counters[sym] ?? 0, n)
    }
  })
}

let netCounter = 0
function generateNetId() {
  netCounter++
  return `net_${netCounter}`
}
function syncNetCounterFromNets(nets) {
  nets.forEach(n => {
    const match = n.id.match(/^net_(\d+)$/)
    if (match) netCounter = Math.max(netCounter, parseInt(match[1], 10))
  })
}

/** Generate a session-unique UUID */
function newCircuitId() {
  return crypto.randomUUID()
}

let validationTimeout = null

// ── localStorage helpers ───────────────────────────────────────────────────

/** Persist only the serialisable circuit data (not UI state). */
function persist(circuit_id, instances, nets) {
  try {
    const payload = { circuit_id, templates: TEMPLATES, instances, nets }
    localStorage.setItem(LS_KEY, JSON.stringify(payload))
  } catch { /* quota errors — silently ignore */ }
}

/** Load saved circuit from localStorage. Returns null if nothing saved. */
function loadSaved() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

// ── Initial state from localStorage ───────────────────────────────────────

const saved = loadSaved()
let initialCircuitId = newCircuitId()
let initialInstances  = []
let initialNets       = []

if (saved) {
  initialCircuitId = saved.circuit_id ?? newCircuitId()
  initialInstances = saved.instances ?? []
  initialNets      = saved.nets ?? []
  // Sync counters so new IDs don't collide with rehydrated ones
  syncCountersFromInstances(initialInstances)
  syncNetCounterFromNets(initialNets)
}

// ── Store ──────────────────────────────────────────────────────────────────

export const useCircuitStore = create((set, get) => ({
  // ── Serialisable circuit state ─────────────────────────────
  circuit_id: initialCircuitId,
  templates: TEMPLATES,          // static — always the full list
  instances: initialInstances,
  nets: initialNets,

  // ── Transient UI state (NOT persisted) ─────────────────────
  selectedId: null,
  highlightedIds: [],            // [{ id, severity }] — drives canvas glow
  wireInProgress: null,          // { fromComponentId, fromPinName } | null

  // ── Validation state ────────────────────────────────────────
  isValidating: false,
  validationResult: null,
  apiError: null,
  suggestions: [],

  // ═══════════════ Internal helper ═════════════════════════════════════════

  _persist() {
    const { circuit_id, instances, nets } = get()
    persist(circuit_id, instances, nets)
  },

  debouncedValidation() {
    if (validationTimeout) clearTimeout(validationTimeout)
    validationTimeout = setTimeout(() => {
      get().runValidation()
    }, 400)
  },

  setSuggestions(suggestions) {
    set({ suggestions })
  },

  clearSuggestions() {
    set({ suggestions: [] })
  },

  cycleFocus() {
    const { suggestions } = get()
    if (suggestions.length === 0) return
    const idx = suggestions.findIndex(s => s.focused)
    const nextIdx = (idx + 1) % suggestions.length
    set({
      suggestions: suggestions.map((s, i) => ({ ...s, focused: i === nextIdx }))
    })
  },

  focusSuggestion(suggestionId) {
    const { suggestions } = get()
    set({
      suggestions: suggestions.map(s => ({ ...s, focused: s.id === suggestionId }))
    })
  },

  acceptSuggestion(suggestionId) {
    const { suggestions, instances } = get()
    const suggestion = suggestions.find(s => s.id === suggestionId)
    if (!suggestion) return

    // 1. Add instance
    const type = suggestion.component_type
    const lib = COMPONENT_LIBRARY[type]
    if (!lib) return
    
    const id = generateId(type)
    const newInstance = {
      id,
      type,
      position: { x: snap(suggestion.position.x), y: snap(suggestion.position.y) },
      properties: { ...lib.defaultProps },
    }

    // 2. Add net connecting the new ghost pin to the target pin
    // Default to the first pin of the new component
    const firstPinName = Object.keys(lib.pins)[0]
    const netId = generateNetId()
    const newNet = { id: netId, pins: [suggestion.attach_to, `${id}.${firstPinName}`] }

    set(state => ({
      instances: [...state.instances, newInstance],
      nets: [...state.nets, newNet],
      selectedId: id,
    }))
    
    get()._persist()
    get().clearSuggestions()
    get().debouncedValidation()
  },

  // ═══════════════ Instance actions ════════════════════════════════════════

  addInstance(type, x, y) {
    get().clearSuggestions()
    const lib = COMPONENT_LIBRARY[type]
    if (!lib) return
    const id = generateId(type)
    const newInstance = {
      id,
      type,
      position: { x: snap(x), y: snap(y) },
      properties: { ...lib.defaultProps },
    }
    set(state => ({
      instances: [...state.instances, newInstance],
      selectedId: id,
    }))
    get()._persist()
    get().debouncedValidation()
  },

  moveInstance(id, x, y) {
    get().clearSuggestions()
    set(state => ({
      instances: state.instances.map(inst =>
        inst.id === id
          ? { ...inst, position: { x: snap(x), y: snap(y) } }
          : inst
      ),
    }))
    get()._persist()
    get().debouncedValidation()
  },

  deleteSelected() {
    get().clearSuggestions()
    const { selectedId } = get()
    if (!selectedId) return
    set(state => ({
      instances: state.instances.filter(i => i.id !== selectedId),
      // Remove any net that references this instance
      nets: state.nets.filter(n =>
        !n.pins.some(pinStr => pinStr.startsWith(`${selectedId}.`))
      ),
      selectedId: null,
      highlightedIds: state.highlightedIds.filter(h => h.id !== selectedId),
    }))
    get()._persist()
    get().debouncedValidation()
  },

  updateProperty(id, key, value) {
    get().clearSuggestions()
    set(state => ({
      instances: state.instances.map(inst =>
        inst.id === id
          ? { ...inst, properties: { ...inst.properties, [key]: value } }
          : inst
      ),
    }))
    get()._persist()
    get().debouncedValidation()
  },

  selectInstance(id) {
    set({ selectedId: id })
  },

  clearSelection() {
    set({ selectedId: null })
  },

  // ═══════════════ Wiring actions ══════════════════════════════════════════

  startWire(fromComponentId, fromPinName) {
    set({ wireInProgress: { fromComponentId, fromPinName } })
  },

  completeWire(toComponentId, toPinName) {
    get().clearSuggestions()
    const { wireInProgress } = get()
    if (!wireInProgress) return
    const { fromComponentId, fromPinName } = wireInProgress

    // Reject self-connections
    if (fromComponentId === toComponentId && fromPinName === toPinName) {
      set({ wireInProgress: null })
      return
    }

    const netId = generateNetId()
    // Store pins in "ComponentId.pinName" string format (backend graph engine format)
    const fromPin = `${fromComponentId}.${fromPinName}`
    const toPin   = `${toComponentId}.${toPinName}`

    set(state => ({
      nets: [
        ...state.nets,
        { id: netId, pins: [fromPin, toPin] },
      ],
      wireInProgress: null,
    }))
    get()._persist()
    get().debouncedValidation()
  },

  cancelWire() {
    set({ wireInProgress: null })
  },

  deleteNet(netId) {
    get().clearSuggestions()
    set(state => ({ nets: state.nets.filter(n => n.id !== netId) }))
    get()._persist()
    get().debouncedValidation()
  },

  // ═══════════════ Highlight ═══════════════════════════════════════════════

  setHighlightedIds(ids) {
    set({ highlightedIds: ids })
  },

  clearHighlights() {
    set({ highlightedIds: [] })
  },

  // ═══════════════ Validate ════════════════════════════════════════════════

  async runValidation() {
    const state = get()
    
    // Minimum threshold guard
    if (state.instances.length < 2) {
      set({ validationResult: null, apiError: null, isValidating: false, suggestions: [] })
      return
    }

    if (state.isValidating) return
    set({ isValidating: true, apiError: null, validationResult: null, highlightedIds: [] })

    try {
      // Build the frontend circuitState, then convert to the backend wire format
      const circuitState = {
        circuit_id: state.circuit_id,
        templates: state.templates,
        instances: state.instances,
        nets: state.nets,
      }
      const backendPayload = toBackendFormat(circuitState)
      const result = await validateCircuit(backendPayload)
      set({ validationResult: result, isValidating: false })
      if (result.status === 'ok') {
        get().clearSuggestions()
      } else {
        const newSuggestions = parseSuggestionsFromResult(result, state.instances)
        set({ suggestions: newSuggestions })
      }
    } catch (err) {
      set({ apiError: err.message, isValidating: false, suggestions: [] })
    }
  },

  clearApiError() {
    set({ apiError: null })
  },

  // ═══════════════ Reset ═══════════════════════════════════════════════════

  clearCanvas() {
    // Reset module-level counters so IDs restart from 1
    Object.keys(counters).forEach(k => { counters[k] = 0 })
    netCounter = 0
    const freshId = newCircuitId()
    set({
      circuit_id: freshId,
      instances: [],
      nets: [],
      selectedId: null,
      highlightedIds: [],
      wireInProgress: null,
      validationResult: null,
      apiError: null,
      isValidating: false,
      suggestions: [],
    })
    persist(freshId, [], [])
  },
}))

// Expose to window for automated testing
if (typeof window !== 'undefined') {
  window.__circuitStore = useCircuitStore
}
