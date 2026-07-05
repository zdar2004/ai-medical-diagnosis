import styles from './ClinicalAssistant.module.css'

// Toggle this to preview the typing indicator — kept static, no hooks needed.
const SHOW_TYPING = false

// Static, illustrative data only — no API, no AI SDKs, no business logic.
const CONVERSATION = [
  {
    role: 'assistant',
    text: 'Hello Doctor. How can I assist you today?',
  },
  {
    role: 'user',
    text: 'Patient has persistent fever, cough and elevated WBC.',
  },
  {
    role: 'assistant',
    text: 'Based on the provided information, possible differential diagnoses include bacterial pneumonia and acute bronchitis. Further clinical evaluation is recommended.',
  },
  {
    role: 'user',
    text: 'What tests should I order?',
  },
  {
    role: 'assistant',
    text: 'Recommended Tests',
    list: ['CBC', 'Chest X-Ray', 'CRP', 'Blood Culture'],
  },
]

const SUGGESTED_QUESTIONS = [
  'Explain CBC Result',
  'Interpret ECG',
  'Summarize Clinical Notes',
  'Analyze Blood Report',
  'Suggest Further Tests',
]

function AssistantAvatar() {
  return (
    <span className={`${styles.avatar} ${styles.avatarAssistant}`} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path
          d="M9 3v4a3 3 0 0 0 6 0V3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M7 7v3a5 5 0 0 0 10 0V7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M12 15v3" strokeLinecap="round" />
        <circle cx="12" cy="20" r="1.4" />
        <circle cx="18.5" cy="7" r="1.6" />
      </svg>
    </span>
  )
}

function UserAvatar() {
  return (
    <span className={`${styles.avatar} ${styles.avatarUser}`} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
        <circle cx="12" cy="8.5" r="3.4" />
        <path d="M4.8 20c1.6-3.6 4.6-5.4 7.2-5.4s5.6 1.8 7.2 5.4" strokeLinecap="round" />
      </svg>
    </span>
  )
}

function Message({ message }) {
  const isAssistant = message.role === 'assistant'
  const rowClassName = isAssistant
    ? `${styles.messageRow} ${styles.messageRowAssistant}`
    : `${styles.messageRow} ${styles.messageRowUser}`
  const bubbleClassName = isAssistant
    ? `${styles.bubble} ${styles.bubbleAssistant}`
    : `${styles.bubble} ${styles.bubbleUser}`

  return (
    <li className={rowClassName}>
      {isAssistant && <AssistantAvatar />}
      <div className={bubbleClassName}>
        <p className={styles.bubbleText}>{message.text}</p>
        {message.list && (
          <ul className={styles.bubbleList}>
            {message.list.map((item) => (
              <li className={styles.bubbleListItem} key={item}>
                <span className={styles.bubbleListDot} aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        )}
      </div>
      {!isAssistant && <UserAvatar />}
    </li>
  )
}

function ClinicalAssistant() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>AI Clinical Assistant</p>
        <h1 className={styles.title}>Clinical AI Assistant</h1>
        <p className={styles.subtitle}>
          Ask medical questions and receive AI-assisted clinical guidance.
        </p>
      </section>

      <section className={styles.chatContainer} aria-label="Clinical assistant chat">
        {/* Conversation Area */}
        <div className={styles.conversationArea}>
          <ul className={styles.conversationList} aria-label="Conversation history">
            {CONVERSATION.map((message, index) => (
              <Message message={message} key={index} />
            ))}

            {SHOW_TYPING && (
              <li className={`${styles.messageRow} ${styles.messageRowAssistant}`}>
                <AssistantAvatar />
                <div className={`${styles.bubble} ${styles.bubbleAssistant}`}>
                  <span className={styles.typingIndicator} aria-label="Assistant is typing">
                    <span className={styles.typingDot} />
                    <span className={styles.typingDot} />
                    <span className={styles.typingDot} />
                  </span>
                </div>
              </li>
            )}
          </ul>

          {/* Suggested Questions */}
          <div className={styles.suggestions} aria-label="Suggested questions">
            {SUGGESTED_QUESTIONS.map((question) => (
              <button type="button" className={styles.suggestionChip} key={question}>
                {question}
              </button>
            ))}
          </div>
        </div>

        {/* Message Input Area */}
        <div className={styles.inputArea}>
          <textarea
            className={styles.messageInput}
            placeholder="Ask the AI Clinical Assistant..."
            rows={3}
            aria-label="Message input"
          />
          <div className={styles.inputControls}>
            <button type="button" className={styles.iconButton} aria-label="Attach file">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
                <path
                  d="M17.5 8.5 9.9 16.1a3 3 0 1 1-4.24-4.24l7.6-7.6a2 2 0 1 1 2.83 2.83l-7.6 7.6a1 1 0 1 1-1.42-1.42l6.9-6.9"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
            <button type="button" className={styles.iconButton} aria-label="Voice input">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
                <path d="M12 18v3" strokeLinecap="round" />
              </svg>
            </button>
            <button type="button" className={styles.sendButton}>
              Send
            </button>
          </div>
        </div>
      </section>

      {/* Information Card */}
      <section className={styles.noticeCard} aria-label="Clinical notice">
        <svg
          className={styles.noticeIcon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5" strokeLinecap="round" />
          <path d="M12 16h.01" strokeLinecap="round" />
        </svg>
        <div>
          <p className={styles.noticeTitle}>Clinical Notice</p>
          <p className={styles.noticeText}>
            The AI assistant provides clinical decision support only. Final
            medical decisions must always be made by qualified healthcare
            professionals.
          </p>
        </div>
      </section>
    </div>
  )
}

export default ClinicalAssistant