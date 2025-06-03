# AI Transcriber & Conversation Analyzer for Kommo CRM

## Project Overview

This AI-powered solution integrates with **Kommo CRM** to automate the processing and analysis of phone calls between managers and clients. After each call, the system receives call metadata and the audio file, transcribes the conversation using **OpenAI Whisper**, and analyzes it using **OpenAI Assistant**.

Prompts for the AI analysis are fully configurable via an admin panel, and the final conversation summary is sent back to the CRM — directly into the lead's profile.

---

## 🔍 Features

- Automatic transcription of call audio
- AI-driven analysis of conversation content
- Configurable prompts via admin panel
- Integration with Kommo CRM via webhooks
- Asynchronous background processing with Celery

---

## Tech Stack

- **Python 3.11**
- **Flask** — API server and admin interface
- **Celery + Redis** — background task processing
- **OpenAI Whisper & Assistant API** — transcription and conversation analysis
- **Kommo CRM** — external integration for leads and webhooks
- **SQLAlchemy** — ORM
- **Flask-Admin** — admin panel for prompts, users, integrations

---

## Workflow

1.  A manager makes a call via Kommo CRM.
2.  The CRM sends a webhook with metadata and audio URL.
3.  The audio is downloaded and transcribed with OpenAI Whisper.
4.  The transcript is analyzed by OpenAI Assistant using a dynamic prompt.
5.  The summarized insights are pushed back into the CRM as a note.

---