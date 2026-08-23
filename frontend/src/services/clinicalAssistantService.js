import api from "./api";

// =========================================================
// Helpers
// =========================================================

const createChatFormData = ({
  message,
  conversationId = null,
  files = [],
}) => {
  const formData = new FormData();

  formData.append("message", message);

  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  files.forEach((file) => {
    formData.append("files", file);
  });

  return formData;
};

// =========================================================
// Start conversation
// =========================================================

export const startConversation = async (
  message,
  files = []
) => {
  const formData = createChatFormData({
    message,
    files,
  });

  const response = await api.post(
    "/clinical-assistant/",
    formData,
    {
      timeout: 120000,

      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};

// =========================================================
// Continue conversation
// =========================================================

export const continueConversation = async (
  conversationId,
  message,
  files = []
) => {
  const formData = createChatFormData({
    message,
    conversationId,
    files,
  });

  const response = await api.post(
    `/clinical-assistant/continue/${conversationId}`,
    formData,
    {
      timeout: 120000,

      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};

// =========================================================
// Get history
// =========================================================

export const getConversationHistory = async (
  conversationId
) => {
  const response = await api.get(
    `/clinical-assistant/history/${conversationId}`
  );

  return response.data;
};

// =========================================================
// Clear conversation
// =========================================================

export const clearConversationMemory = async (
  conversationId
) => {
  const response = await api.delete(
    `/clinical-assistant/conversation/${conversationId}/memory`
  );

  return response.data;
};

// =========================================================
// Delete conversation
// =========================================================

export const deleteConversation = async (
  conversationId
) => {
  const response = await api.delete(
    `/clinical-assistant/conversation/${conversationId}`
  );

  return response.data;
};

// =========================================================
// Health
// =========================================================

export const getClinicalAssistantHealth = async () => {
  const response = await api.get(
    "/clinical-assistant/health"
  );

  return response.data;
};

// =========================================================
// Upload clinical assistant attachments
// =========================================================

export const uploadAttachments = async (
  files
) => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await api.post(
    "/clinical-assistant/attachments",
    formData,
    {
      timeout: 120000,

      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};