# AI-Powered Financial Fraud Detection System

### A Neo4j-Based Banking Management and Intelligent Fraud Detection Application

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/Neo4j-Graph%20Database-blue?logo=neo4j" />
  <img src="https://img.shields.io/badge/Cypher-Query%20Language-orange" />
</p>

**GitHub Repository:**  
https://github.com/Vinodd07/FINANCIAL-FRAUD-DETECTION_DBMS_PROJECT

**Project Demonstration Video:**  
[Watch the complete project demonstration on YouTube](https://youtu.be/uDMpE0RNGts)

---

## 1. Project Overview

The **AI-Powered Financial Fraud Detection System** is a graph-based banking application designed to demonstrate secure banking operations, role-based access control and intelligent financial fraud detection.

The application allows customers to register, manage bank accounts, deposit virtual money, add beneficiaries and transfer funds. Alongside normal banking operations, the system monitors transactions and identifies suspicious activities using transaction behaviour, device information, IP addresses and graph-based relationships.

The project uses **Neo4j Graph Database** to represent customers, accounts, employees, devices, transactions and fraud cases as interconnected nodes and relationships.

A risk-scoring mechanism evaluates each transaction and determines whether it should be approved, sent for OTP verification or blocked.

## 2. Problem Statement

Financial fraud can occur through unusual transactions, unauthorised devices, suspicious IP addresses, recently added beneficiaries and abnormal transaction patterns.

Conventional transaction monitoring approaches may not effectively identify complex relationships between customers, accounts, devices and transactions.

This project addresses these challenges through a graph-based banking system that analyses interconnected banking information, evaluates suspicious activities and assigns risk scores to transactions.

## 3. Project Objectives

- Develop a banking application with multiple user roles and access permissions.
- Implement customer and employee management.
- Store banking information using Neo4j Graph Database.
- Establish relationships between customers, accounts, transactions, devices and IP addresses.
- Analyse transaction behaviour and calculate fraud risk scores.
- Identify suspicious login and transaction activities.
- Maintain fraud cases, audit records and transaction histories.
- Demonstrate graph database concepts through Cypher queries.

## 4. Key Features

### Banking Operations

- Customer registration and login.
- Account creation and balance management.
- Virtual money deposits.
- Beneficiary registration and management.
- Money transfers between accounts.
- Transaction history and account information.
- Simulated OTP verification for selected transactions.

### Fraud Detection

The application evaluates multiple fraud indicators:

- Login from a new or unrecognised device.
- Login from a new IP address.
- Unusually large transaction amounts.
- Transactions significantly higher than normal customer behaviour.
- Transfers involving a large proportion of the available account balance.
- Recently added beneficiaries.
- Transactions performed during unusual hours.
- Multiple rapid transactions.
- Shared devices across different users.
- Beneficiaries receiving money from multiple senders.

### Risk-Based Transaction Decisions

The system calculates a fraud risk score and classifies transactions into three categories:

- **Low Risk:** Transaction is approved.
- **Medium Risk:** Transaction requires OTP verification.
- **High Risk:** Transaction is blocked.

Configured risk thresholds:

- Risk score below 35: `SUCCESS`
- Risk score from 35 to below 70: `PENDING_OTP`
- Risk score of 70 or above: `BLOCKED`

### Automatic Device and Login Tracking

The application automatically collects login-related information, including:

- IP address.
- Browser information.
- Operating system.
- Device fingerprint.
- Login timestamp.
- New device detection.
- New IP detection.
- Shared device information.

This information contributes to the transaction fraud analysis process.

### Audit and Fraud Case Management

- Fraud cases are recorded for suspicious transactions.
- Fraud factors and their associated risk points are stored.
- Fraud analysts can investigate suspicious activities.
- Login and transaction activities are maintained for monitoring.
- Audit logs record relevant system operations.

## 5. User Roles and Permissions

The application supports six different roles with role-based access permissions.

### ADMIN

- Access the overall banking management system.
- View customers, employees and accounts.
- Create and manage employees.
- Monitor transactions and fraud cases.
- Manage system-level operations.
- Access audit and monitoring information.

### MANAGER

- Monitor branch-level banking operations.
- View relevant customers and employees.
- Review transactions.
- Monitor suspicious activities.
- Manage and review assigned fraud cases.

### TELLER

- Perform supported branch-level banking operations.
- Assist customers with banking services.
- Handle supported deposit operations.

### FRAUD ANALYST

- Review suspicious transactions.
- Investigate flagged fraud cases.
- Analyse fraud risk scores and risk factors.
- Examine device and IP-related activities.
- Update fraud investigation status where permitted.

### SUPPORT

- View relevant customer information.
- Handle customer support requests.
- Review complaints and support tickets.
- Add support notes and update ticket status where permitted.

### CUSTOMER

- Register and log in.
- View personal account information.
- Check account balance.
- Make virtual deposits.
- Add and manage beneficiaries.
- Transfer money.
- View transaction history.
- Complete simulated OTP verification when required.
- View personal login and security information.

## 6. Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn
- Neo4j Python Driver

### Frontend

- HTML
- CSS
- JavaScript

### Database

- Neo4j Graph Database
- Cypher Query Language

### Fraud Detection

- Python-based risk scoring mechanism.
- Sigmoid-based fraud risk score calculation.
- Device and IP address tracking.
- Transaction behaviour analysis.
- Graph relationship analysis.
- Rule-based transaction risk classification.

## 7. Database Design

The project uses **Neo4j Graph Database** instead of a traditional relational database.

Neo4j represents information through nodes, relationships, properties and labels.

- **Nodes:** Represent entities such as customers, accounts, employees and transactions.
- **Relationships:** Represent connections between entities.
- **Properties:** Store information associated with nodes and relationships.
- **Labels:** Identify the type of each node.

### Main Node Labels

The database contains the following 23 node labels:

1. Customer
2. Account
3. Employee
4. Role
5. Branch
6. Department
7. Beneficiary
8. Transaction
9. FraudCase
10. FraudFactor
11. Device
12. IPAddress
13. Login
14. Session
15. AuditLog
16. SupportTicket
17. Complaint
18. Notification
19. BankCard
20. Loan
21. OTPChallenge
22. BankPolicy
23. IdCounter

### Main Relationship Types

The database contains the following 20 relationship types:

- OWNS
- SENT
- RECEIVED_BY
- HAS_ROLE
- AT_BRANCH
- IN_DEPARTMENT
- HAS_BENEFICIARY
- REGISTERED_BENEFICIARY
- POINTS_TO
- LOGGED_IN
- FROM_DEVICE
- FROM_IP
- HAS_SESSION
- FOR_LOGIN
- MADE_IN
- FLAGGED_AS
- HAS_FACTOR
- RAISED
- ASSIGNED_TO
- USES

### Database Constraints

Neo4j uniqueness constraints are implemented to maintain data integrity.

Examples include:

- Unique customer IDs and email addresses.
- Unique account IDs and account numbers.
- Unique employee IDs.
- Unique transaction IDs.
- Unique branch IFSC codes and branch IDs.
- Unique device hashes and IP addresses.
- Unique fraud case IDs.
- Unique beneficiary IDs.
- Unique role names.

The `schema.cypher` file contains the database constraints. Nodes and relationships are created through the application during banking operations and through the optional sample-data script.

## 8. Fraud Detection Workflow

The transaction monitoring process follows these steps:

1. The customer initiates a money transfer.
2. The application retrieves sender and receiver account details.
3. Login and transaction-related information is collected.
4. Transaction behaviour is analysed using configured fraud indicators.
5. Device, IP and graph-based information is examined.
6. A fraud risk score is calculated.
7. The transaction is classified based on the configured thresholds.
8. The transaction is approved, sent for OTP verification or blocked.
9. Fraud factors and related fraud cases are recorded in Neo4j.

### Risk Score Calculation

The application combines the points assigned to individual fraud indicators.

The resulting score is calculated using a sigmoid function:

`Risk Score = 100 / (1 + e^(-z))`

Where `z` is calculated using a base value and the sum of the detected fraud-factor points.

The final score is expressed as a value between 0 and 100.

### Transaction Decision

- Below 35: Transaction approved.
- 35 to below 70: OTP verification required.
- 70 and above: Transaction blocked.

For OTP-required transactions, the application uses a simulated OTP mechanism. Actual SMS delivery is not implemented.

## 9. Project Architecture

The application follows a client-server architecture.

**Frontend → FastAPI Backend → Fraud Detection Logic → Neo4j Database**

- **Frontend:** Provides the banking interface and user interactions.
- **FastAPI Backend:** Handles authentication, API requests, banking operations and role-based access.
- **Fraud Detection Logic:** Analyses transaction behaviour, device information, IP addresses and graph relationships.
- **Neo4j Database:** Stores banking entities, relationships, transactions, fraud cases and audit records.
- **Cypher:** Used to retrieve, create and analyse connected graph data.

## 10. Database Design Approach

The project follows a graph-based database design.

Unlike relational databases that organise data into tables, Neo4j stores entities as nodes and their connections as relationships.

The database design focuses on:

- Entity representation using labelled nodes.
- Relationship-based connections between customers, accounts and transactions.
- Uniqueness constraints to maintain data integrity.
- Cypher queries for retrieving and analysing graph data.
- Connected device and IP relationships for suspicious activity analysis.
- FraudCase and FraudFactor nodes for maintaining investigation details.

The application creates and updates database nodes and relationships through its FastAPI backend.

## 11. Repository Structure

The project is organised into the following structure:

```text
FINANCIAL-FRAUD-DETECTION_DBMS_PROJECT/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── server.py
│
├── static/
│   └── Frontend HTML, CSS and JavaScript files
│
├── database/
│   ├── schema.cypher
│   ├── sample_data.cypher
│   └── queries.cypher
│
├── tests/
│   └── Test files
│
├── report/
│   └── DBMS_Project_Report.pdf
│
└── presentation/
    └── DBMS_Project_Presentation.pptx
```

The frontend files are maintained in the `static/` directory, while the database scripts are organised separately inside `database/`.

## 12. Installation and Setup

### Prerequisites

Install the following software:

- Python 3.x
- Neo4j Desktop or Neo4j running through Docker
- Git
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Vinodd07/FINANCIAL-FRAUD-DETECTION_DBMS_PROJECT.git

cd FINANCIAL-FRAUD-DETECTION_DBMS_PROJECT
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Start Neo4j

Start your Neo4j database and configure its connection details.

Example local configuration:

```text
URI: bolt://localhost:7687
Username: neo4j
Password: your_neo4j_password
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory.

Example:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

Use the variable names expected by the application. Never upload actual database credentials or the `.env` file to GitHub.

### Step 6: Create Database Constraints

Open Neo4j Browser and execute the contents of:

```text
database/schema.cypher
```

This creates the uniqueness constraints required by the application.

### Step 7: Load Sample Data

For demonstration records, execute:

```text
database/sample_data.cypher
```

This step is optional. The application also creates its required initial records during startup.

### Step 8: Run the Application

From the project root directory, execute:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 9: Open the Application

Open the following address in your browser:

```text
http://localhost:8000
```

To access the application from another device connected to the same Wi-Fi network, use:

```text
http://YOUR_LAPTOP_IP:8000
```

## 13. Cypher Queries

The project includes a separate `queries.cypher` file containing 15 queries for database operations and analysis.

These queries demonstrate:

- Retrieving customer and account information.
- Analysing money transfers.
- Identifying blocked transactions.
- Finding transactions pending OTP verification.
- Retrieving fraud cases.
- Analysing fraud factors.
- Viewing employee roles.
- Retrieving branch information.
- Tracking login IP addresses.
- Tracking device information.
- Identifying shared devices.
- Retrieving beneficiaries.
- Viewing support tickets.
- Analysing audit logs.
- Generating transaction statistics.

## 14. Testing

The application can be tested using the following scenarios:

- Customer registration and login.
- Employee login and role-based access.
- Account creation and virtual deposits.
- Beneficiary registration.
- Successful money transfer.
- Transaction requiring OTP verification.
- High-risk transaction blocking.
- Login from a new device.
- Login from a new IP address.
- Suspicious transaction pattern detection.
- Fraud case creation and investigation.
- Support ticket creation and management.
- Audit log generation.

## 15. Limitations

- OTP verification is simulated within the application; real SMS integration is not implemented.
- Deposits are virtual demonstrations and are not connected to real banking payment systems.
- The application is an academic prototype, not a production banking platform.
- Fraud detection decisions depend on the configured risk indicators and thresholds.
- Device and IP information do not independently prove fraudulent activity.
- The application does not connect to actual bank accounts or payment networks.

## 16. Future Enhancements

- Integrate a trained Random Forest model for transaction classification.
- Improve fraud prediction using historical financial transaction datasets.
- Implement real-time fraud monitoring and alert notifications.
- Introduce advanced graph-based fraud ring detection.
- Integrate real OTP delivery through an authorised SMS provider.
- Improve transaction behaviour analysis using historical customer patterns.
- Strengthen authentication and production-level security.

## 17. Project Demonstration

Watch the complete project demonstration to understand the banking operations, user roles, database implementation and fraud detection workflow.

**YouTube Demonstration:**  
https://youtu.be/uDMpE0RNGts

## 18. Team Members

**Project Title:** AI-Powered Financial Fraud Detection System

**Team Members:**

- **Vinodd V** — 25BCE1221
- **Varun Krishna** — 25BCE1530
- **Arjun Karthikeyan** — 25BCE1467

## 19. Academic Information

**Course:** Database Management Systems (DBMS)

**Project Type:** Graph Database-Based Banking and Financial Fraud Detection Application

**Database:** Neo4j Graph Database

**Query Language:** Cypher

**Backend:** Python and FastAPI

**Frontend:** HTML, CSS and JavaScript

**GitHub Repository:**  
https://github.com/Vinodd07/FINANCIAL-FRAUD-DETECTION_DBMS_PROJECT

---

