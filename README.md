# KANUN – RAG-Based Application for the Constitution of Nepal

KANUN is a final-year academic project designed to make the Constitution of Nepal more accessible through an AI-powered question-answering system. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant constitutional information and generate context-aware responses to users' queries.

## 📌 Project Overview

Legal documents can be lengthy and difficult to navigate. KANUN aims to simplify access to constitutional information by allowing users to ask questions in natural language and receive responses based on relevant constitutional provisions.

## ✨ Key Features

- **AI-Powered Question Answering:** Ask questions about the Constitution of Nepal in natural language.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant constitutional content to provide context for generated answers.
- **Semantic Search:** Identifies relevant constitutional passages based on the meaning of a query.
- **Role-Based Access Control:** Supports Normal User, Staff, and Super Admin roles.
- **Usage Tracking:** Maintains chat usage logs for monitoring application activity.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Language Model Integration | LangChain |
| Large Language Model | OpenAI GPT-4o mini |
| Vector Database | Qdrant |
| Frontend | HTML, CSS, JavaScript, SB Admin template |
| Retrieval Method | Vector similarity search |

## 🧠 How It Works

1. **User Query:** The user submits a question about the Constitution of Nepal.
2. **Retrieval:** The application searches the vector database for relevant constitutional passages.
3. **Context Construction:** Retrieved passages provide context for the language model.
4. **Response Generation:** The model generates a response based on the retrieved information.
5. **Display:** The answer is presented to the user through the application interface.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or a compatible version
- pip
- Access to an OpenAI API key
- A Qdrant instance or compatible vector database configuration

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Abhinab433/Final-Year-Project.git
cd Final-Year-Project
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

**3. Install dependencies**

If the repository includes a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Configure the required API keys and database settings according to the application's configuration. Keep secret keys out of source control.

**5. Apply database migrations**

```bash
python manage.py migrate
```

**6. Start the development server**

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

*Note: These setup commands assume the repository contains a standard Django project. The exact dependency installation, environment variables, Qdrant configuration, and startup steps may differ depending on the project files.*

## 🎯 Project Objectives

- Improve access to constitutional information through natural-language interaction.
- Explore the practical integration of large language models with retrieval systems.
- Apply semantic search and vector databases to document-based question answering.
- Develop a web application with authentication and role-based access control.

## ⚠️ Disclaimer

KANUN is an academic project intended to support access to constitutional information. Generated responses may be incomplete or inaccurate and should be verified against the official Constitution of Nepal. The application does not replace professional legal advice.

## 👨‍💻 Author

**Abhinab Shrestha**

- GitHub: [@Abhinab433](https://github.com/Abhinab433)
- Project Repository: [Final-Year-Project](https://github.com/Abhinab433/Final-Year-Project)

---

Developed as a final-year project for the B.Sc. CSIT program.
