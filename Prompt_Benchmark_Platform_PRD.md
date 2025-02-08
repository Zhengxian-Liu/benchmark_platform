# Prompt Benchmark Platform for LLM Translation Tasks

## 1. Overview

### 1.1. Product Description
The **Prompt Benchmark Platform for LLM Translation Tasks** is a tool designed to enable users—primarily internal team members working on localization—to experiment with various prompt versions and evaluate translation quality from AWS Bedrock’s Claude 3.5 Haiku. It provides an integrated workflow that includes prompt editing/versioning, LLM invocation, automated & human evaluations, and dynamic style guide integration. The system is built on a Gradio interface with a Python backend and uses PostgreSQL for persistent data storage.

### 1.2. Goals and Objectives
- **Prompt Experimentation & Management:**  
  - Allow creation, editing, and automatic versioning (per edit) of prompts.
  - Maintain a version history for each project and language combination.
- **LLM Translation Evaluation:**  
  - Integrate with AWS Bedrock (Claude 3.5 Haiku) for translation tasks.
  - Provide both overall and per-segment evaluation capabilities.
  - Capture automated quality metrics and enable human evaluation (with scoring and annotation fields).
- **Dynamic Style Guide Integration:**  
  - Allow users to upload an Excel-based style guide containing character attributes.
  - Enable users to provide an additional Excel file containing an “Extra” column.
  - Automatically detect matches between the “Extra” column and style guide data (using Chinese names) to substitute markup tags (e.g., `{name}`, `{gender}`) in the prompt with corresponding values.
- **Collaboration & Organization:**  
  - Organize experiments by projects and languages.
  - Each project/language combination is treated as a distinct experiment space.
  - Support multiple users working concurrently (each typically focused on a single language).
- **Local Prototyping:**  
  - Begin with a locally hosted solution for rapid prototyping and internal testing before scaling to cloud-based hosting.

### 1.3. Projects and Languages
The experiments are organized by the following projects and languages:

- **原神:** CHT, DE, EN, ES, FR, ID, IT, JA, KO, PT, RU, TR, VI  
- **RPG:** CHT, DE, EN, ES, FR, ID, JA, KO, PT, RU, VI  
- **NAP:** CHT, DE, EN, ES, FR, ID, JA, KO, PT, RU, VI  
- **崩3:** DE, EN, FR, ID, JP, KR, TH, VI  
- **NXX:** EN, JP, KR

---

## 2. Scope

### 2.1. Functional Requirements

#### 2.1.1. Prompt Management and Versioning
- **Prompt Editor:**  
  - A rich text editor (with syntax highlighting if needed) provided via Gradio.
  - Editing a prompt for a specific project-language combination automatically creates a new version.
- **Versioning Features:**  
  - Each edit triggers version creation with a timestamp and change log.
  - Ability to view the version history, compare (diff view), and rollback to previous versions.
  - Versioning is scoped per project per language (each project-language pair maintains its own history).

#### 2.1.2. Project and Language Organization
- **Predefined Projects and Languages:**  
  - The interface should allow the user to select one of the predefined projects and the associated languages.
- **User-Specific Focus:**  
  - While multiple users can access the platform, each user is primarily responsible for one language, though the system supports multi-user collaboration.

#### 2.1.3. LLM Integration via AWS Bedrock
- **Model Integration:**  
  - Utilize AWS Bedrock with the Claude 3.5 Haiku model for LLM-based translation.
  - Provide configurable model parameters (e.g., temperature, max tokens) on a per-call basis.
- **Invocation Process:**  
  - Support asynchronous API calls with progress indicators.
  - Log all requests/responses and handle error states gracefully.

#### 2.1.4. Evaluation Module
- **Automated Evaluation:**  
  - Integrate quality metrics (such as BLEU score or custom metrics focused on translation quality).
- **Human Evaluation:**  
  - Support both overall evaluation and optional per-segment evaluation.
  - Include numerical scoring and annotation/comment fields for detailed feedback.
- **Result Comparison:**  
  - Display side-by-side comparisons of translations from different prompt versions for the same project-language pair.

#### 2.1.5. Style Guide Integration
- **Style Guide Upload:**  
  - Provide a Gradio component to upload an Excel file serving as the style guide.
  - The style guide file must include an index column of Chinese names along with attributes (e.g., gender, speaking style).
- **Experiment Data Upload:**  
  - Allow users to upload an Excel file containing an “Extra” column.
- **Matching and Dynamic Replacement:**  
  - Automatically scan the “Extra” column for any Chinese name that matches an entry in the style guide.
  - For a matched character, replace prompt markup tags (e.g., `{name}`, `{gender}`) with the corresponding values from the style guide.
  - This dynamic substitution occurs before sending the prompt to AWS Bedrock.

#### 2.1.6. Data Persistence and Analytics
- **Database Requirements:**  
  - Use PostgreSQL (locally during initial development) to store:
    - Users
    - Projects & Languages
    - Prompts (with version history)
    - Experiment runs (including LLM outputs)
    - Evaluation results (automated and human)
    - Style guide data
- **Analytics Dashboard:**  
  - Provide visualizations and reports that track translation quality trends, version performance, and user feedback.
  - Filters to sort by project, language, prompt version, and evaluation metrics.

#### 2.1.7. User Management (Simplified)
- **Roles:**  
  - Admin, Evaluator, and Viewer (with a focus on internal, single-team use).
- **Authentication:**  
  - Minimal authentication (security is not a primary concern for internal, small-team use).

---

### 2.2. Non-Functional Requirements

#### 2.2.1. Usability and User Experience (UX/UI)
- **Agile and Intuitive Interface:**  
  - Utilize Gradio’s UI components to ensure a responsive, intuitive, and easy-to-navigate interface.
  - Ensure high usability even for users without technical backgrounds.

#### 2.2.2. Performance and Scalability
- **Local Development:**  
  - Initially hosted locally for rapid prototyping.
  - Ensure efficient handling of API calls and file uploads.
- **Future Scalability:**  
  - While the initial release is local, the architecture should allow for an easy transition to cloud-based hosting if required.

#### 2.2.3. Maintainability and Extensibility
- **Modular Code Design:**  
  - Structure the code to separate the frontend (Gradio) and backend (API, LLM integration, database interactions).
  - Provide comprehensive documentation to facilitate future enhancements and potential migration to different hosting environments.

---

## 3. System Architecture

### 3.1. High-Level Architecture Diagram
*(A diagram is recommended here to visualize the architecture; see attached diagram file if available.)*

- **Frontend:**  
  - **Gradio Interface:**  
    - Components include: Prompt Editor, Evaluation Panels, File Uploaders, Project & Language Selectors, Diff View, and Analytics Dashboard.
- **Backend:**  
  - **API Server:**  
    - Python-based server (FastAPI or Flask) managing REST API endpoints for prompt management, LLM calls, evaluation data, and file uploads.
  - **LLM Integration Module:**  
    - Service that handles asynchronous calls to AWS Bedrock (Claude 3.5 Haiku) and logs interactions.
  - **File Processing Module:**  
    - Handles parsing of uploaded Excel files (using Pandas) for style guide data and experiment “Extra” columns.
- **Database:**  
  - **PostgreSQL:**  
    - Stores all persistent data including prompts, version history, evaluation results, user data, and style guide tables.
- **Optional Exposure:**  
  - For testing, a tunneling service (e.g., ngrok) can be used to expose the local server to public URLs.

### 3.2. Data Flow and Interaction
1. **User Interaction:**
   - User selects a project and language.
   - User edits a prompt in the rich text editor. Each save triggers a new version stored in the DB.
2. **LLM Invocation:**
   - The current prompt is processed (including dynamic style guide tag replacement) and sent via an asynchronous API call to AWS Bedrock.
   - Translation outputs and any error logs are captured and stored.
3. **Evaluation Module:**
   - Automated metrics are calculated upon receiving the translation.
   - The interface displays translation outputs, allowing evaluators to add scores and annotations (both overall and per-segment).
4. **Style Guide Integration:**
   - On file upload, the system parses the Excel style guide.
   - When an experiment file with an “Extra” column is uploaded, the system matches entries to the style guide and dynamically replaces the prompt tags.
5. **Analytics:**
   - Data from prompt versions, LLM outputs, and evaluations are aggregated for visual dashboards and reporting.

---

## 4. Detailed Requirements Specification

### 4.1. Functional Modules

#### 4.1.1. Prompt Editor and Versioning  
- **Features:**  
  - Text editor for prompt input.  
  - Automatic versioning on each edit with a timestamp, change summary, and unique version ID.  
  - Diff view and rollback functionality.
- **Data Storage:**  
  - Database table for prompts containing:  
    - Project ID  
    - Language Code  
    - Prompt Text  
    - Version Number  
    - Timestamp  
    - Change Log/Metadata

#### 4.1.2. Experiment and Evaluation Module  
- **LLM Invocation:**  
  - Trigger API calls to AWS Bedrock using user-configured parameters.  
  - Support asynchronous processing with progress tracking.
- **Automated Evaluation:**  
  - Calculate translation quality metrics (e.g., BLEU, custom metrics).
- **Human Evaluation:**  
  - Form interface allowing evaluators to:  
    - Score the overall output (numeric or rubric-based).  
    - Optionally score individual segments.  
    - Provide annotations and comments for each segment or overall.
- **Result Comparison:**  
  - Display side-by-side comparisons of outputs from different prompt versions.
- **Data Storage:**  
  - Tables for Experiment Runs and Evaluation Results with fields for:  
    - Experiment ID  
    - Prompt Version ID  
    - Translation Output  
    - Automated Metrics  
    - Human Evaluation Scores and Annotations  
    - User ID, Timestamp, and Additional Metadata

#### 4.1.3. Style Guide Integration  
- **File Uploads:**  
  - Component to upload an Excel file containing the style guide data.  
  - Component to upload an Excel file for experiment data that includes an “Extra” column.
- **Data Parsing:**  
  - Use Pandas to parse and extract data from the Excel files.  
  - The style guide must have a unique Chinese name column (index) and additional attribute columns (gender, speaking style, etc.).
- **Dynamic Tag Replacement:**  
  - Scan the “Extra” column for Chinese names.  
  - For every detected name that matches the style guide, replace markup tags (e.g., `{name}`, `{gender}`) in the prompt with the corresponding values.
- **Data Storage:**  
  - Style guide table that stores all uploaded style guide entries and mappings.

#### 4.1.4. Analytics and Reporting  
- **Dashboard:**  
  - Visualizations (charts, tables) displaying trends in translation quality, prompt performance over time, and user evaluations.
- **Filtering:**  
  - Ability to filter data by project, language, prompt version, and evaluation scores.
- **Data Export:**  
  - Option to export reports for further analysis.

#### 4.1.5. User Management (Simplified)  
- **Roles:**  
  - Admin, Evaluator, Viewer  
- **Authentication:**  
  - Basic authentication mechanism sufficient for internal usage (potential for SSO in future if needed).

### 4.2. Non-Functional Specifications

- **Performance:**  
  - Low-latency processing for local use; asynchronous calls to manage longer API response times.
- **Scalability:**  
  - The local prototype should be designed with a modular architecture to facilitate migration to cloud hosting if necessary.
- **Usability:**  
  - An intuitive, agile interface built with Gradio.  
  - Clear, responsive UI for prompt editing, evaluation, and file uploads.
- **Maintainability:**  
  - Modular code structure with clear separation of concerns (frontend, API backend, LLM integration, file processing, database interactions).
- **Documentation:**  
  - In-code documentation and an overall architecture document to ease onboarding for future developers.

---

## 5. Technical Architecture

### 5.1. Frontend (Gradio)
- **Components:**  
  - **Prompt Editor:** Text area with versioning controls.
  - **Evaluation Panels:** Sections for overall and per-segment evaluations (score fields, annotation boxes).
  - **File Uploaders:** For style guide and experiment Excel files.
  - **Project/Language Selector:** Dropdown menus or tabs.
  - **Diff View:** For comparing prompt versions.
  - **Analytics Dashboard:** Graphs and tables for performance metrics.
- **Technology:**  
  - Gradio framework in Python, with custom components as needed.

### 5.2. Backend (API Server)
- **Framework:**  
  - Python (FastAPI or Flask recommended).
- **Modules:**  
  - **Prompt Management Module:** Handles creation, editing, and versioning.
  - **LLM Integration Module:** Interfaces with AWS Bedrock (Claude 3.5 Haiku) with asynchronous support.
  - **Evaluation Module:** Collects automated metrics and processes human evaluation inputs.
  - **File Processing Module:** Uses Pandas to parse Excel files for style guide and extra data.
  - **Database Interaction:** ORM (e.g., SQLAlchemy) for PostgreSQL interactions.
- **API Endpoints:**  
  - Endpoints for saving/retrieving prompt versions, triggering LLM calls, uploading files, and logging evaluations.

### 5.3. Database (PostgreSQL)
- **Schema:**  
  - **Users Table:** User ID, role, and minimal authentication info.
  - **Projects Table:** Project names and associated metadata.
  - **Languages Table:** Language codes and names.
  - **Prompts Table:** Prompt text, versioning info, project-language references.
  - **Experiment Runs Table:** LLM outputs, automated metrics, timestamps.
  - **Evaluation Results Table:** Overall and per-segment scores, annotations.
  - **Style Guide Table:** Parsed data from Excel uploads (Chinese name, gender, speaking style, etc.).

### 5.4. Deployment (Local Prototyping)
- **Local Environment Setup:**  
  - Develop and test on a local machine.
  - Use Docker (optional) for containerizing the application.
- **Optional Public Exposure:**  
  - Use tools like ngrok to expose the local instance for team testing.
- **Future Scalability:**  
  - Architecture designed to transition to cloud (AWS EC2, managed RDS for PostgreSQL) when required.

---

## 6. Milestones and Roadmap

### 6.1. Phase 1: Research & Prototyping
- Finalize detailed requirements.
- Set up the local development environment, including PostgreSQL and necessary Python libraries.
- Create a basic Gradio interface and integrate with a dummy API endpoint.

### 6.2. Phase 2: Core Feature Implementation
- **Prompt Management:**  
  - Implement prompt editor, versioning, and diff view.
- **LLM Integration:**  
  - Integrate AWS Bedrock (Claude 3.5 Haiku) for translation calls.
- **Evaluation Module:**  
  - Build both automated and human evaluation interfaces.
- **File Uploads and Processing:**  
  - Implement style guide and experiment file upload components.
  - Develop the dynamic tag replacement logic.

### 6.3. Phase 3: Testing and Iteration
- Thoroughly test each module individually (unit testing) and the system as a whole (integration testing).
- Gather internal team feedback and refine the UX/UI.
- Validate the style guide matching and prompt tag replacement functionalities.

### 6.4. Phase 4: Analytics and Reporting
- Develop the analytics dashboard with data visualization.
- Implement export and filtering functionalities.

### 6.5. Phase 5: Final Review and Documentation
- Finalize internal documentation and code comments.
- Prepare deployment scripts and configuration for local hosting.
- Optionally set up temporary public access for broader internal testing.

---

## 7. Deliverables and Handoff Requirements

- **Complete Codebase:**  
  - Modular code following the architectural separation described above.
- **Documentation:**  
  - Developer documentation, including API endpoint definitions, database schema, and setup instructions.
  - User documentation covering how to use the prompt editor, evaluation modules, and file uploads.
- **Test Cases:**  
  - Unit and integration test suites for each module.
- **Deployment Scripts:**  
  - Dockerfiles (if applicable) and instructions for local setup and optional public exposure.
- **Future Recommendations:**  
  - Notes on how to transition from local hosting to a cloud environment when scaling up.

---

## 8. Final Considerations

- **Agile Development:**  
  - Start with a minimal viable product (MVP) running locally.
  - Use iterative development cycles based on internal team feedback.
- **Extensibility:**  
  - The modular design will allow for the easy integration of additional LLMs or further enhancements to the evaluation and analytics components.
- **Collaboration:**  
  - Although initial usage is internal and local, the codebase and documentation will be structured to allow other developers to quickly understand and extend the system.

---

*This detailed PRD and requirements specification is intended to provide a clear, unambiguous blueprint for any developer or team tasked with implementing the Prompt Benchmark Platform. If further clarifications or adjustments are needed, please review and provide feedback before proceeding to the coding phase.*