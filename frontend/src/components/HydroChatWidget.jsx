import React, { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import { useStore } from '../store/useStore'

const QUICK_PROMPTS = [
  '⚡ How is Francis turbine flow calculated?',
  '🧱 What is normal concrete intensity per MW?',
  '💰 Typical cost per MW for hydro in India?',
  '🏛️ What are CEA DPR submission norms?',
]

function renderFormattedMessage(content) {
  if (!content) return null
  const parts = content.split(/(\*\*.*?\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ fontWeight: 700 }}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

export function HydroChatWidget() {
  const { estimationResult, monitorProjectId } = useStore()
  const [isOpen, setIsOpen] = useState(false)
  const [unread, setUnread] = useState(true)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hello! I am your Hydro AI Assistant. Ask me anything about hydroelectric estimations, turbine selection, material BOQs, financial costs, or CEA/PARIVESH statutory guidelines.'
    }
  ])
  const [inputMsg, setInputMsg] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
      setUnread(false)
    }
  }, [messages, isOpen])

  const handleSend = async (textToSend) => {
    const query = textToSend || inputMsg
    if (!query.trim() || isLoading) return

    const newMessages = [...messages, { role: 'user', content: query }]
    setMessages(newMessages)
    if (!textToSend) setInputMsg('')
    setIsLoading(true)

    try {
      const res = await api.sendChat(newMessages, estimationResult, monitorProjectId)
      if (res && res.reply) {
        setMessages([...newMessages, { role: 'assistant', content: res.reply }])
      } else {
        setMessages([...newMessages, { role: 'assistant', content: '⚠️ Sorry, I could not generate a response. Please try again.' }])
      }
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: '⚠️ Could not connect to assistant engine. Please try again.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* ─── Stitch Floating Bot Button (Bottom Right) ─── */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="floating-chat-btn"
        aria-label="Toggle Hydro AI Assistant"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '54px',
          height: '54px',
          borderRadius: '50%',
          background: '#005F6A',
          color: '#FFFFFF',
          border: 'none',
          boxShadow: '0 6px 20px rgba(0, 95, 106, 0.45)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.6rem',
          cursor: 'pointer',
          zIndex: 1000,
          transition: 'all 0.2s ease'
        }}
      >
        <span>{isOpen ? '✕' : '🤖'}</span>
        {unread && !isOpen && (
          <span
            style={{
              position: 'absolute',
              top: '-2px',
              right: '-2px',
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: '#FF1744',
              color: '#FFFFFF',
              fontSize: '0.68rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid #FFFFFF'
            }}
          >
            1
          </span>
        )}
      </button>

      {/* ─── Pop-Up Chat Drawer Window ─── */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '90px',
            right: '24px',
            width: '380px',
            maxHeight: '560px',
            height: '80vh',
            background: '#FFFFFF',
            borderRadius: '16px',
            boxShadow: '0 12px 32px rgba(15, 23, 42, 0.18)',
            border: '1px solid #E2E8F0',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: 1000
          }}
        >
          {/* Header */}
          <div
            style={{
              background: '#005F6A',
              color: '#FFFFFF',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.4rem' }}>🤖</span>
              <div>
                <div style={{ fontWeight: 800, fontSize: '0.92rem' }}>Hydro Specialist Assistant</div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: '#FFFFFF', fontSize: '1.2rem', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          {/* Messages Container */}
          <div
            style={{
              flex: 1,
              padding: '14px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              background: '#F8FAFC'
            }}
          >
            {messages.map((m, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '10px 14px',
                    borderRadius: m.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    background: m.role === 'user' ? '#005F6A' : '#FFFFFF',
                    color: m.role === 'user' ? '#FFFFFF' : '#0F172A',
                    fontSize: '0.82rem',
                    border: m.role === 'user' ? 'none' : '1px solid #E2E8F0',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                  }}
                >
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                    {renderFormattedMessage(m.content)}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ background: '#FFFFFF', padding: '8px 12px', borderRadius: '8px', border: '1px solid #E2E8F0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  ⚡ Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          <div style={{ padding: '8px 12px', background: '#FFFFFF', borderTop: '1px solid #F1F5F9', display: 'flex', gap: '6px', overflowX: 'auto' }}>
            {QUICK_PROMPTS.map((qp, i) => (
              <button
                key={i}
                onClick={() => handleSend(qp)}
                style={{
                  whiteSpace: 'nowrap',
                  padding: '4px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  background: '#F1F5F9',
                  border: '1px solid #CBD5E1',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  color: 'var(--text-secondary)'
                }}
                disabled={isLoading}
              >
                {qp}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div style={{ padding: '10px 12px', background: '#FFFFFF', borderTop: '1px solid #E2E8F0', display: 'flex', gap: '8px' }}>
            <input
              type="text"
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '0.85rem',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                outline: 'none'
              }}
              placeholder="Ask hydro plant questions..."
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              onClick={() => handleSend()}
              style={{
                background: '#005F6A',
                color: '#FFFFFF',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontWeight: 700,
                cursor: 'pointer'
              }}
              disabled={isLoading || !inputMsg.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
