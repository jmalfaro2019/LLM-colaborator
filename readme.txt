# 🤖 PBL (Problem-Based Learning) Discussion Simulator

## 📋 What is this?

This project simulates a **group discussion among 3 AI students** with different personalities and opinions on a machine learning problem. The goal is to see how they debate, argue, and reach conclusions about how to configure a K-Nearest Neighbors (KNN) algorithm to diagnose diseases.

### 🎓 The 3 students:

1. **Carlos** (Dominant)
   - Confident and decisive
   - Believes that K should be very small (K=1)
   - Believes that the training error is evidence of accuracy
   - Defends his ideas with confidence

2. **Ana** (Passive)
   - Insecure and avoids conflict
   - Believes that K should be very large (K=1000)
   - Believes that the algorithm’s speed demonstrates good generalization
   - Uses hesitant but direct language

3. **Luis** (Reflective)
   - Analytical and a mediator
   - Has no strong opinion about K
   - Believes that a 99.7% accuracy rate is definitive proof of accuracy
   - Builds on the ideas of others

### 👨‍🏫 The Tutor (Automatic)

The tutor intervenes automatically in two situations:
- **If everyone remains silent** for more than 3 minutes → asks about the learning approach
- **If a student does not participate** for more than 3 minutes → invites them to participate

---

## 📁 Project Structure

```
├── main.py                    # Main file (entry point)
├── pbl_config.py             # Configuration: scenarios and prompts for each student
├── pbl_simulator.py          # Simulation logic: how the discussion works
├── simulated_student.py      # Student class (connects to AI)
├── simulated_tutor.py        # Tutor class (connects to AI)
├── requirements.txt          # Required dependencies
└── .env                      # Private configuration (API key)
```

### What each file does:
- **main.py**: Creates the 3 students and starts the simulation
- **pbl_config.py**: Defines what each student knows, their personalities, and the problem
- **pbl_simulator.py**: Handles the logic of turns, interventions, and silence
- **simulated_student.py** and **simulated_tutor.py**: Communicate with the AI (Groq API)

---

## ⚙️ How the simulation works

1. **The tutor poses the problem** → “Team, we’ll use KNN. What should K be? How do we prove the model isn’t overfitted?”

2. **Every minute (tick)**:
   - Carlos gives his opinion
   - Ana gives her opinion
   - Luis gives his opinion
   - If someone doesn’t want to speak, they type [SILENCE]

3. **Everyone listens**: When one person speaks, the others see what they said

4. **The tutor intervenes if necessary**: If there is too much silence or someone isn’t participating

5. **Repeat** for up to 6 minutes (rounds)

---

## 🚀 How to run

### Prerequisites

- Python 3.8 or higher
- An account on [Groq Console](https://console.groq.com/) (free)

### Step 1: Set up the environment

```bash
# Activate the virtual environment (navigate to the project folder first)
env\Scripts\activate.ps1
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure the API Key

1. Go to https://console.groq.com/
2. Create an account or log in
3. Go to “API Keys” and copy your key
4. Create a `.env` file in the project's root folder
5. Add the line:
   ```
   GROQ_API_KEY=your_key_here
   ```

### Step 4: Run

```bash
python main.py
```

---

## 📊 What you'll see in the output

```
[Tick 0] Tutor: Team, we will use KNN to diagnose the patients...

--- Minute 1 ---
Carlos says: I think we should use a very small K...
Ana says: I think a huge K...
Luis says: I think a medium K...

--- Minute 2 ---
...
```

You’ll see how the students debate, change their minds, and apply what others say. It’s just like a real AI working group!

---

## 🔧 To modify

- **Change the problem**: Edit `pbl_config.py` → `PBL_SCENARIO`
- **Change student opinions**: Edit `pbl_config.py` → `KNOWLEDGE_*`
- **Change personalities**: Edit `pbl_config.py` → `PROMPT_*`
- **Change simulation duration**: Edit `pbl_config.py` → `MAX_TICKS`
- **Change how the tutor intervenes**: Edit `pbl_simulator.py` → intervention methods

---