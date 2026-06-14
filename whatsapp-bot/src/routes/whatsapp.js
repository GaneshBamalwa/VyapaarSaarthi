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

// Twilio posts inbound WhatsApp messages here as x-www-form-urlencoded.
router.post("/whatsapp", validateRequest, async (req, res) => {
  const twiml = new MessagingResponse();

  try {
    const incomingMessage = (req.body.Body || "").trim();

    if (!incomingMessage) {
      twiml.message("Please send a text message.");
    } else {
      const reply = await generateReply(incomingMessage);
      twiml.message(reply);
    }
  } catch (err) {
    console.error("Error handling WhatsApp message:", err);
    twiml.message("An error occurred while processing your request.");
  }

  res.type("text/xml").send(twiml.toString());
});

module.exports = router;
