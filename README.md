John Jedric G. Alipat

Harvey A. Jain

Jose Rey Grandea

No initial design of database 70 Points 10/7/2026



Farm Pulse BSIT-3A Class Project Concept Paper

Formatting & Submission Guidelines Reminder
•	Paper Size: Letter (8.5'' \times 11'')
•	Font Style & Size: Times New Roman, 12 pt
•	Line Spacing: Double-spaced
•	Margins: Left: 1.5'' (for binding); Top, Right, Bottom: 1.0''
•	Paragraph Indentation: First-line indent by 0.5''
•	Tense: Future tense for proposed systems, tasks, and features
•	Scope Exclusion: Do NOT include results, conclusions, recommendations, or an abstract.

DEVELOPMENT OF FARMPULSE: AN INTELLIGENT WEB-BASED 
CROP MONITORING AND FARM MANAGEMENT SYSTEM 
WITH AI-POWERED DISEASE DIAGNOSIS
BSIT Capstone Project Concept Paper


INTRODUCTION

Background of the Project
Agriculture remains a vital cornerstone of socioeconomic stability and food production. However, smallholder farmers, local farm cooperatives, and agricultural managers frequently struggle with fragmented farm record-keeping and delayed response times to crop pests and diseases. In traditional farm operations, field inspections, irrigation schedules, fertilizer applications, and crop health observations are either documented in physical notebooks or managed entirely through memory. This conventional approach leads to misplaced field records, difficulty tracking historical disease patterns, inadequate crop lifecycle oversight, and substantial yield loss due to late-stage pathology detection.
Furthermore, when crop foliage shows symptoms of infection (such as leaf discoloration, blight, or pest infestation), farmers often lack immediate access to certified agronomists or plant pathologists. Misidentifying plant diseases frequently results in the incorrect application of agrochemicals, escalated operational costs, and environmental contamination. 
To resolve these operational challenges, the proposed project will focus on the design and development of Farm Pulse, a centralized, web-based crop health monitoring and farm management system with integrated artificial intelligence (AI) diagnostic capabilities. The web platform will digitize crop registry profiles, automate daily field activity logging, calculate real-time farm health performance indicators, and utilize Google Gemini AI models to deliver instant, crop-specific disease diagnoses and treatment action plans. By bridging agricultural operations with modern web and artificial intelligence technologies, Farm Pulse will provide an accessible, transparent, and data-driven farming management solution.

Statement of the Problem or Project Objectives
The primary objective of this project is to design, develop, and evaluate Farm Pulse: A Web-Based Crop Monitoring and Farm Management System with AI-Powered Disease Diagnosis to streamline farm record administration, track crop conditions, and accelerate agricultural pathology identification.



Specifically, the project aims to accomplish the following technical objectives:

1. Design and implement a secure user and role management module incorporating role-based access control (Superuser/Administrator, Staff, and Farm User), credential authentication, account lockouts for failed logins, and administrative password management.
2. Develop a centralized crop profile and field registry module that records crop names, specific varieties/cultivars, field locations or greenhouse zones, health status indicators (Healthy, Minor Warning, Unhealthy), and initial observation notes.
3. Build an interactive farm activity and field log subsystem allowing farmers and agricultural technicians to record daily maintenance tasks (e.g., field inspections, irrigation, pest control, fertilization) alongside observed plant conditions and date stamps.
4. Integrate an AI-assisted crop pathology diagnosis engine utilizing the Google Gemini API to analyze observed leaf, stalk, and soil symptoms, producing structured disease titles, immediate organic/cultural action plans, and preventative measures locked strictly to the specific crop variety. And provides photo captures for the AI to recognize so that it can help Identify easily.
5. Construct an interactive analytics dashboard that calculates real-time key performance indicators (KPIs), health distribution ratios, recent field activity feeds, determining kilogram crops estimated when harvested, and diagnostic history summaries.
6. Conduct user acceptance testing (UAT) with local farmers, agriculture students, and IT specialists to evaluate the platform’s usability, functionality, and performance based on ISO/IEC 25010 software quality standards.



Significance of the Project
The proposed system will provide substantial practical value and direct benefits to the following stakeholders:

•	Smallholder Farmers and Farm Technicians: Provides an easy-to-use digital tool to log daily fieldwork, track crop growth across multiple plots, and receive rapid, actionable disease treatment guidance without expensive consulting fees.
•	Farm Owners and Agricultural Managers: Delivers operational transparency and real-time dashboard analytics, enabling proactive resource management, crop health monitoring, and reduced crop mortality rates.
•	Agricultural Cooperatives and Extension Workers: Serves as a digital registry to audit seasonal crop yields, assess prevailing regional plant diseases, and coordinate data-backed agricultural assistance.
•	Environmental and Public Health Advocates: Minimizes indiscriminate chemical pesticide usage by offering precise, targeted organic and field-level remediation practices.
•	Future Researchers and IT Students: Provides an architectural and empirical reference for integrating generative AI technologies with web frameworks in smart agriculture and precision farming solutions.

Alignment with Institutional Research Agenda and Sustainable Development Goals

•	Institutional Research Agenda Alignment: 
  The proposed project aligns directly with the Institutional Research Agenda on Agricultural Informatics, Technological Innovation, and Sustainable Development by leveraging software engineering and generative AI to modernize rural farming operations and support data-driven decision-making.

•	Sustainable Development Goals (SDGs) Alignment:
    o	SDG 2 (Zero Hunger): Supports target 2.4 by promoting resilient and sustainable agricultural practices, mitigating crop loss through early pathology detection, and boosting agricultural productivity.
    o	SDG 9 (Industry, Innovation, and Infrastructure): Fosters technological innovation within rural and small-scale agricultural infrastructures through digital software transformation.
    o	SDG 12 (Responsible Consumption and Production): Encourages sustainable pesticide and fertilizer application through tailored treatment plans, preventing chemical runoff and soil degradation.



SCOPE AND LIMITATIONS
System Scope & Technical Architecture

Component & Description and Coverage

Core Modules

1. Authentication & Security: User registration, credential login with rate-limiting lockouts, session handling, and role-based permissions.
2. User Administration: Administrative CRUD, role toggles (Superuser/Staff/User), account status controls (Active/Inactive), and password resets.
3. Crop & Field Registry: Management of crop varieties, plot locations, categorized status indicators, and baseline observations.
4. Daily Activity & Field Logging: Recording of field inspections, watering, and fertilization tasks linked to specific crops.
5. AI Diagnosis & Treatment Engine: Generative AI-driven diagnosis module powered by Gemini API, crop-locked to prevent cross-crop hallucinations, providing immediate actions and preventative measures.
6. Farm Pulse Analytics Dashboard: Real-time health distribution metrics, progress indicators, recent activity logs, and diagnosis feeds.

Technology Stack

Backend: Python, Django Web Framework (Model-View-Template architecture, ORM).
Database: MySQL Relational Database Management System.
AI Integration: Google Gemini API (gemini-flash-lite-latest / REST HTTP fallback).
Frontend: HTML5, CSS3, JavaScript (Fetch API / Asynchronous AJAX), Tabler UI, Bootstrap 5, Font Awesome Icons.

Target Users

Farm Owners, Agricultural Field Workers, Farm Technicians, and System Administrators.



Limitations
•	The system is designed as a web application accessible via desktop and mobile web browsers over local intranet or hosted web server environments; it will not function as an installable standalone native mobile APK.
•	The AI diagnostic module relies on textual symptom descriptions submitted by users; automated computer vision image segmentation directly from live camera streams is excluded from this development phase.
•	The system provides advisory recommendations and treatment plans; it does not directly control physical IoT hardware, robotic sprayers, or automated drip-valve controllers.
•	Real-time weather forecasting APIs and external financial marketplace integrations are excluded from the current phase and are reserved for future enhancement phases.

