# Employee Experience Agentic Assistant - PoC Design Spec


## 1. User experience specifications

**Summary**

Employee Experience Agent where the assistant helps the user complete a fixed number of actions enabled via tools.

**Conversational flow and UI behavior**

* Conversation is driven by the chat text box (Chainlit) where the user enters free text.
* The assistant maps the user query to one of the available tools and shows the associated action button.
* Provide two additional action buttons (maximum of 3 total) at the end of assistant responses for the user to execute tools and see results.
* The user is provided with a response text and up to 3 action buttons for each user input or tool execution.
* When a button is clicked it triggers one tool (sequential chaining is planned for later with user consent in the loop).
* The assistant only surfaces capabilities that correspond to the defined tool set.

**Behavior when no tool maps**

* **No mapping found:** default to a fixed set of tools with corresponding buttons and explain politely why the request cannot be handled. Also list supported actions.
* **Related but not exact:** ask clarifying questions. If the input still cannot be mapped after clarification, fall back to the “no mapping found” behavior.

**Post mapping**

* The agent shows the mapped action button and a short explanation of why the chosen tool is appropriate (highest confidence). It also mentions additional actions available via the other buttons (max 3).

---

## 2. Tool Registry (Local JSON)

| Tool                 | Description                                                                                                                       | Notes         |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| **profile_analyzer** | Analyzes the profile and provides a completion score based on missing or insufficient information.                                | Built (basic) |
| **update_profile**   | Helps update sections of the talent profile. Initial focus: skills section.                                                       | To implement  |
| **infer_skills**     | Suggests candidate skills from the profile and returns top and additional skills.                                                 | To implement  |
| **get_matches**      | One tool with arguments for modes: Vanilla, Filter, User input text (semantic). Returns top 3 matches with score and explanation. | To implement  |
| **ask_jd_qa**        | Q and A over a selected job posting.                                                                                              | To implement  |
| **draft_email**      | Drafts a message or note to a hiring manager or recruiter.                                                                        | To implement  |

> All tools except **profile_analyzer** are mocked for the PoC and marked for later implementation.

---

## 3. High-level architecture

### 3.1 Tool selection and conversational flow

* If the query maps to a tool, provide the corresponding action button.
* Provide up to two more actions (max 3 total). Ranking runs after intent mapping to prepare the top 3 buttons.
* Default ranking if needed: `get_matches → profile_analyzer → infer_skills → update_profile → ask_jd_qa → draft_email`.
* Show the mapped tool first, followed by the next two according to the default order or ranking.

**Flow**

```
User input (text) → Intent mapping → Next best actions selector → Response text → Show buttons (max 3)
User input (button) → Tool execution → Results → Response text (based on results) → Show next buttons
```

**Remediation for poor matches**

* If 2 consecutive get_matches sessions have average match score below 60 or the user taps “Not helpful” twice:

  * Run **profile_analyzer** and suggest profile updates. Focus the response on concrete updates based on the completion score and how they can improve matches.
  * Flow: condition detected → ask user if they want to improve the profile → explain that matching relies on the current profile and improving it may uncover better roles.

**Profile preconditions**

* Load the user profile at the beginning of the session and store it in Chainlit memory.
* If the profile is missing or completion score is below 50, do not show matches. Provide results of **profile_analyzer** and recommend the **update_profile** (skills) tool.
* **ask_jd_qa** is triggered after matches are shown. The user provides a job id via text to begin Q and A. Only the first step is mocked for now.

### 3.2 Context engineering

* Agent state has access to previous chats and actions within the same thread.

### 3.3 Code implementation guidelines

* Maintain separation of concerns.
* Make LLMs replaceable (GPT-4o vs GPT-5 etc.).
* Centralize prompts in `prompt.py`. The agent reads prompts from this module.

### 3.4 Confidence scoring and thresholds for intent mapping

* Ranking and confidence scoring are driven by the LLM module.
* Each tool mapping decision has a **confidence score (0 to 1)** from the LLM or ranking model.
* The agent selects the primary tool to display first.
* **Primary threshold (example 0.75):** strong match, proceed to execution copy.
* **Secondary range (example 0.45 to 0.75):** trigger clarifying questions. Show buttons, but the text response focuses on clarification. Remap after the answer. If still no tool is above the primary threshold, fall back.
* **Below 0.45:** fallback behavior — show default ranking of action buttons and inform the user that intent could not be mapped.
* Confidence also drives ordering of the top 3 buttons.
* Log scores and threshold outcomes for tuning.

### 3.5 Data flow between components

1. **User input:** free text or button click in Chainlit.
2. **Intent detection:** LLM parses input and identifies intent, mapping to a tool or to clarification.
3. **Tool mapping and context enrichment:** combine recent session data, prior actions, and relevant MyCareer data (profile, skills, preferences).
4. **Memory interaction:**

   * *Short-term:* recent inputs, actions, and results. Keep profile analyzer results to drive next best actions.
   * *Long-term:* past interactions and user-specific history for personalization.
5. **Tool execution:** selected tool runs and returns structured output (matches, analysis, messages).
6. **Response assembly:** LLM composes the message and next actions (max 3 buttons).
7. **User feedback loop:** selections update context and memory to maintain continuity.

### 3.6 Components

* **LLM layer capabilities:** intent detection, tool calling, routing to next best actions, response generation in text and buttons.
* **Session state management:** short-term context and MyCareer data (profile, preferences, metadata).
* **Tool registry:** local JSON registry of callable functions.
* **Resources:** JSON-based talent profile data.

---

## 4. Frontend

* Framework: Chainlit (Python) version 2.8.4

---

## 5. Backend

* Language: Python
* Agent framework: LangChain and LangGraph v1

  * `langchain==1.0.5`
  * `langgraph==1.0.3`
* Model: GPT-4o (tests planned with GPT-5 and GPT-4.1)

---

## 6. Memory management

### Short-term memory

* Chainlit and LangGraph session context
* Chat history of current thread

### Long-term memory

* Chat history (local SQLite)
* User history

---

## 7. Resources for tools (local files first)

* **talent-profile:** JSON file to be ported to Cosmos DB later
  Path: `data/sample_profile.json`
* **requisition:** JSON file to be ported to Cosmos DB later
  Path: `data/sample_job.json`

---

## 8. Feature prioritization

| Feature                                                                                                   | Complexity | Priority     | Triggers                                                       | Flow |
| --------------------------------------------------------------------------------------------------------- | ---------- | ------------ | -------------------------------------------------------------- | ---- |
| Show job matches based on the user's profile with AI explanation and match score (get_matches)            | Low        | Must have    |                                                                |      |
| Show job matches with user-provided filters (get_matches with filters)                                    | Medium     | Must have    |                                                                |      |
| Show job matches using user input text for semantic similarity (get_matches with text)                    | High       | Must have    |                                                                |      |
| Provide answers to clarifying questions against a job role                                                | Low        | Must have    |                                                                |      |
| Analyze profile for missing sections                                                                      | Low        | Must have    |                                                                |      |
| Analyze profile for insufficient sections (qualitative)                                                   | Medium     | Must have    |                                                                |      |
| Provide improvement suggestions (Experience, Qualifications, Affiliations, Career Aspirations, Languages) | Low        | Must have    |                                                                |      |
| Update skills (part of update_profile)                                                                    | Medium     | Must have    | Matches not good enough / skills missing / skills insufficient |      |
| Draft message based on job role (to HM or recruiter)                                                      | Medium     | Must have    |                                                                |      |
| Parse candidate input and map to available tools                                                          | High       | Must have    |                                                                |      |
| Ask clarifying questions if routing confidence is low                                                     | High       | Nice to have |                                                                |      |
| Suggest next action items via buttons on chat interface                                                   | Medium     | Must have    |                                                                |      |

---

## 9. Scope

* English language only
