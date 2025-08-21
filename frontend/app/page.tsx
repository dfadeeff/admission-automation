'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface Application {
  id: string
  status: string
  files: File[]
  targetProgram: string
  entity: string
  result?: any
}

export default function HomePage() {
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(false)
  const [targetProgram, setTargetProgram] = useState('Finanzmanagement')
  const [entity, setEntity] = useState('DE')
  const [applicantId, setApplicantId] = useState('')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf')
    if (pdfFiles.length === 0) {
      alert('Please upload PDF files only')
      return
    }
    
    // Generate a temporary ID for this application
    const tempId = Date.now().toString()
    setApplications(prev => [...prev, {
      id: tempId,
      status: 'ready',
      files: pdfFiles,
      targetProgram,
      entity
    }])
  }, [targetProgram, entity])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  })

  const submitApplication = async (app: Application) => {
    if (!applicantId.trim()) {
      alert('Please enter an Applicant ID')
      return
    }

    setLoading(true)
    
    try {
      const formData = new FormData()
      formData.append('applicant_id', applicantId)
      formData.append('target_program', app.targetProgram)
      formData.append('entity', app.entity)
      
      app.files.forEach(file => {
        formData.append('files', file)
      })

      const response = await fetch('http://localhost:8000/submit-application', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Update application with result
      setApplications(prev => prev.map(a => 
        a.id === app.id 
          ? { ...a, id: result.application_id, status: 'processing', result }
          : a
      ))

      // Poll for results
      pollForResults(result.application_id)

    } catch (error) {
      console.error('Submission failed:', error)
      alert('Failed to submit application: ' + error)
      setApplications(prev => prev.map(a => 
        a.id === app.id ? { ...a, status: 'error' } : a
      ))
    } finally {
      setLoading(false)
    }
  }

  const pollForResults = async (applicationId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/application/${applicationId}`)
      if (response.ok) {
        const result = await response.json()
        
        setApplications(prev => prev.map(app => 
          app.id === applicationId 
            ? { ...app, status: result.current_stage, result }
            : app
        ))

        // Continue polling if still processing
        if (result.current_stage === 'processing' || result.current_stage === 'classifying' || result.current_stage === 'extracting') {
          setTimeout(() => pollForResults(applicationId), 2000)
        }
      }
    } catch (error) {
      console.error('Failed to check status:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready': return <Upload className="w-5 h-5 text-blue-500" />
      case 'processing': 
      case 'classifying': 
      case 'extracting': return <Clock className="w-5 h-5 text-yellow-500 animate-spin" />
      case 'decision_made': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'error_handled': 
      case 'error': return <XCircle className="w-5 h-5 text-red-500" />
      default: return <AlertCircle className="w-5 h-5 text-gray-500" />
    }
  }

  const getDecisionColor = (status?: string) => {
    switch (status) {
      case 'APPROVED': return 'text-green-600 bg-green-50'
      case 'REJECTED': return 'text-red-600 bg-red-50'
      case 'REVIEW_REQUIRED': return 'text-yellow-600 bg-yellow-50'
      case 'MISSING_DOCS': return 'text-orange-600 bg-orange-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            IU Admissions System
          </h1>
          <p className="text-gray-600">
            Upload admission documents and get instant decisions powered by AI
          </p>
        </div>

        {/* Application Form */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Applicant ID
              </label>
              <input
                type="text"
                value={applicantId}
                onChange={(e) => setApplicantId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. test123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Program
              </label>
              <select
                value={targetProgram}
                onChange={(e) => setTargetProgram(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Finanzmanagement">Finanzmanagement</option>
                <option value="Business Administration">Business Administration</option>
                <option value="International Management">International Management</option>
                <option value="Computer Science">Computer Science</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Entity
              </label>
              <select
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="DE">Germany (DE)</option>
                <option value="UK">United Kingdom (UK)</option>
                <option value="CA">Canada (CA)</option>
              </select>
            </div>
          </div>

          {/* File Upload Area */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-blue-600">Drop the PDF files here...</p>
            ) : (
              <div>
                <p className="text-gray-600 mb-2">
                  Drag & drop PDF files here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supported: Abitur, A-Levels, IB Diploma, Transcripts, CV, Work Certificates
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Applications List */}
        {applications.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Applications</h2>
            
            {applications.map((app) => (
              <div key={app.id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(app.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">
                        Application {app.id}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {app.targetProgram} • {app.entity} • {app.files.length} files
                      </p>
                    </div>
                  </div>
                  
                  {app.status === 'ready' && (
                    <button
                      onClick={() => submitApplication(app)}
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                      {loading ? 'Submitting...' : 'Submit Application'}
                    </button>
                  )}
                </div>

                {/* Files */}
                <div className="mb-4">
                  <div className="flex flex-wrap gap-2">
                    {app.files.map((file, idx) => (
                      <div key={idx} className="flex items-center space-x-2 bg-gray-100 rounded px-3 py-1">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <span className="text-sm text-gray-700">{file.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Results */}
                {app.result && (
                  <div className="border-t pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Processing Status</h4>
                        <p className="text-sm text-gray-600 capitalize">{app.status.replace('_', ' ')}</p>
                      </div>
                      
                      {app.result.decision && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Decision</h4>
                          <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getDecisionColor(app.result.decision.status)}`}>
                            {app.result.decision.status}
                          </div>
                          <p className="text-sm text-gray-600 mt-2">
                            Confidence: {Math.round(app.result.decision.confidence * 100)}%
                          </p>
                        </div>
                      )}
                    </div>

                    {app.result.decision?.reasoning && (
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-900 mb-2">Reasoning</h4>
                        <p className="text-sm text-gray-600">{app.result.decision.reasoning}</p>
                      </div>
                    )}

                    {app.result.decision?.handbook_citations && app.result.decision.handbook_citations.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-900 mb-2">Handbook References</h4>
                        <div className="flex flex-wrap gap-2">
                          {app.result.decision.handbook_citations.map((citation: string, idx: number) => (
                            <span key={idx} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                              {citation}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {app.result.logs && (
                      <details className="mt-4">
                        <summary className="font-medium text-gray-900 cursor-pointer">Processing Logs</summary>
                        <div className="mt-2 space-y-2">
                          {app.result.logs.map((log: any, idx: number) => (
                            <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                              <span className="font-medium">{log.agent}</span>: {log.action}
                              {log.details && (
                                <pre className="text-xs mt-1 text-gray-600 overflow-x-auto">
                                  {JSON.stringify(log.details, null, 2)}
                                </pre>
                              )}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
