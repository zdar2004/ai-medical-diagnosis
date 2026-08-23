import { useEffect, useRef, useState } from "react";
import styles from "./ClinicalAssistant.module.css";
import ReactMarkdown from "react-markdown";
import {
  startConversation,
  continueConversation,
  getConversationHistory,
} from "../../services/clinicalAssistantService";

const SUGGESTED_QUESTIONS = [
  "Explain CBC Result",
  "Interpret ECG",
  "Summarize Clinical Notes",
  "Analyze Blood Report",
  "Suggest Further Tests",
];

const MAX_ATTACHMENTS = 5;

const MAX_FILE_SIZE = 20 * 1024 * 1024;

const ALLOWED_FILE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
  "text/plain",
];

function AssistantAvatar() {
  return (
    <span
      className={`${styles.avatar} ${styles.avatarAssistant}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
      >
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
  );
}

function UserAvatar() {
  return (
    <span
      className={`${styles.avatar} ${styles.avatarUser}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
      >
        <circle cx="12" cy="8.5" r="3.4" />
        <path
          d="M4.8 20c1.6-3.6 4.6-5.4 7.2-5.4s5.6 1.8 7.2 5.4"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

function AttachmentIcon({ type }) {
  if (type?.startsWith("image/")) {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        aria-hidden="true"
      >
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <circle cx="8.5" cy="9" r="1.5" />
        <path
          d="m4 17 5-5 3.5 3.5 2.5-2.5 5 5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      aria-hidden="true"
    >
      <path
        d="M6 3h8l4 4v14H6z"
        strokeLinejoin="round"
      />
      <path
        d="M14 3v5h5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Message({ message }) {
  const isAssistant = message.role === "assistant";

  const rowClassName = isAssistant
    ? `${styles.messageRow} ${styles.messageRowAssistant}`
    : `${styles.messageRow} ${styles.messageRowUser}`;

  const bubbleClassName = isAssistant
    ? `${styles.bubble} ${styles.bubbleAssistant}`
    : `${styles.bubble} ${styles.bubbleUser}`;

  return (
    <li className={rowClassName}>
      {isAssistant && <AssistantAvatar />}

      <div className={bubbleClassName}>
        {message.attachments?.length > 0 && (
          <div className={styles.messageAttachments}>
            {message.attachments.map((attachment, index) => (
              <div
                className={styles.messageAttachment}
                key={`${attachment.name}-${index}`}
              >
                <AttachmentIcon type={attachment.type} />

                <span>
                  {attachment.name}
                </span>
              </div>
            ))}
          </div>
        )}

        {message.content && (
          <div className={styles.bubbleText}>
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {!isAssistant && <UserAvatar />}
    </li>
  );
}

function ClinicalAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);

  const [attachments, setAttachments] = useState([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const fileInputRef = useRef(null);
  const conversationEndRef = useRef(null);

  // =========================================================
  // Scroll
  // =========================================================

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  // =========================================================
  // Load existing conversation
  // =========================================================

  useEffect(() => {
    const savedConversationId =
      localStorage.getItem(
        "clinical_conversation_id"
      );

    if (!savedConversationId) {
      return;
    }

    const loadHistory = async () => {
      try {
        const data =
          await getConversationHistory(
            savedConversationId
          );

        setConversationId(
          data.conversation_id
        );

        setMessages(
          data.messages || []
        );
      } catch (err) {
        console.error(
          "Failed to load conversation history:",
          err
        );

        localStorage.removeItem(
          "clinical_conversation_id"
        );
      }
    };

    loadHistory();
  }, []);

  // =========================================================
  // File selection
  // =========================================================

  const handleFileSelection = (event) => {
    const selectedFiles = Array.from(
      event.target.files || []
    );

    if (!selectedFiles.length) {
      return;
    }

    setError("");

    const availableSlots =
      MAX_ATTACHMENTS - attachments.length;

    if (availableSlots <= 0) {
      setError(
        `You can attach a maximum of ${MAX_ATTACHMENTS} files.`
      );

      event.target.value = "";
      return;
    }

    const filesToAdd =
      selectedFiles.slice(
        0,
        availableSlots
      );

    const invalidFile = filesToAdd.find(
      (file) =>
        !ALLOWED_FILE_TYPES.includes(
          file.type
        )
    );

    if (invalidFile) {
      setError(
        `Unsupported file type: ${invalidFile.name}. ` +
          "Please upload PNG, JPG, JPEG, WEBP, PDF or TXT files."
      );

      event.target.value = "";
      return;
    }

    const oversizedFile =
      filesToAdd.find(
        (file) =>
          file.size > MAX_FILE_SIZE
      );

    if (oversizedFile) {
      setError(
        `${oversizedFile.name} is too large. ` +
          "Maximum file size is 20 MB."
      );

      event.target.value = "";
      return;
    }

    setAttachments((previous) => [
      ...previous,
      ...filesToAdd,
    ]);

    event.target.value = "";
  };

  // =========================================================
  // Remove attachment
  // =========================================================

  const removeAttachment = (index) => {
    setAttachments((previous) =>
      previous.filter(
        (_, fileIndex) =>
          fileIndex !== index
      )
    );
  };

  // =========================================================
  // Send message
  // =========================================================

  const sendMessage = async (
    messageText = input
  ) => {
    const trimmedMessage =
      messageText.trim();

    if (
      !trimmedMessage &&
      attachments.length === 0
    ) {
      return;
    }

    if (isLoading) {
      return;
    }

    setError("");

    const messageAttachments =
      attachments.map((file) => ({
        name: file.name,
        type: file.type,
        size: file.size,
      }));

    const userMessage = {
      role: "user",
      content: trimmedMessage,
      attachments: messageAttachments,
      timestamp: new Date().toISOString(),
    };

    setMessages((previousMessages) => [
      ...previousMessages,
      userMessage,
    ]);

    setInput("");

    const filesToSend = [...attachments];

    setAttachments([]);

    setIsLoading(true);

    try {
      let data;

      if (!conversationId) {
        data = await startConversation(
          trimmedMessage ||
            "Please analyze the attached file(s).",
          filesToSend
        );

        setConversationId(
          data.conversation_id
        );

        localStorage.setItem(
          "clinical_conversation_id",
          data.conversation_id
        );
      } else {
        data = await continueConversation(
          conversationId,
          trimmedMessage ||
            "Please analyze the attached file(s).",
          filesToSend
        );
      }

      const assistantMessage = {
        role: "assistant",
        content: data.response,
        timestamp: data.generated_at,
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

    } catch (err) {
      console.error(
        "Clinical Assistant error:",
        err
      );

      const backendMessage =
        err.response?.data?.detail ||
        "Something went wrong while contacting the Clinical Assistant.";

      setError(
        Array.isArray(backendMessage)
          ? backendMessage
              .map(
                (item) =>
                  item.msg
              )
              .join(", ")
          : backendMessage
      );

    } finally {
      setIsLoading(false);
    }
  };

  // =========================================================
  // Submit
  // =========================================================

  const handleSubmit = (event) => {
    event.preventDefault();

    sendMessage();
  };

  // =========================================================
  // Suggestions
  // =========================================================

  const handleSuggestionClick = (
    question
  ) => {
    sendMessage(question);
  };

  // =========================================================
  // Render
  // =========================================================

  return (
    <div className={styles.page}>

      <section className={styles.header}>
        <p className={styles.eyebrow}>
          AI Clinical Assistant
        </p>

        <h1 className={styles.title}>
          Clinical AI Assistant
        </h1>

        <p className={styles.subtitle}>
          Ask medical questions and receive
          AI-assisted clinical guidance.
        </p>
      </section>

      <section
        className={styles.chatContainer}
        aria-label="Clinical assistant chat"
      >

        {/* =================================================
            Conversation
        ================================================= */}

        <div
          className={styles.conversationArea}
        >
          <ul
            className={
              styles.conversationList
            }
            aria-label="Conversation history"
          >

            {messages.map(
              (message, index) => (
                <Message
                  message={message}
                  key={`${
                    message.timestamp ||
                    index
                  }-${index}`}
                />
              )
            )}

            {isLoading && (
              <li
                className={`${styles.messageRow} ${styles.messageRowAssistant}`}
              >
                <AssistantAvatar />

                <div
                  className={`${styles.bubble} ${styles.bubbleAssistant}`}
                >
                  <span
                    className={
                      styles.typingIndicator
                    }
                    aria-label="Assistant is typing"
                  >
                    <span
                      className={
                        styles.typingDot
                      }
                    />
                    <span
                      className={
                        styles.typingDot
                      }
                    />
                    <span
                      className={
                        styles.typingDot
                      }
                    />
                  </span>
                </div>
              </li>
            )}

            <div
              ref={conversationEndRef}
            />
          </ul>

          {/* Error */}

          {error && (
            <p
              style={{
                color:
                  "var(--color-signal)",
                margin: 0,
                fontSize:
                  "var(--fs-sm)",
              }}
            >
              {error}
            </p>
          )}

          {/* Suggestions */}

          <div
            className={
              styles.suggestions
            }
            aria-label="Suggested questions"
          >
            {SUGGESTED_QUESTIONS.map(
              (question) => (
                <button
                  type="button"
                  className={
                    styles.suggestionChip
                  }
                  key={question}
                  onClick={() =>
                    handleSuggestionClick(
                      question
                    )
                  }
                  disabled={
                    isLoading ||
                    attachments.length > 0
                  }
                >
                  {question}
                </button>
              )
            )}
          </div>
        </div>

        {/* =================================================
            Input
        ================================================= */}

        <form
          className={styles.inputArea}
          onSubmit={handleSubmit}
        >

          {/* Attachment preview */}

          {attachments.length > 0 && (
            <div
              className={
                styles.attachmentsPreview
              }
              aria-label="Selected attachments"
            >
              {attachments.map(
                (file, index) => (
                  <div
                    className={
                      styles.attachmentChip
                    }
                    key={`${file.name}-${index}`}
                  >
                    <span
                      className={
                        styles.attachmentIcon
                      }
                    >
                      <AttachmentIcon
                        type={
                          file.type
                        }
                      />
                    </span>

                    <span
                      className={
                        styles.attachmentName
                      }
                      title={file.name}
                    >
                      {file.name}
                    </span>

                    <button
                      type="button"
                      className={
                        styles.removeAttachmentButton
                      }
                      onClick={() =>
                        removeAttachment(
                          index
                        )
                      }
                      disabled={
                        isLoading
                      }
                      aria-label={`Remove ${file.name}`}
                    >
                      ×
                    </button>
                  </div>
                )
              )}
            </div>
          )}

          <textarea
            className={
              styles.messageInput
            }
            placeholder="Ask the AI Clinical Assistant..."
            rows={3}
            aria-label="Message input"
            value={input}
            onChange={(event) =>
              setInput(
                event.target.value
              )
            }
            disabled={isLoading}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();
                handleSubmit(event);
              }
            }}
          />

          <div
            className={
              styles.inputControls
            }
          >

            {/* Hidden file input */}

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.webp,.pdf,.txt"
              className={
                styles.hiddenFileInput
              }
              onChange={
                handleFileSelection
              }
              disabled={isLoading}
            />

            {/* Attach */}

            <button
              type="button"
              className={
                styles.iconButton
              }
              aria-label="Attach file"
              disabled={
                isLoading ||
                attachments.length >=
                  MAX_ATTACHMENTS
              }
              onClick={() =>
                fileInputRef.current?.click()
              }
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                aria-hidden="true"
              >
                <path
                  d="M17.5 8.5 9.9 16.1a3 3 0 1 1-4.24-4.24l7.6-7.6a2 2 0 1 1 2.83 2.83l-7.6 7.6a1 1 0 1 1-1.42-1.42l6.9-6.9"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>

            {/* Voice - reserved for next stage */}

            <button
              type="button"
              className={
                styles.iconButton
              }
              aria-label="Voice input"
              disabled={true}
              title="Voice input coming soon"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                aria-hidden="true"
              >
                <rect
                  x="9"
                  y="3"
                  width="6"
                  height="11"
                  rx="3"
                />
                <path
                  d="M5 11a7 7 0 0 0 14 0"
                  strokeLinecap="round"
                />
                <path
                  d="M12 18v3"
                  strokeLinecap="round"
                />
              </svg>
            </button>

            {/* Send */}

            <button
              type="submit"
              className={
                styles.sendButton
              }
              disabled={
                isLoading ||
                (
                  !input.trim() &&
                  attachments.length === 0
                )
              }
            >
              {isLoading
                ? "Sending..."
                : "Send"}
            </button>
          </div>
        </form>
      </section>

      {/* =================================================
          Clinical Notice
      ================================================= */}

      <section
        className={
          styles.noticeCard
        }
        aria-label="Clinical notice"
      >
        <svg
          className={
            styles.noticeIcon
          }
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-hidden="true"
        >
          <circle
            cx="12"
            cy="12"
            r="9"
          />

          <path
            d="M12 8v5"
            strokeLinecap="round"
          />

          <path
            d="M12 16h.01"
            strokeLinecap="round"
          />
        </svg>

        <div>
          <p
            className={
              styles.noticeTitle
            }
          >
            Clinical Notice
          </p>

          <p
            className={
              styles.noticeText
            }
          >
            The AI assistant provides
            clinical decision support only.
            Final medical decisions must
            always be made by qualified
            healthcare professionals.
          </p>
        </div>
      </section>
    </div>
  );
}

export default ClinicalAssistant;