MERGE (b:Branch {ifsc:'NBNK0000001'})
ON CREATE SET
b.id='BR001',
b.name='NeoBank Main Branch',
b.city='Chennai',
b.status='ACTIVE';

MERGE (r1:Role {name:'ADMIN'});
MERGE (r2:Role {name:'MANAGER'});
MERGE (r3:Role {name:'TELLER'});
MERGE (r4:Role {name:'FRAUD_ANALYST'});
MERGE (r5:Role {name:'SUPPORT'});
MERGE (r6:Role {name:'CUSTOMER'});

MERGE (dep:Department {id:'DEP001'})
ON CREATE SET dep.name='Bank Operations';

MERGE (c1:Customer {id:'DEMO_CUS001'})
SET c1.name='Demo Customer One',
c1.email='demo1@example.com',
c1.phone='9000000001',
c1.role='CUSTOMER',
c1.status='ACTIVE',
c1.created=1760000000;

MERGE (c2:Customer {id:'DEMO_CUS002'})
SET c2.name='Demo Customer Two',
c2.email='demo2@example.com',
c2.phone='9000000002',
c2.role='CUSTOMER',
c2.status='ACTIVE',
c2.created=1760000100;

MERGE (a1:Account {id:'DEMO_ACC001'})
SET a1.acc_no='900000000001',
a1.balance=150000.00,
a1.status='ACTIVE',
a1.type='SAVINGS',
a1.created=1760000000;

MERGE (a2:Account {id:'DEMO_ACC002'})
SET a2.acc_no='900000000002',
a2.balance=50000.00,
a2.status='ACTIVE',
a2.type='SAVINGS',
a2.created=1760000100;

MERGE (c1)-[:OWNS]->(a1);
MERGE (c2)-[:OWNS]->(a2);

MERGE (a1)-[:AT_BRANCH]->(b);
MERGE (a2)-[:AT_BRANCH]->(b);

MERGE (c1)-[:HAS_ROLE]->(r6);
MERGE (c2)-[:HAS_ROLE]->(r6);

MERGE (e1:Employee {id:'DEMO_EMP001'})
SET e1.name='Demo Manager',
e1.email='manager.demo@example.com',
e1.phone='9000000011',
e1.role='MANAGER',
e1.status='ACTIVE',
e1.created=1760000200;

MERGE (e1)-[:HAS_ROLE]->(r2);
MERGE (e1)-[:IN_DEPARTMENT]->(dep);
MERGE (e1)-[:ASSIGNED_TO]->(b);

MERGE (ben:Beneficiary {id:'DEMO_BEN001'})
SET ben.nick='Demo Recipient',
ben.created=1760000300,
ben.status='ACTIVE';

MERGE (c1)-[:REGISTERED_BENEFICIARY]->(ben);
MERGE (ben)-[:POINTS_TO]->(a2);

MERGE (c1)-[hb:HAS_BENEFICIARY {id:'DEMO_BEN001'}]->(a2)
SET hb.nick='Demo Recipient',
hb.created=1760000300;

MERGE (dev:Device {hash:'DEMO_DEVICE_HASH_001'})
ON CREATE SET dev.created=1760000400;

MERGE (ip:IPAddress {ip:'192.0.2.10'})
ON CREATE SET ip.first_seen=1760000400;

MERGE (login:Login {id:'DEMO_LOGIN001'})
SET login.ts=1760000400,
login.browser='Chrome',
login.os='Windows',
login.platform='Windows',
login.tz='Asia/Kolkata',
login.lang='en-IN',
login.screen='1920x1080',
login.new_device=false,
login.new_ip=false,
login.shared_count=0;

MERGE (c1)-[:LOGGED_IN]->(login);
MERGE (login)-[:FROM_DEVICE]->(dev);
MERGE (login)-[:FROM_IP]->(ip);

MERGE (tx1:Transaction {id:'DEMO_TXN001'})
SET tx1.ref='NBDEMO0001',
tx1.type='TRANSFER',
tx1.amount=100000.00,
tx1.remarks='Demonstration high-risk transfer',
tx1.ts=1760000500,
tx1.status='BLOCKED',
tx1.fraud=98.7,
tx1.otp='';

MERGE (a1)-[:SENT]->(tx1);
MERGE (tx1)-[:RECEIVED_BY]->(a2);
MERGE (tx1)-[:MADE_IN]->(login);

MERGE (fc1:FraudCase {id:'DEMO_CASE001'})
SET fc1.status='OPEN',
fc1.score=98.7,
fc1.created=1760000500,
fc1.notes='Demo case: high-risk transfer blocked';

MERGE (tx1)-[:FLAGGED_AS]->(fc1);

MERGE (ff1:FraudFactor {id:'DEMO_FACTOR001'})
SET ff1.factor='High-value transfer',
ff1.points=25.0;

MERGE (tx1)-[:HAS_FACTOR]->(ff1);

MERGE (tx2:Transaction {id:'DEMO_TXN002'})
SET tx2.ref='NBDEMO0002',
tx2.type='TRANSFER',
tx2.amount=5000.00,
tx2.remarks='Demonstration successful transfer',
tx2.ts=1760000600,
tx2.status='SUCCESS',
tx2.fraud=16.1,
tx2.otp='';

MERGE (a1)-[:SENT]->(tx2);
MERGE (tx2)-[:RECEIVED_BY]->(a2);
MERGE (tx2)-[:MADE_IN]->(login);

MERGE (ticket:SupportTicket {id:'DEMO_TICKET001'})
SET ticket.subject='Demo support request',
ticket.message='This is sample support-ticket data.',
ticket.status='OPEN',
ticket.created=1760000700;

MERGE (c1)-[:RAISED]->(ticket);

MERGE (audit:AuditLog {id:'DEMO_AUDIT001'})
SET audit.actor_id='DEMO_CUS001',
audit.action='DEMO_DATA_CREATED',
audit.target='DEMO_TXN001',
audit.details='Sample data created for repository demonstration.',
audit.ts=1760000800;