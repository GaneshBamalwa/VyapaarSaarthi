const { GoogleGenAI } = require("@google/genai");

const project = process.env.GOOGLE_CLOUD_PROJECT;
const location = process.env.GOOGLE_CLOUD_LOCATION || "us-central1";
const modelName = process.env.GEMINI_MODEL || "gemini-2.5-flash";

// WhatsApp (via Twilio) rejects message bodies longer than 1600 characters.
const MAX_REPLY_LENGTH = 1500;

const SYSTEM_INSTRUCTION =
  "You are VyapaarSaarthi, a friendly WhatsApp business assistant for small " +
  "Indian shopkeepers and traders. Help with orders, inventory, and customer " +
  "queries. Reply in the same language the user writes in (Hindi, English, or " +
  "Hinglish). Keep answers short and clear — this is a chat, not an essay. " +
  "IMPORTANT: DO NOT use markdown like **bold**. For bold text, use WhatsApp formatting which is *bold*. For italics use _italic_.";

// Lazily create the client so importing this module never throws before the
// app has validated configuration.
let ai;
function getClient() {
  if (!ai) {
    ai = new GoogleGenAI({ vertexai: true, project, location });
  }
  return ai;
}

// Sends a prompt to Gemini (via Vertex AI) and returns the plain text reply,
// trimmed to a length WhatsApp will accept.
async function generateReply(prompt) {
  const response = await getClient().models.generateContent({
    model: modelName,
    contents: prompt,
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      maxOutputTokens: 1024,
      temperature: 0.7,
    },
  });

  // `response.text` is empty when the response is blocked by safety filters or
  // the model returns no content.
  const text = (response.text || "").trim();
  if (!text) {
    return "Sorry, I could not generate a response. Please try rephrasing.";
  }

  return text.length > MAX_REPLY_LENGTH
    ? `${text.slice(0, MAX_REPLY_LENGTH - 1)}…`
    : text;
}

module.exports = { generateReply };
