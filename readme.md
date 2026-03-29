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

## 🎯 Advanced Features

### 1. Thematic Knowledge Bases (Divided Conceptual Foundation)

Each student has **two distinct knowledge domains** that allow them to debate on the same conceptual basis while holding different opinions:

- **TOPIC A (K-Value Strategy)**: How to choose the K parameter
  - Carlos believes K=1 is optimal (memorization as accuracy)
  - Ana believes K=1000 is optimal (flexibility as generalization)
  - Luis has no strong preference but recognizes KNN is non-parametric

- **TOPIC B (Evaluation Metrics)**: How to measure if the model is accurate
  - Carlos trusts training error (0% = perfect)
  - Ana trusts runtime performance (fast execution = good generalization)
  - Luis trusts a single metric (99.7% probability = perfect prediction)

This **divided-but-connected structure** enables:
- Students to disagree meaningfully about the same ML concepts
- The ability to build coherent arguments based on shared understanding

### 2. Chain of Thought (Internal vs. Public)

Each student generates a **two-part response** structured as:

```
[THOUGHT]
(Internal monologue: I analyze what was just said, check my beliefs, and decide if I should speak, and what to say)

[MESSAGE]
(Public response: What I actually say to the group, or [SILENCE] if I choose not to speak)
```

**Benefits of this approach:**
- **Transparency**: You can see the agent's reasoning process (internal thought) vs. what they communicate (public message)
- **Logical Consistency**: Students don't make random statements; they follow their personality and knowledge base
- **Self-Questioning**: Each thought analyzes contradictions and allows gradual perspective shifts
- **Realistic Simulation**: Agents can be internally conflicted or deliberately silent based on personality

The tutor and other students ONLY see the `[MESSAGE]` part, simulating real group dynamics where internal reasoning is private.

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

## 🎓 Tutor Intervention Systems

The simulator supports **two intervention strategies** (set in `main.py`):

### System B: Activity-Based (Recommended - Currently Tested ✓)
- Tutor intervenes when **complete group silence** occurs for 3+ minutes
- Tutor intervenes when **a single student** has been silent for 3+ minutes
- Uses **open-ended scaffolding questions** to restart discussion naturally
- Particularly effective at keeping passive students (Ana) engaged without intimidation

**Observed Improvements:**
- ✅ Better simulation quality when students have equal participation
- ✅ Tutor asks thought-provoking questions during silence
- ✅ Individual student inactivity is effectively addressed without directly calling them out
- ✅ More realistic group dynamics emerge with balanced contributions

### System A: Transactivity-Based (Experimental - Not Yet Tested ⚠️)
- Tutor intervenes when students fail to **synthesize or cross-reference** ideas
- Detects monologues vs. real debate (transactive discourse)
- Uses an additional LLM classifier to evaluate dialogue quality in real-time
- **Status**: Architecture complete but simulation results not yet verified

To switch systems, change `system_type` in `main.py`:
```python
system_type = "B"  # Use "A" for transactivity-based (experimental)
```

---

## 📈 Current Simulation Results

### What's Working Well
- **Student Diversity**: All three personas generate distinct, personality-consistent responses
- **Logical Arguments**: Students defend positions based on their thematic knowledge, not randomly
- **Internal Consistency**: Chain of Thought ensures decisions follow a logical line
- **Graceful Silence**: Students authentically decide NOT to speak based on personality (Ana's conflict avoidance, for example)
- **Tutor Quality**: System B interventions are contextually appropriate and encourage deeper thinking
- **Information Sharing**: Students genuinely listen and build on what others say

### Known Limitations
- ⚠️ **System A (Transactivity)** has not been tested in full simulation runs
- ⚠️ Some edge cases may cause unexpected [SILENCE] patterns (depends on LLM output quality)
- ⚠️ Tutor System A may require fine-tuning prompts for better responsiveness

### Research Challenge: Rapid Consensus Problem

**Current Issue**: Students reach consensus too quickly in most simulations.

The three students, while maintaining distinct identities, often **converge to similar conclusions within 2-3 exchanges**. This happens because:

1. **High Coherence**: The Chain of Thought mechanism ensures logical consistency, which can lead to acceptance of well-reasoned counterarguments too easily
2. **Limited Friction**: While students have strong initial positions, they may be too willing to acknowledge alternative viewpoints
3. **Cooperative Nature**: The underlying goal of each agent is to participate in learning, not to "win" the debate

**Why This Matters for Tutor Evaluation**:
- With rapid consensus, the tutor never faces **prolonged disagreement** scenarios
- System B (Activity-based) tutor is designed for **silence/inactivity**, not for **unproductive debate**
- System A (Transactivity) tutor would benefit from scenarios where students stubbornly repeat ideas without synthesis
- We cannot properly evaluate how well tutors handle **conflict resolution, contradictory evidence, or strong resistance to new ideas**


This challenge is essential for future research: **we need more diverse and contentious scenarios to properly benchmark the tutor's pedagogical effectiveness.**

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