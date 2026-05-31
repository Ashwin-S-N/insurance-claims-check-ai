# Demo Script

1. Start the backend and frontend.
2. Load `Early stop` in the UI and submit. Show the specific missing `HOSPITAL_BILL` message.
3. Load `Approval` and submit. Show approved amount INR 1,350 and trace events for verification, extraction, policy, fraud, and decision.
4. Load `Fraud review` and submit. Show same-day claim signal and `MANUAL_REVIEW`.
5. Technical decision to highlight: policy and fraud are deterministic and traceable; Gemini is isolated as an optional extraction adapter.
6. What to change with more time: add production OCR/PDF parsing and asynchronous document processing.
