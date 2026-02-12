/**
 * ProjectWorkflowPage - Phase I Analyst Agent Workflow
 * 使用顶层 app-sidebar 进行导航
 */
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { workflowStateApi } from '@/api/workflowState'
import { ProjectDashboard } from '@/components/workflow/ProjectDashboard'
import { Step1ImportPage } from '@/components/workflow/steps/Step1ImportPage'
import { Step2ScriptAnalysisPage } from '@/components/workflow/steps/Step2ScriptAnalysisPage'
import { Step3NovelAnalysisPage } from '@/components/workflow/steps/Step3NovelAnalysisPage'
import { Step4AlignmentPage } from '@/components/workflow/steps/Step4AlignmentPage'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'

export default function ProjectWorkflowPage() {
  const { projectId, stepId } = useParams<{ projectId: string; stepId?: string }>()

  // Fetch workflow state
  const {
    data: phaseState,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['workflow-state', projectId],
    queryFn: () => workflowStateApi.getWorkflowState(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      // Poll more frequently if any step is running
      const data = query.state.data
      if (!data) return 10000
      
      const hasRunningStep =
        data.step_1_import?.status === 'running' ||
        data.step_2_script?.status === 'running' ||
        data.step_3_novel?.status === 'running' ||
        data.step_4_alignment?.status === 'running'
      return hasRunningStep ? 500 : 10000  // 500ms for running, 10s for idle
    },
  })

  // Logs state for real-time display
  const [workflowLogs, setWorkflowLogs] = useState<Array<{
    id: string
    timestamp: string
    level: 'info' | 'warning' | 'error'
    message: string
    step_id?: string
  }>>([])

  // WebSocket for real-time updates
  useEffect(() => {
    if (!projectId) return

    const websocket = workflowStateApi.createWebSocket(projectId)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setWorkflowLogs(prev => [...prev, {
        id: `ws-connected-${Date.now()}`,
        timestamp: new Date().toISOString(),
        level: 'info',
        message: 'Connected to workflow server',
      }])
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      // Add log entry
      const logLevel = data.type === 'step_failed' ? 'error' : 
                      data.type === 'progress_update' ? 'info' : 'info'
      
      const logMessage = data.current_task || data.message || 
                        `${data.type.replace('_', ' ')}: ${data.step_id || ''}`
      
      setWorkflowLogs(prev => [...prev, {
        id: `${Date.now()}-${Math.random()}`,
        timestamp: data.timestamp || new Date().toISOString(),
        level: logLevel,
        message: logMessage,
        step_id: data.step_id,
      }])

      // Refetch state on important updates
      if (
        data.type === 'progress_update' ||
        data.type === 'step_completed' ||
        data.type === 'step_failed'
      ) {
        refetch()
      }

      // Desktop notifications
      if (data.type === 'step_completed' || data.type === 'step_failed') {
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(data.type === 'step_completed' ? 'Task Completed' : 'Task Failed', {
            body: data.message || `Step ${data.step_id}`,
            icon: '/favicon.ico',
          })
        }
      }
    }

    websocket.onerror = () => {
      console.error('WebSocket error')
      setWorkflowLogs(prev => [...prev, {
        id: `ws-error-${Date.now()}`,
        timestamp: new Date().toISOString(),
        level: 'error',
        message: 'WebSocket connection error',
      }])
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setWorkflowLogs(prev => [...prev, {
        id: `ws-close-${Date.now()}`,
        timestamp: new Date().toISOString(),
        level: 'warning',
        message: 'Disconnected from workflow server',
      }])
    }

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    return () => {
      websocket.close()
    }
  }, [projectId, refetch])

  if (!projectId) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert>
          <AlertTitle>No Project Selected</AlertTitle>
          <AlertDescription>Please select a project from the sidebar</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full gap-2">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="text-muted-foreground">Loading workflow state...</span>
      </div>
    )
  }

  if (error || !phaseState) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <Alert variant="destructive">
          <AlertTitle>Failed to load workflow state</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : 'Unknown error'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Start workflow step
  const handleStartStep = async (stepId: string) => {
    try {
      const result = await workflowStateApi.startStep(projectId, stepId)
      console.log('Step started:', result)
      
      // Show success notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Workflow Started', {
          body: result.message || `Step ${stepId} started`,
          icon: '/favicon.ico',
        })
      }
      
      // Refetch workflow state
      refetch()
    } catch (error) {
      console.error('Failed to start step:', error)
      
      // Show error notification
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Workflow Failed to Start', {
          body: errorMessage,
          icon: '/favicon.ico',
        })
      }
      
      // Also show in UI (could use toast notification)
      alert(`Failed to start workflow: ${errorMessage}`)
    }
  }

  // Cancel workflow step
  const handleCancelStep = async (stepId: string) => {
    if (!confirm('Are you sure you want to cancel this workflow? Progress will be lost.')) {
      return
    }
    
    try {
      const result = await workflowStateApi.failStep(projectId, stepId, 'Cancelled by user')
      console.log('Step cancelled:', result)
      
      // Refetch workflow state
      refetch()
    } catch (error) {
      console.error('Failed to cancel step:', error)
      alert(`Failed to cancel workflow: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Stop workflow step
  const handleStopStep = async (stepId: string) => {
    if (!confirm('Are you sure you want to stop this workflow?')) {
      return
    }
    
    try {
      const result = await workflowStateApi.stopStep(projectId, stepId)
      console.log('Step stopped:', result)
      setWorkflowLogs(prev => [...prev, {
        id: `${Date.now()}-stop-${stepId}`,
        timestamp: new Date().toISOString(),
        level: 'warning',
        message: `Workflow stopped: ${result.message}`,
      }])
      refetch()
    } catch (error) {
      console.error('Failed to stop step:', error)
      alert(`Failed to stop workflow: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Start single episode
  const handleStartEpisode = async (episodeId: string) => {
    try {
      const result = await workflowStateApi.startEpisode(projectId, episodeId)
      console.log('Episode started:', result)
      setWorkflowLogs(prev => [...prev, {
        id: `${Date.now()}-start-ep-${episodeId}`,
        timestamp: new Date().toISOString(),
        level: 'info',
        message: `Started processing episode: ${episodeId}`,
      }])
      refetch()
    } catch (error) {
      console.error('Failed to start episode:', error)
      alert(`Failed to start episode: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Stop single episode
  const handleStopEpisode = async (episodeId: string) => {
    try {
      const result = await workflowStateApi.stopEpisode(projectId, episodeId)
      console.log('Episode stopped:', result)
      setWorkflowLogs(prev => [...prev, {
        id: `${Date.now()}-stop-ep-${episodeId}`,
        timestamp: new Date().toISOString(),
        level: 'warning',
        message: `Stopped episode: ${episodeId}`,
      }])
      refetch()
    } catch (error) {
      console.error('Failed to stop episode:', error)
      alert(`Failed to stop episode: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Pause workflow step (not yet implemented in backend)
  const handlePauseStep = async (stepId: string) => {
    alert('Pause functionality is not yet implemented. Use Stop to cancel the workflow.')
  }

  // Render appropriate page based on stepId
  return (
    <>
      {!stepId ? (
        <ProjectDashboard projectId={projectId} phaseState={phaseState} />
      ) : (
        <>
          {stepId === 'step_1_import' && (
            <Step1ImportPage projectId={projectId} stepState={phaseState.step_1_import} onComplete={() => refetch()} />
          )}
          {stepId === 'step_2_script' && (
            <Step2ScriptAnalysisPage 
              projectId={projectId} 
              stepState={phaseState.step_2_script}
              logs={workflowLogs.filter(log => !log.step_id || log.step_id === 'step_2_script')}
              onStart={() => handleStartStep('step_2_script')}
              onStartEpisode={handleStartEpisode}
              onStopEpisode={handleStopEpisode}
              onStopAll={() => handleStopStep('step_2_script')}
            />
          )}
          {stepId === 'step_3_novel' && (
            <Step3NovelAnalysisPage 
              projectId={projectId} 
              stepState={phaseState.step_3_novel}
              onStart={() => handleStartStep('step_3_novel')}
            />
          )}
          {stepId === 'step_4_alignment' && (
            <Step4AlignmentPage 
              projectId={projectId} 
              stepState={phaseState.step_4_alignment}
              onStart={() => handleStartStep('step_4_alignment')}
            />
          )}
        </>
      )}
    </>
  )
}
