This project addresses the challenge of making history and science engaging through interactive quizzes. Unlike many quizzes, it is enhanced with a chatbot that allows learners to ask questions and receive instant explanations. 

# Project Overview / Purpose
  
EduTrivia is an interactive educational platform designed to make learning history and science engaging. It combines multiple-choice quizzes with a chatbot that answers questions in real time, allowing learners to explore content, verify facts, and gain deeper understanding beyond standard quizzes.

# Modules / Content
It includes the following modules, covering key events, figures, and discoveries, with unique questions that contain historical context, as well as critical thinking questions:

- French Revolution Quiz – Beginner (8 min) – History
- American Revolution Quiz – Beginner (8 min) – History
- Cal State LA History Quiz – Beginner (10 min) – Local History
- Joseon Dynasty Quiz – Beginner (8 min) – History
- Isaac Newton & Scientific Revolution Quiz – Beginner (10 min) – History

Unlike most quizzes, the chatbot component encourages curiosity, supports deeper understanding, and makes learning both personalized and interactive.

# Features / Highlights
This application has the following features:
1. Chatbot for instant Q&A about any quiz topic
2. Multiple-choice questions
3. Curated sources for each question to encourage further learning once you complete a question, as well as explanation on what the answer is and why it is the correct solution, as well as whether you got the question right or wrong.
4. Beginner-friendly with estimated completion times for each module

# Installation / Usage

### Running Locally
1. Clone the repository:
   ```
   bash
   git clone https://github.com/theirenechen12/ai-hackathon.git
   cd ai-hackathon
   ```

2.	Install dependencies:

```
pip install -r backend/requirements.txt
```

3.	Run a virtual environment in the home folder.

```
source venv/bin/activate

```

4. Run the Python file to start the application in the virtual environment:

```
cd ../Playwright
python main.py
```

5. Also run
```
cd backend
uvicorn app.main:app --reload --port 8000
```
To refresh as needed.
