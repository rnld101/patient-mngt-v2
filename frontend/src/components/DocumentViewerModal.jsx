import React, { useState, useEffect } from 'react'

export const DocumentViewerModal = ({ isOpen, onClose, doc, url }) => {
  if (!isOpen || !doc) return null

  const [loading, setLoading] = useState(true)
  const fileName = doc.file_name || 'document'
  const fileExtension = fileName.split('.').pop().toLowerCase()

  // Determine file type category
  let viewType = 'fallback'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'].includes(fileExtension)) {
    viewType = 'image'
  } else if (fileExtension === 'pdf') {
    viewType = 'pdf'
  }

  // Clear loading spinner after iframe or image loads
  useEffect(() => {
    setLoading(true)
  }, [url, doc])

  // Get size classes based on view type
  const getModalSizeClass = () => {
    switch (viewType) {
      case 'pdf':
        return 'max-w-5xl w-[95vw] h-[85vh]'
      case 'image':
        return 'max-w-4xl w-[90vw] max-h-[90vh]'
      default:
        return 'max-w-md w-full'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop with Glassmorphism */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-md transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div 
        className={`relative bg-white rounded-2xl shadow-2xl border border-slate-100 flex flex-col overflow-hidden transform transition-all duration-300 scale-100 ${getModalSizeClass()}`}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <span className="px-2.5 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
              {doc.document_type}
            </span>
            <h3 className="text-base font-semibold text-slate-800 truncate max-w-[200px] sm:max-w-[400px]">
              {fileName}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200/50 transition-colors duration-150"
            aria-label="Close modal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-auto bg-slate-100 flex items-center justify-center p-4 relative">
          
          {/* Loading Indicator */}
          {loading && viewType !== 'fallback' && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-100/80 z-10">
              <div className="flex flex-col items-center space-y-3">
                <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm font-medium text-slate-500">Loading document...</p>
              </div>
            </div>
          )}

          {/* PDF View (iframe) */}
          {viewType === 'pdf' && (
            <iframe
              src={url}
              title={fileName}
              className="w-full h-full rounded-lg bg-white border-0"
              onLoad={() => setLoading(false)}
            />
          )}

          {/* Image View */}
          {viewType === 'image' && (
            <div className="flex items-center justify-center w-full h-full max-h-[70vh]">
              <img
                src={url}
                alt={fileName}
                className="max-w-full max-h-full object-contain rounded-lg shadow-md bg-white"
                onLoad={() => setLoading(false)}
                onError={() => setLoading(false)}
              />
            </div>
          )}

          {/* Fallback View (Download Card) */}
          {viewType === 'fallback' && (
            <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-100 text-center max-w-sm w-full mx-auto my-6">
              <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-blue-100">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h4 className="text-lg font-bold text-slate-800 mb-1">
                Preview Not Available
              </h4>
              <p className="text-xs text-slate-500 mb-6 px-2">
                This file format ({fileExtension.toUpperCase()}) cannot be rendered directly in the browser.
              </p>
              <a
                href={url}
                download={fileName}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center w-full px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-150 space-x-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download File</span>
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
