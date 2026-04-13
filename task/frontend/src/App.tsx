import { useState, useEffect } from 'react'
import './App.css'

interface Message {
  role: string
  content: string
  function?: string
  tool_calls?: any[]
  tool_call_id?: string
}

async function postConversation(logName: string, conversation: Message[]) {
  const response = await fetch(`http://localhost:8000/logs/${logName}/conversation`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(conversation)
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.json()
}

function App() {
  const [logs, setLogs] = useState<string[]>([])
  const [selectedLog, setSelectedLog] = useState<string>('')
  const [messages, setMessages] = useState<Message[][]>([])
  const [conversation, setConversation] = useState<Message[]>([])
  const [currentQuestion, setCurrentQuestion] = useState<string>('')
  const [selectedSample, setSelectedSample] = useState<number>(0)
  const [loading, setLoading] = useState(false)

  // Fetch available logs
  useEffect(() => {
    fetch('http://localhost:8000/logs')
      .then(res => res.json())
      .then(data => {
        setLogs(data)
        // Select the latest log by default
        if (data.length > 0) {
          setSelectedLog(data[0])
        }
      })
  }, [])

  // Fetch messages when a log is selected
  useEffect(() => {
    if (selectedLog) {
      setLoading(true)
      fetch(`http://localhost:8000/logs/${selectedLog}/samples`)
        .then(res => res.json())
        .then(data => {
          setMessages(data)
          setSelectedSample(0) // Reset to first sample when changing logs
          setLoading(false)
        })
        .catch(error => {
          console.error('Error fetching messages:', error)
          setLoading(false)
        })
    }
  }, [selectedLog])

  const renderMessage = (message: Message, index: number) => {
    return (
      <div key={index} className={`message ${message.role}`}>
        <div className="message-role">{message.role}{message.function && `: ${message.function}`}</div>
        {message.content && <div className="message-content">{message.content}</div>}

        {message.tool_calls?.map((toolCall, toolIndex) => (
          <div key={toolIndex} className="tool-call">
            <div className="tool-call-header">Tool Call: {toolCall.function?.name || toolCall.function}</div>
            <div className="tool-call-content">
              {JSON.stringify(toolCall.function?.arguments || toolCall.arguments, null, 2)}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderConversation = (message: Message, index: number) => {
    return (
      <div key={index} className={`message ${message.role}`}>
        <div className="message-role">{message.role}{message.function && `: ${message.function}`}</div>
        {message.content && <div className="message-content">{message.content}</div>}
      </div>
    )
  }

  return (
    <div className="container">
      <h1>Inspect Logs Viewer</h1>

      <div className="selectors">
        <div className="log-selector">
          <label htmlFor="log-select">Select Log File: </label>
          <select
            id="log-select"
            value={selectedLog}
            onChange={(e) => setSelectedLog(e.target.value)}
          >
            {logs.map((log) => (
              <option key={log} value={log}>
                {log}
              </option>
            ))}
          </select>
        </div>

        {messages.length > 0 && (
          <div className="sample-selector">
            <label htmlFor="sample-select">Select Sample: </label>
            <select
              id="sample-select"
              value={selectedSample}
              onChange={(e) => setSelectedSample(Number(e.target.value))}
            >
              {messages.map((_, index) => (
                <option key={index} value={index}>
                  Sample {index + 1}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div>Loading messages...</div>
      ) : messages.length > 0 ? (
        <div className="messages-container">
          <div className="sample">
            <h2>Sample {selectedSample + 1}</h2>
            {messages[selectedSample].map((message, index) => renderMessage(message, index))}
          </div>
        </div>
      ) : (
        <div>No messages available</div>
      )}

      {loading ? (
        <div>Loading conversation...</div>
      ) : conversation.length > 0 ? (
        <div className="conversation-container">
          <h2>Conversation about Log: {selectedLog}</h2>
          {conversation.map((message, index) => renderConversation(message, index))}
        </div>
      ) : (
        <div>No conversation available</div>
      )}

      <div className="question-input">
        <textarea rows={5} placeholder="Ask a question about the log..." onChange={
          (e) => setCurrentQuestion(e.target.value)
        } />
        <button onClick={
          () => {
            let request: Message[]
            if (conversation && conversation.length > 0) {
              request = [...conversation, { role: 'user', content: currentQuestion }]
            } else {
              request = [{ role: 'user', content: currentQuestion }]
            }

            setCurrentQuestion('')

            postConversation(selectedLog, request)
            .then(response => {
              console.log('Conversation response:', response)
              setConversation(response)
            })
            .catch(error => {
              console.error('Error posting conversation:', error)
            })
          }
        }>Send</button>
      </div>



    </div >
  )
}

export default App
