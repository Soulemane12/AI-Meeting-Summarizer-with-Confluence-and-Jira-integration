# AI Meeting Summarizer

Effortlessly transcribe, summarize, and organize your meetings with the **AI Meeting Summarizer**. This tool integrates seamlessly with Confluence and Jira to centralize meeting insights and streamline task management.

---

## Features

- **Audio Transcription**: Converts meeting audio into text using AI-powered speech recognition.
- **Meeting Summarization**: Provides concise summaries of discussions.
- **Task Extraction**: Identifies actionable items and assigns them to team members.
- **Integration**:
  - Pushes meeting summaries to Confluence pages.
  - Creates Jira tasks for action items with due dates.
- **Task Management**: Enables filtering and assignment of tasks directly from the interface.

---

## Built With

- **Languages**: 
  - Python (Backend)
  - HTML, CSS, JavaScript (Frontend)
- **Frameworks**: Flask
- **APIs & Libraries**:
  - [Julep API](https://julep.ai) - For summarization (powered by GPT-4).
  - Google Speech-to-Text - For audio transcription.
  - Atlassian APIs - For Confluence and Jira integration.
- **Cloud Services**: AWS (Hosting and scalability).

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/meeting-summarizer.git
   cd meeting-summarizer
