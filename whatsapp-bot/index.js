require("dotenv").config();

const express = require("express");
const whatsappRouter = require("./src/routes/whatsapp");

// Fail fast if Vertex AI is not configured.
if (!process.env.GOOGLE_CLOUD_PROJECT) {
  console.error("GOOGLE_CLOUD_PROJECT is required. See .env.example.");
  process.exit(1);
}

const app = express();
const PORT = process.env.PORT || 3000;

// Trust the proxy (ngrok, Cloud Run, etc.) so req.protocol/host reflect the
// public HTTPS URL Twilio signed — required for webhook signature validation.
app.set("trust proxy", true);

// Twilio sends form-encoded payloads.
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "healthy" });
});

app.use("/api", whatsappRouter);

app.listen(PORT, () => {
  console.log(`WhatsApp bot listening on port ${PORT}`);
});
