const express = require("express");
const twilio = require("twilio");
const { generateReply } = require("../services/vertexAI");

const router = express.Router();
const { MessagingResponse } = twilio.twiml;

// Validate the X-Twilio-Signature so only Twilio can invoke the webhook.
// When TWILIO_AUTH_TOKEN is unset (e.g. local testing) validation is skipped
// with a warning rather than rejecting every request.
const authToken = process.env.TWILIO_AUTH_TOKEN;
const validateRequest = authToken
  ? twilio.webhook({ authToken })
  : (req, _res, next) => {
      console.warn("TWILIO_AUTH_TOKEN not set — skipping signature validation.");
      next();
    };

// Clean WhatsApp phone number from Twilio (From: 'whatsapp:+919876543210')
function extractPhone(from) {
  if (!from) return "unknown";
  return from.replace("whatsapp:", "").trim();
}

// Format the backend response to WhatsApp markup
function formatBackendResponse(data) {
  if (!data.success) {
    return `❌ ${data.message}`;
  }
  if (data.data && data.data.orders) {
    const orders = data.data.orders;
    if (!orders.length) return "No orders found.";
    let lines = [`📊 *${data.message}*`];
    for (const o of orders) {
      lines.push(`• *ORD-${o.id}* | ${o.customer} | ${o.status} | ${o.date}`);
    }
    return lines.join("\n");
  }
  if (data.data && data.data.order_id) {
    return `✅ *Success*\n${data.message}`;
  }
  return `✅ ${data.message}`;
}

// Twilio posts inbound WhatsApp messages here as x-www-form-urlencoded.
router.post("/whatsapp", validateRequest, async (req, res) => {
  const twiml = new MessagingResponse();

  try {
    const incomingMessage = (req.body.Body || "").trim();
    const sender = extractPhone(req.body.From);

    if (!incomingMessage) {
      twiml.message("Please send a text message.");
    } else {
      let backendHandled = false;
      try {
        const backendRes = await fetch("http://127.0.0.1:8000/api/communication/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message_text: incomingMessage,
            user_id: sender,
            channel: "whatsapp",
            phone_number: sender
          })
        });

        if (backendRes.ok) {
          const data = await backendRes.json();
          // If the backend processed an intent (not fallback), use its response
          if (data.intent !== "unknown" && data.intent !== "fallback") {
            const reply = formatBackendResponse(data);
            twiml.message(reply);
            backendHandled = true;
          }
        }
      } catch (err) {
        console.error("Backend unreachable or error, falling back to LLM", err.message);
      }

      if (!backendHandled) {
        const reply = await generateReply(incomingMessage);
        twiml.message(reply);
      }
    }
  } catch (err) {
    console.error("Error handling WhatsApp message:", err);
    twiml.message("An error occurred while processing your request.");
  }

  res.type("text/xml").send(twiml.toString());
});

module.exports = router;
