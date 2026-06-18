'use client'

import { useEffect } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  message: string
  type?: 'error' | 'success' | 'warning' | 'info'
}

export default function Modal({ isOpen, onClose, title, message, type = 'info' }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const typeStyles = {
    error: {
      bg: 'from-red-50 to-rose-50',
      border: 'border-red-200',
      iconBg: 'from-red-500 to-rose-600',
      textColor: 'text-red-900',
      buttonBg: 'from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      )
    },
    success: {
      bg: 'from-green-50 to-emerald-50',
      border: 'border-green-200',
      iconBg: 'from-green-500 to-emerald-600',
      textColor: 'text-green-900',
      buttonBg: 'from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
    },
    warning: {
      bg: 'from-yellow-50 to-amber-50',
      border: 'border-yellow-200',
      iconBg: 'from-yellow-500 to-amber-600',
      textColor: 'text-yellow-900',
      buttonBg: 'from-yellow-600 to-amber-600 hover:from-yellow-700 hover:to-amber-700',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      )
    },
    info: {
      bg: 'from-blue-50 to-indigo-50',
      border: 'border-blue-200',
      iconBg: 'from-blue-500 to-indigo-600',
      textColor: 'text-blue-900',
      buttonBg: 'from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  }

  const style = typeStyles[type]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fadeIn"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full animate-slideUp">
        <div className={`bg-gradient-to-br ${style.bg} border-2 ${style.border} rounded-2xl p-8 text-center`}>
          {/* Icon */}
          <div className={`inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br ${style.iconBg} rounded-full mb-4 shadow-lg`}>
            {style.icon}
          </div>

          {/* Title */}
          <h3 className={`text-2xl font-bold ${style.textColor} mb-3`}>
            {title}
          </h3>

          {/* Message */}
          <p className="text-gray-700 mb-6 leading-relaxed">
            {message}
          </p>

          {/* Close Button */}
          <button
            onClick={onClose}
            className={`w-full bg-gradient-to-r ${style.buttonBg} text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5`}
          >
            Got it
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }

        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}
