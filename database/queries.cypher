MATCH (c:Customer)-[:OWNS]->(a:Account)
RETURN c.id AS Customer_ID, c.name AS Customer_Name, a.acc_no AS Account_Number, a.balance AS Balance;

MATCH (a:Account)-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(b:Account)
RETURN a.acc_no AS Sender_Account, b.acc_no AS Receiver_Account, t.amount AS Amount, t.type AS Transaction_Type, t.status AS Status, t.ts AS Timestamp;

MATCH (t:Transaction)
WHERE t.status = 'BLOCKED'
RETURN t.id AS Transaction_ID, t.amount AS Amount, t.fraud AS Fraud_Score, t.status AS Status, t.ts AS Timestamp;

MATCH (t:Transaction)
WHERE t.status = 'PENDING_OTP'
RETURN t.id AS Transaction_ID, t.amount AS Amount, t.fraud AS Fraud_Score, t.status AS Status;

MATCH (t:Transaction)-[:FLAGGED_AS]->(f:FraudCase)
RETURN t.id AS Transaction_ID, f.id AS Fraud_Case_ID, f.score AS Risk_Score, f.status AS Case_Status, f.notes AS Notes;

MATCH (t:Transaction)-[:HAS_FACTOR]->(f:FraudFactor)
RETURN t.id AS Transaction_ID, t.status AS Transaction_Status, f.factor AS Fraud_Factor, f.points AS Risk_Points;

MATCH (e:Employee)-[:HAS_ROLE]->(r:Role)
RETURN e.id AS Employee_ID, e.name AS Employee_Name, r.name AS Assigned_Role;

MATCH (e:Employee)-[:AT_BRANCH]->(b:Branch)
RETURN e.name AS Employee_Name, b.name AS Branch_Name, b.city AS City, b.ifsc AS IFSC_Code;

MATCH (p)-[:LOGGED_IN]->(l:Login)-[:FROM_IP]->(ip:IPAddress)
RETURN p.name AS User_Name, l.ts AS Login_Time, ip.ip AS IP_Address, l.new_ip AS New_IP;

MATCH (p)-[:LOGGED_IN]->(l:Login)-[:FROM_DEVICE]->(d:Device)
RETURN p.name AS User_Name, l.ts AS Login_Time, d.hash AS Device_Hash, l.browser AS Browser, l.os AS Operating_System, l.new_device AS New_Device;

MATCH (d:Device)<-[:FROM_DEVICE]-(l:Login)<-[:LOGGED_IN]-(p)
WITH d, collect(DISTINCT p.name) AS Users, count(DISTINCT p) AS User_Count
WHERE User_Count > 1
RETURN d.hash AS Shared_Device, Users, User_Count;

MATCH (c:Customer)-[r:HAS_BENEFICIARY]->(a:Account)
RETURN c.name AS Customer_Name, r.nick AS Beneficiary_Name, a.acc_no AS Beneficiary_Account, r.created AS Added_On;

MATCH (c:Customer)-[:RAISED]->(t:SupportTicket)
RETURN c.name AS Customer_Name, t.id AS Ticket_ID, t.subject AS Subject, t.status AS Ticket_Status, t.created AS Created_On;

MATCH (a:AuditLog)
RETURN a.actor_id AS Actor_ID, a.action AS Action, a.target AS Target, a.details AS Details, a.ts AS Timestamp
ORDER BY a.ts DESC;

MATCH (n)
UNWIND labels(n) AS Node_Label
RETURN Node_Label, count(*) AS Total_Nodes
ORDER BY Total_Nodes DESC;

MATCH (t:Transaction)
OPTIONAL MATCH (t)-[:FLAGGED_AS]->(f:FraudCase)
RETURN count(t) AS Total_Transactions,
       count(CASE WHEN t.status = 'SUCCESS' THEN 1 END) AS Successful_Transactions,
       count(CASE WHEN t.status = 'BLOCKED' THEN 1 END) AS Blocked_Transactions,
       count(CASE WHEN t.status = 'PENDING_OTP' THEN 1 END) AS Pending_OTP_Transactions,
       count(f) AS Fraud_Cases;