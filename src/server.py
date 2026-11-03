import secrets, hashlib, math, time, random, threading, os, uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from neo4j import GraphDatabase

BASE = os.path.dirname(os.path.abspath(__file__))
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PWD = os.getenv("NEO4J_PASSWORD", "neo4j12345")
IFSC = "NBNK0000001"
BLOCK_AT, OTP_AT = 70.0, 35.0
LOCK = threading.Lock()
driver = GraphDatabase.driver(URI, auth=(USER, PWD))

# Neo4j graph schema: 20+ node labels act as the project's relational tables.
CONSTRAINTS = [
 "CREATE CONSTRAINT c_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT c_email IF NOT EXISTS FOR (n:Customer) REQUIRE n.email IS UNIQUE",
 "CREATE CONSTRAINT a_id IF NOT EXISTS FOR (n:Account) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT a_no IF NOT EXISTS FOR (n:Account) REQUIRE n.acc_no IS UNIQUE",
 "CREATE CONSTRAINT b_ifsc IF NOT EXISTS FOR (n:Branch) REQUIRE n.ifsc IS UNIQUE",
 "CREATE CONSTRAINT d_hash IF NOT EXISTS FOR (n:Device) REQUIRE n.hash IS UNIQUE",
 "CREATE CONSTRAINT i_ip IF NOT EXISTS FOR (n:IPAddress) REQUIRE n.ip IS UNIQUE",
 "CREATE CONSTRAINT l_id IF NOT EXISTS FOR (n:Login) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT s_tok IF NOT EXISTS FOR (n:Session) REQUIRE n.token IS UNIQUE",
 "CREATE CONSTRAINT t_id IF NOT EXISTS FOR (n:Transaction) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT e_id IF NOT EXISTS FOR (n:Employee) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT ad_id IF NOT EXISTS FOR (n:AuditLog) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT case_id IF NOT EXISTS FOR (n:FraudCase) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT card_id IF NOT EXISTS FOR (n:BankCard) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT loan_id IF NOT EXISTS FOR (n:Loan) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT notif_id IF NOT EXISTS FOR (n:Notification) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT ticket_id IF NOT EXISTS FOR (n:SupportTicket) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT ben_id IF NOT EXISTS FOR (n:Beneficiary) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT role_name IF NOT EXISTS FOR (n:Role) REQUIRE n.name IS UNIQUE",
 "CREATE CONSTRAINT dept_id IF NOT EXISTS FOR (n:Department) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT branch_id IF NOT EXISTS FOR (n:Branch) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT factor_id IF NOT EXISTS FOR (n:FraudFactor) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT otp_id IF NOT EXISTS FOR (n:OTPChallenge) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT complaint_id IF NOT EXISTS FOR (n:Complaint) REQUIRE n.id IS UNIQUE",
 "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (n:BankPolicy) REQUIRE n.id IS UNIQUE",
]

ROLES = {
 "ADMIN": "Full system administration, staff provisioning, all customers/accounts/transactions, fraud cases, audit trail and system-wide reports.",
 "MANAGER": "Branch-level operations, customer and account oversight, employee activity, transaction review and fraud-case assignment.",
 "TELLER": "Branch deposits/withdrawals and customer service actions; cannot create staff or change system roles.",
 "FRAUD_ANALYST": "Review fraud scores and flagged transfers, investigate linked IP/device patterns, resolve fraud cases.",
 "SUPPORT": "View assigned customer profiles, handle support tickets/complaints and add notes; cannot move money.",
 "CUSTOMER": "Own account dashboard, beneficiaries, demo deposits, fund transfers, statements and own login/security history."
}

@asynccontextmanager
async def lifespan(app):
    try: driver.verify_connectivity()
    except Exception as e: raise RuntimeError(f"Cannot connect to Neo4j at {URI} as '{USER}'. Start Neo4j and check NEO4J_PASSWORD. Details: {e}")
    with driver.session() as s:
        for c in CONSTRAINTS: s.run(c).consume()
        s.run("MERGE (b:Branch {ifsc:$i}) ON CREATE SET b.id='BR001', b.name='NeoBank Main Branch', b.city='Chennai', b.status='ACTIVE'", i=IFSC).consume()
        for role, desc in ROLES.items():
            s.run("MERGE (r:Role {name:$n}) SET r.description=$d", n=role, d=desc).consume()
        s.run("MERGE (d:Department {id:'DEP001'}) ON CREATE SET d.name='Bank Operations'")
        # Keep the core entity labels visible in a fresh project database. These marked
        # schema records are not business records and are excluded from operational lists.
        for label, key, value in [
            ("AuditLog","id","SCHEMA_PLACEHOLDER"), ("FraudCase","id","SCHEMA_PLACEHOLDER"),
            ("FraudFactor","id","SCHEMA_PLACEHOLDER"), ("SupportTicket","id","SCHEMA_PLACEHOLDER"),
            ("Beneficiary","id","SCHEMA_PLACEHOLDER"), ("BankCard","id","SCHEMA_PLACEHOLDER"),
            ("Loan","id","SCHEMA_PLACEHOLDER"), ("Notification","id","SCHEMA_PLACEHOLDER"),
            ("Complaint","id","SCHEMA_PLACEHOLDER"), ("OTPChallenge","id","SCHEMA_PLACEHOLDER"),
            ("BankPolicy","id","SCHEMA_PLACEHOLDER")
        ]:
            s.run(f"MERGE (n:{label} {{{key}:$v}}) SET n._schema_placeholder=true", v=value).consume()
        # A development-only bootstrap administrator; override credentials through environment variables.
        admin_id = os.getenv("NEOBANK_ADMIN_ID", "ADMIN001")
        admin_pw = os.getenv("NEOBANK_ADMIN_PASSWORD", "Admin@12345")
        if not s.run("MATCH (e:Employee {id:$id}) RETURN e.id", id=admin_id).single():
            salt=secrets.token_hex(16)
            s.run("""CREATE (e:Employee {id:$id, name:'System Administrator', email:'admin@neobank.local',
                phone:'', salt:$salt, pw:$pw, role:'ADMIN', status:'ACTIVE', created:$now})
                WITH e MATCH (r:Role {name:'ADMIN'}), (d:Department {id:'DEP001'}), (b:Branch {ifsc:$ifsc})
                CREATE (e)-[:HAS_ROLE]->(r), (e)-[:IN_DEPARTMENT]->(d), (e)-[:ASSIGNED_TO]->(b)""",
                id=admin_id, salt=salt, pw=hpw(admin_pw,salt), now=time.time(), ifsc=IFSC).consume()
    yield
    driver.close()

app = FastAPI(title="NeoBank Banking & Fraud Detection (Neo4j)", lifespan=lifespan)

def work(fn):
    with driver.session() as s: return s.execute_write(fn)
def run(tx, cy, **p): tx.run(cy, **p).consume()
def rows(tx, cy, **p): return [r.data() for r in tx.run(cy, **p)]
def one(tx, cy, **p):
    r=tx.run(cy, **p).single()
    return r.data() if r else None
def hpw(pw,salt): return hashlib.pbkdf2_hmac("sha256",pw.encode(),salt.encode(),150000).hex()
def uid(): return uuid.uuid4().hex
def ref(): return "NB"+time.strftime("%y%m%d%H%M%S")+str(random.randint(100,999))
def gen_id(prefix, label):
    # IDs are user-facing and generated from a persisted sequence counter.
    def f(tx):
        r=one(tx, "MERGE (c:IdCounter {name:$n}) ON CREATE SET c.value=0 SET c.value=c.value+1 RETURN c.value AS v", n=prefix)
        return f"{prefix}{r['v']:06d}"
    return work(f)
def parse_ua(ua):
    b="Edge" if "Edg/" in ua else "Opera" if "OPR/" in ua else "Chrome" if "Chrome/" in ua else "Firefox" if "Firefox/" in ua else "Safari" if "Safari/" in ua else "Unknown"
    o="Windows" if "Windows" in ua else "Android" if "Android" in ua else "iOS" if ("iPhone" in ua or "iPad" in ua) else "macOS" if "Mac OS" in ua else "Linux" if "Linux" in ua else "Unknown"
    return b,o
def get_ip(req):
    # Only trust forwarded headers when running behind a trusted proxy in a real deployment.
    ip=req.client.host if req.client else "unknown"
    if ip=="::1": ip="127.0.0.1"
    return ip
class Client(BaseModel):
    fingerprint:str=""
    screen:str=""
    tz:str=""
    lang:str=""
    platform:str=""
class RegisterIn(Client):
    name:str
    email:str
    phone:str=""
    password:str
    initial_deposit:float=0
class LoginIn(Client):
    login_id:str
    password:str
class EmployeeIn(BaseModel):
    name:str
    email:str
    phone:str=""
    password:str=Field(min_length=8)
    role:str
class StatusIn(BaseModel):
    status:str
    reason:str=""
class BenIn(BaseModel):
    acc_no:str
    ifsc:str
    nick:str=""
class TransferIn(BaseModel):
    beneficiary_id:str
    amount:float
    remarks:str=""
class ConfirmIn(BaseModel):
    txn_id:str
    otp:str
class AmountIn(BaseModel):
    amount:float
    account_no:str=""
class CaseIn(BaseModel):
    status:str="UNDER_REVIEW"
    notes:str=""
class TicketIn(BaseModel):
    subject:str
    message:str

def dev_info(req,d):
    ua=req.headers.get("user-agent",""); b,o=parse_ua(ua)
    return get_ip(req),hashlib.sha256((d.fingerprint+"|"+ua).encode()).hexdigest()[:32],b,o
def audit(tx, actor, action, target="", details=""):
    now=time.time()
    run(tx, """CREATE (a:AuditLog {id:$id, actor_id:$actor, action:$action, target:$target, details:$details, ts:$ts})
        """, id=uid(), actor=actor, action=action, target=target, details=details[:1000], ts=now)
def upsert_device(tx,cid,h,label,primary):
    now=time.time()
    r=one(tx,"MATCH (c:Customer {id:$cid}) OPTIONAL MATCH (c)-[u:USES]->(d:Device {hash:$h}) RETURN u.first_seen AS fs,u.is_primary AS pr",cid=cid,h=h)
    if r and r["fs"] is not None:
        run(tx,"MATCH (:Customer {id:$cid})-[u:USES]->(:Device {hash:$h}) SET u.last_seen=$now",cid=cid,h=h,now=now)
        return 0 if r["pr"] else int(now-r["fs"]<86400)
    run(tx,"MERGE (d:Device {hash:$h}) ON CREATE SET d.created=$now WITH d MATCH (c:Customer {id:$cid}) CREATE (c)-[:USES {label:$label,first_seen:$now,last_seen:$now,is_primary:$pr}]->(d)",h=h,cid=cid,now=now,label=label,pr=primary)
    return 0 if primary else 1
def make_login(tx, person_label, pid, d, h, ip, b, o, nd, first):
    now=time.time(); lid=uid(); tok=secrets.token_urlsafe(32)
    run(tx,"MERGE (i:IPAddress {ip:$ip}) ON CREATE SET i.first_seen=$now",ip=ip,now=now)
    seen=one(tx,"MATCH (p {id:$pid})-[:LOGGED_IN]->(:Login)-[:FROM_IP]->(:IPAddress {ip:$ip}) RETURN count(*) AS n",pid=pid,ip=ip)["n"]
    nip=0 if (first or seen>0) else 1
    shared=one(tx,"MATCH (d:Device {hash:$h})<-[:FROM_DEVICE]-(:Login)<-[:LOGGED_IN]-(p) WHERE p.id<>$pid RETURN count(DISTINCT p) AS n",h=h,pid=pid)["n"]
    run(tx,f"""MATCH (p:{person_label} {{id:$pid}}),(dv:Device {{hash:$h}}),(i:IPAddress {{ip:$ip}})
      CREATE (l:Login {{id:$lid,ts:$now,browser:$b,os:$o,platform:$pl,tz:$tz,lang:$lang,screen:$sc,new_device:$nd,new_ip:$nip,shared_count:$shared}})
      CREATE (p)-[:LOGGED_IN]->(l),(l)-[:FROM_DEVICE]->(dv),(l)-[:FROM_IP]->(i)
      CREATE (s:Session {{token:$tok,created:$now,role:$role}}),(p)-[:HAS_SESSION]->(s),(s)-[:FOR_LOGIN]->(l)""",
      pid=pid,h=h,ip=ip,lid=lid,now=now,b=b,o=o,pl=d.platform,tz=d.tz,lang=d.lang,sc=d.screen,nd=nd,nip=nip,shared=shared,tok=tok,role=person_label)
    return tok,lid
def current(request:Request):
    token=request.cookies.get("session") or ""
    def f(tx):
        return one(tx,"""MATCH (s:Session {token:$t})-[:FOR_LOGIN]->(l:Login)<-[:LOGGED_IN]-(p)
          WHERE s.created>$since AND coalesce(p.status,'ACTIVE')='ACTIVE'
          RETURN p.id AS id,p.name AS name,p.email AS email,p.role AS role,labels(p) AS labels,
          l.id AS login_id,l.new_device AS new_device,l.new_ip AS new_ip,l.shared_count AS shared_count,
          l.browser AS browser,l.os AS os,l.platform AS platform,l.tz AS tz,l.screen AS screen,
          head([(l)-[:FROM_IP]->(i:IPAddress) | i.ip]) AS ip,
          head([(l)-[:FROM_DEVICE]->(d:Device) | d.hash]) AS device_hash,
          head([(p)-[:OWNS]->(a:Account) | a.id]) AS account_id,
          head([(p)-[:OWNS]->(a:Account) | a.acc_no]) AS acc_no,
          head([(p)-[:OWNS]->(a:Account) | a.balance]) AS balance,
          head([(p)-[:OWNS]->(a:Account)-[:AT_BRANCH]->(b:Branch) | b.ifsc]) AS ifsc,
          coalesce(p.role,'CUSTOMER') AS actual_role""",t=token,since=time.time()-43200)
    u=work(f)
    if not u: raise HTTPException(401,"Session expired. Please log in again.")
    return u
def auth(request:Request): return current(request)
def require(*roles):
    def dep(u=Depends(auth)):
        if u["role"] not in roles: raise HTTPException(403,"Your role is not allowed to perform this action.")
        return u
    return dep
def log_activity(tx,u,action,target="",details=""):
    audit(tx,u["id"],action,target,details)
def deposit_txn(tx,aid,lid,amt,remarks,actor):
    tid=uid()
    run(tx,"""MATCH (a:Account {id:$aid}),(l:Login {id:$lid})
      CREATE (t:Transaction {id:$tid,ref:$ref,type:'DEPOSIT',amount:$amt,remarks:$rem,ts:$now,status:'SUCCESS',fraud:0.0,otp:''})
      CREATE (t)-[:RECEIVED_BY]->(a),(t)-[:MADE_IN]->(l)""",aid=aid,lid=lid,tid=tid,ref=ref(),amt=amt,rem=remarks,now=time.time())
    audit(tx,actor,"DEPOSIT",aid,f"{amt:.2f}")
def score_txn(tx,u,ben_created,to_aid,amount,balance):
    now=time.time(); factors=[]
    def add(name,w,v):
        if v>0:factors.append({"factor":name,"points":round(w*v,2)})
    avg=one(tx,"MATCH (:Account {id:$a})-[:SENT]->(t:Transaction {status:'SUCCESS'}) RETURN avg(t.amount) AS a",a=u["account_id"])["a"]
    ratio=amount/max(avg or 5000,1000)
    n=one(tx,"MATCH (:Account {id:$a})-[:SENT]->(t:Transaction) WHERE t.ts>$s RETURN count(t) AS n",a=u["account_id"],s=now-600)["n"]
    mule=one(tx,"MATCH (s:Account)-[:SENT]->(t:Transaction {status:'SUCCESS'})-[:RECEIVED_BY]->(:Account {id:$a}) WHERE t.ts>$s RETURN count(DISTINCT s) AS n",a=to_aid,s=now-86400)["n"]
    add("New / unrecognised device",2.5,u["new_device"]); add("Login from a new IP address",1.3,u["new_ip"])
    add("Amount far above usual transfers",2.0,min(math.log10(max(ratio,1)),2)/2)
    add("Large share of account balance",1.5,min(amount/max(balance,1),1))
    add("High-value transfer",1.0,1 if amount>=100000 else .5 if amount>=50000 else 0)
    add("Recently added beneficiary (<24h)",1.0,1 if now-ben_created<86400 else 0)
    add("Unusual hour (12am-5am)",.6,1 if time.localtime(now).tm_hour<5 else 0)
    add("Rapid repeated transfers",1.2,min(n/3,1))
    add("Graph: shared device",1.8,min(max(u["shared_count"]-2,0)/3,1))
    add("Graph: beneficiary receiving from many senders",1.5,min(max(mule-2,0)/3,1))
    z=-3.4+sum(x["points"] for x in factors)
    return round(100/(1+math.exp(-z)),1),factors
def create_account_for_customer(tx,c,initial,branch_ifsc=IFSC):
    aid=uid(); acc="".join(random.choice("0123456789") for _ in range(12))
    while one(tx,"MATCH (a:Account {acc_no:$a}) RETURN a.id AS id",a=acc): acc="".join(random.choice("0123456789") for _ in range(12))
    run(tx,"MATCH (c:Customer {id:$cid}),(b:Branch {ifsc:$ifsc}) CREATE (a:Account {id:$aid,acc_no:$acc,balance:$bal,status:'ACTIVE',type:'SAVINGS',created:$now}) CREATE (c)-[:OWNS]->(a),(a)-[:AT_BRANCH]->(b)",cid=c["id"],ifsc=branch_ifsc,aid=aid,acc=acc,bal=round(initial,2),now=time.time())
    return aid,acc

@app.post("/api/register")
def register(d:RegisterIn,request:Request,response:Response):
    if len(d.password)<8: raise HTTPException(400,"Password must be at least 8 characters")
    if d.initial_deposit<0 or d.initial_deposit>10000000: raise HTTPException(400,"Invalid opening deposit")
    email=d.email.lower().strip()
    if not email or "@" not in email: raise HTTPException(400,"Enter a valid email")
    ip,h,b,o=dev_info(request,d); cid=gen_id("CUS","Customer")
    def f(tx):
        if one(tx,"MATCH (c:Customer {email:$e}) RETURN c.id AS id",e=email): raise HTTPException(400,"Email already registered")
        now=time.time(); salt=secrets.token_hex(16)
        run(tx,"CREATE (c:Customer {id:$cid,name:$name,email:$e,phone:$ph,salt:$salt,pw:$pw,role:'CUSTOMER',status:'ACTIVE',created:$now})",cid=cid,name=d.name.strip(),e=email,ph=d.phone,salt=salt,pw=hpw(d.password,salt),now=now)
        aid,acc=create_account_for_customer(tx,{"id":cid},d.initial_deposit)
        upsert_device(tx,cid,h,f"{b} on {o}",True)
        tok,lid=make_login(tx,"Customer",cid,d,h,ip,b,o,0,True)
        if d.initial_deposit>0: deposit_txn(tx,aid,lid,d.initial_deposit,"Opening deposit",cid)
        run(tx,"MATCH (c:Customer {id:$id}),(r:Role {name:'CUSTOMER'}) CREATE (c)-[:HAS_ROLE]->(r)",id=cid)
        return tok
    with LOCK: tok=work(f)
    response.set_cookie("session",tok,httponly=True,samesite="lax")
    return {"ok":True,"customer_id":cid,"account_created":True}
@app.post("/api/login")
def login(d:LoginIn,request:Request,response:Response):
    ip,h,b,o=dev_info(request,d); login_id=d.login_id.strip().upper()
    def f(tx):
        p=one(tx,"MATCH (p) WHERE (p:Customer OR p:Employee) AND p.id=$id RETURN p.id AS id,labels(p) AS labels,p.salt AS salt,p.pw AS pw,p.status AS status,p.role AS role",id=login_id)
        if not p or hpw(d.password,p["salt"])!=p["pw"]: raise HTTPException(401,"Invalid ID or password")
        if p["status"]!="ACTIVE": raise HTTPException(403,"This account is disabled. Contact the bank administrator.")
        label="Customer" if "Customer" in p["labels"] else "Employee"
        if label=="Customer": nd=upsert_device(tx,p["id"],h,f"{b} on {o}",False)
        else:
            exists=one(tx,"MATCH (:Employee {id:$id})-[:LOGGED_IN]->(:Login)-[:FROM_DEVICE]->(:Device {hash:$h}) RETURN count(*) AS n",id=p["id"],h=h)["n"]
            run(tx,"MERGE (d:Device {hash:$h}) ON CREATE SET d.created=$now",h=h,now=time.time()); nd=0 if exists else 1
        tok,lid=make_login(tx,label,p["id"],d,h,ip,b,o,nd,False)
        audit(tx,p["id"],"LOGIN",p["id"],f"{ip} | {b}/{o}")
        return tok
    with LOCK: tok=work(f)
    response.set_cookie("session",tok,httponly=True,samesite="lax")
    return {"ok":True}
@app.post("/api/logout")
def logout(request:Request,response:Response):
    token=request.cookies.get("session") or ""
    try:
        u=current(request); work(lambda tx:audit(tx,u["id"],"LOGOUT",u["id"],"User logout"))
    except Exception: pass
    work(lambda tx:run(tx,"MATCH (s:Session {token:$t}) DETACH DELETE s",t=token))
    response.delete_cookie("session")
    return {"ok":True}
@app.get("/api/me")
def me(u=Depends(auth)):
    return {"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"],"account_id":u["account_id"],"acc_no":u["acc_no"],"ifsc":u["ifsc"],"balance":u["balance"],"session":{"ip":u["ip"],"device":u["device_hash"][:10] if u["device_hash"] else "Unknown","browser":u["browser"],"os":u["os"],"new_device":u["new_device"],"new_ip":u["new_ip"]}}
@app.get("/api/roles")
def roles(): return [{"role":k,"description":v} for k,v in ROLES.items()]

# Customer self-service routes
@app.get("/api/beneficiaries")
def list_ben(u=Depends(require("CUSTOMER"))):
    return work(lambda tx:rows(tx,"MATCH (:Customer {id:$cid})-[r:HAS_BENEFICIARY]->(a:Account)<-[:OWNS]-(o:Customer) MATCH (a)-[:AT_BRANCH]->(b:Branch) RETURN r.id AS id,r.nick AS nick,r.created AS created,a.acc_no AS acc_no,b.ifsc AS ifsc,o.name AS name ORDER BY r.created DESC",cid=u["id"]))
@app.post("/api/beneficiaries")
def add_ben(d:BenIn,u=Depends(require("CUSTOMER"))):
    def f(tx):
        t=one(tx,"MATCH (o:Customer)-[:OWNS]->(a:Account {acc_no:$acc})-[:AT_BRANCH]->(:Branch {ifsc:$ifsc}) RETURN o.id AS oid,o.name AS name,a.id AS aid",acc=d.acc_no.strip(),ifsc=d.ifsc.strip().upper())
        if not t: raise HTTPException(400,"Account number / IFSC not found")
        if t["oid"]==u["id"]: raise HTTPException(400,"Cannot add your own account")
        if one(tx,"MATCH (:Customer {id:$cid})-[:HAS_BENEFICIARY]->(:Account {id:$aid}) RETURN count(*) AS n",cid=u["id"],aid=t["aid"])["n"]: raise HTTPException(400,"Beneficiary already added")
        bid=uid()
        run(tx,"MATCH (c:Customer {id:$cid}),(a:Account {id:$aid}) CREATE (c)-[:HAS_BENEFICIARY {id:$id,nick:$nick,created:$now}]->(a) CREATE (b:Beneficiary {id:$id,nick:$nick,created:$now,status:'ACTIVE'}) CREATE (c)-[:REGISTERED_BENEFICIARY]->(b) CREATE (b)-[:POINTS_TO]->(a)",cid=u["id"],aid=t["aid"],id=bid,nick=d.nick or t["name"],now=time.time())
        audit(tx,u["id"],"ADD_BENEFICIARY",bid,t["name"])
    work(f); return {"ok":True}
@app.delete("/api/beneficiaries/{bid}")
def del_ben(bid:str,u=Depends(require("CUSTOMER"))):
    work(lambda tx:run(tx,"MATCH (:Customer {id:$cid})-[r:HAS_BENEFICIARY {id:$bid}]->() DELETE r WITH $cid AS cid MATCH (c:Customer {id:cid})-[:REGISTERED_BENEFICIARY]->(b:Beneficiary {id:$bid}) DETACH DELETE b",cid=u["id"],bid=bid))
    return {"ok":True}
@app.post("/api/deposit")
def deposit(d:AmountIn,u=Depends(require("CUSTOMER","TELLER","MANAGER","ADMIN"))):
    if d.amount<=0 or d.amount>10000000: raise HTTPException(400,"Invalid amount")
    def f(tx):
        if u["role"]=="CUSTOMER":
            aid=u["account_id"]
        else:
            target=one(tx,"MATCH (a:Account {acc_no:$no,status:'ACTIVE'}) RETURN a.id AS id",no=d.account_no.strip())
            if not target: raise HTTPException(400,"Enter a valid active account number.")
            aid=target["id"]
        run(tx,"MATCH (a:Account {id:$a,status:'ACTIVE'}) SET a.balance=a.balance+$amt",a=aid,amt=d.amount)
        deposit_txn(tx,aid,u["login_id"],d.amount,"Cash deposit (prototype)",u["id"])
    work(f); return {"ok":True}
@app.post("/api/transfer")
def transfer(d:TransferIn,u=Depends(require("CUSTOMER"))):
    amt=round(d.amount,2)
    if amt<=0 or amt>10000000: raise HTTPException(400,"Invalid amount")
    def f(tx):
        ben=one(tx,"MATCH (:Customer {id:$cid})-[r:HAS_BENEFICIARY {id:$bid}]->(ta:Account) RETURN r.created AS created,ta.id AS taid",cid=u["id"],bid=d.beneficiary_id)
        if not ben: raise HTTPException(400,"Beneficiary not found")
        acc=one(tx,"MATCH (a:Account {id:$a}) RETURN a.balance AS b,a.status AS status",a=u["account_id"])
        if acc["status"]!="ACTIVE": raise HTTPException(403,"Account is not active")
        if amt>acc["b"]: raise HTTPException(400,"Insufficient balance")
        p,fac=score_txn(tx,u,ben["created"],ben["taid"],amt,acc["b"])
        status="BLOCKED" if p>=BLOCK_AT else "PENDING_OTP" if p>=OTP_AT else "SUCCESS"
        otp=str(random.randint(100000,999999)) if status=="PENDING_OTP" else ""
        tid=uid()
        run(tx,"""MATCH (fa:Account {id:$fa}),(ta:Account {id:$ta}),(l:Login {id:$lid})
          CREATE (t:Transaction {id:$tid,ref:$ref,type:'TRANSFER',amount:$amt,remarks:$rem,ts:$now,status:$st,fraud:$p,otp:$otp})
          CREATE (fa)-[:SENT]->(t),(t)-[:RECEIVED_BY]->(ta),(t)-[:MADE_IN]->(l)
          CREATE (fc:FraudCase {id:$case,status:$caseStatus,score:$p,created:$now,notes:'Auto-created by fraud rule engine'})
          CREATE (t)-[:FLAGGED_AS]->(fc)""",fa=u["account_id"],ta=ben["taid"],lid=u["login_id"],tid=tid,ref=ref(),amt=amt,rem=d.remarks,now=time.time(),st=status,p=p,otp=otp,case=uid(),caseStatus="OPEN" if p>=OTP_AT else "CLOSED")
        if fac: run(tx,"MATCH (t:Transaction {id:$tid}) UNWIND $fs AS f CREATE (t)-[:HAS_FACTOR]->(:FraudFactor {id:f.id,factor:f.factor,points:f.points})",tid=tid,fs=[dict(x,id=uid()) for x in fac])
        if status=="SUCCESS": run(tx,"MATCH (fa:Account {id:$fa}),(ta:Account {id:$ta}) SET fa.balance=fa.balance-$amt,ta.balance=ta.balance+$amt",fa=u["account_id"],ta=ben["taid"],amt=amt)
        audit(tx,u["id"],"TRANSFER",tid,f"{amt:.2f} | {status} | risk={p}")
        return {"txn_id":tid,"status":status,"fraud_percent":p,"factors":fac,"demo_otp":otp or None}
    with LOCK: return work(f)
@app.post("/api/transfer/confirm")
def confirm(d:ConfirmIn,u=Depends(require("CUSTOMER"))):
    def f(tx):
        t=one(tx,"MATCH (:Account {id:$a})-[:SENT]->(t:Transaction {id:$tid,status:'PENDING_OTP'})-[:RECEIVED_BY]->(ta:Account) RETURN t.otp AS otp,t.amount AS amount,ta.id AS taid",a=u["account_id"],tid=d.txn_id)
        if not t:return "none"
        if t["otp"]!=d.otp.strip():
            run(tx,"MATCH (t:Transaction {id:$tid}) SET t.status='BLOCKED'",tid=d.txn_id); return "wrong"
        bal=one(tx,"MATCH (a:Account {id:$a}) RETURN a.balance AS b",a=u["account_id"])["b"]
        if t["amount"]>bal:return "funds"
        run(tx,"MATCH (fa:Account {id:$fa}),(ta:Account {id:$ta}) SET fa.balance=fa.balance-$amt,ta.balance=ta.balance+$amt WITH fa,ta MATCH (t:Transaction {id:$tid}) SET t.status='SUCCESS',t.otp=''",fa=u["account_id"],ta=t["taid"],amt=t["amount"],tid=d.txn_id)
        audit(tx,u["id"],"OTP_CONFIRMED",d.txn_id,"Transfer confirmed")
        return "ok"
    with LOCK:r=work(f)
    if r=="none":raise HTTPException(400,"No pending transaction")
    if r=="wrong":raise HTTPException(400,"Wrong OTP - transaction cancelled")
    if r=="funds":raise HTTPException(400,"Insufficient balance")
    return {"status":"SUCCESS"}
@app.get("/api/transactions")
def txns(u=Depends(auth)):
    if u["role"]=="CUSTOMER":
        def f(tx):
            deb=rows(tx,"""MATCH (a:Account {id:$a})-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(ta:Account)<-[:OWNS]-(tc:Customer)
              OPTIONAL MATCH (t)-[:HAS_FACTOR]->(f:FraudFactor)
              RETURN t.id AS id,t.ref AS ref,t.ts AS ts,t.amount AS amount,t.remarks AS remarks,t.status AS status,t.fraud AS fraud,tc.name AS party,ta.acc_no AS party_acc,collect(f {.factor,.points}) AS factors""",a=u["account_id"])
            cre=rows(tx,"""MATCH (t:Transaction {status:'SUCCESS'})-[:RECEIVED_BY]->(a:Account {id:$a}) OPTIONAL MATCH (fa:Account)-[:SENT]->(t) OPTIONAL MATCH (fa)<-[:OWNS]-(fc:Customer)
              RETURN t.id AS id,t.ref AS ref,t.ts AS ts,t.amount AS amount,t.remarks AS remarks,t.status AS status,coalesce(fc.name,'Cash Deposit') AS party,coalesce(fa.acc_no,'CASH') AS party_acc""",a=u["account_id"])
            return [dict(x,type="DEBIT") for x in deb]+[dict(x,type="CREDIT",fraud=None,factors=[]) for x in cre]
        out=work(f)
    else:
        out=work(lambda tx:rows(tx,"""MATCH (t:Transaction) OPTIONAL MATCH (fa:Account)-[:SENT]->(t) OPTIONAL MATCH (fa)<-[:OWNS]-(fc:Customer)
          OPTIONAL MATCH (t)-[:RECEIVED_BY]->(ta:Account) OPTIONAL MATCH (ta)<-[:OWNS]-(tc:Customer)
          RETURN t.id AS id,t.ref AS ref,t.ts AS ts,t.amount AS amount,t.remarks AS remarks,t.status AS status,t.fraud AS fraud,t.type AS type,
          coalesce(fc.name,'Bank') AS party,coalesce(ta.acc_no,'') AS party_acc,coalesce(tc.id,'') AS customer_id ORDER BY t.ts DESC LIMIT 500"""))
    out.sort(key=lambda x:x.get("ts",0),reverse=True)
    return out[:500]
@app.get("/api/logins")
def logins(u=Depends(auth)):
    if u["role"]=="CUSTOMER":
        return work(lambda tx:rows(tx,"MATCH (:Customer {id:$cid})-[:LOGGED_IN]->(l:Login)-[:FROM_IP]->(i:IPAddress) MATCH (l)-[:FROM_DEVICE]->(d:Device) RETURN l.ts AS ts,l.browser AS browser,l.os AS os,l.platform AS platform,l.tz AS tz,l.lang AS lang,l.screen AS screen,l.new_device AS new_device,l.new_ip AS new_ip,i.ip AS ip,d.hash AS dev_hash ORDER BY l.ts DESC LIMIT 100",cid=u["id"]))
    return work(lambda tx:rows(tx,"MATCH (p)-[:LOGGED_IN]->(l:Login)-[:FROM_IP]->(i:IPAddress) MATCH (l)-[:FROM_DEVICE]->(d:Device) RETURN p.id AS user_id,p.name AS name,coalesce(p.role,'CUSTOMER') AS role,l.ts AS ts,l.browser AS browser,l.os AS os,l.platform AS platform,i.ip AS ip,d.hash AS dev_hash,l.new_device AS new_device,l.new_ip AS new_ip ORDER BY l.ts DESC LIMIT 1000"))
@app.get("/api/network")
def network(u=Depends(auth)):
    cid=u["id"]
    if u["role"]!="CUSTOMER": cid=None
    def f(tx):
        if cid:
            devs=rows(tx,"MATCH (c:Customer {id:$cid})-[u:USES]->(d:Device) OPTIONAL MATCH (d)<-[:USES]-(o:Customer) WHERE o.id<>$cid RETURN u.label AS label,d.hash AS hash,u.first_seen AS first_seen,u.last_seen AS last_seen,u.is_primary AS is_primary,count(DISTINCT o) AS others ORDER BY last_seen DESC",cid=cid)
            ips=rows(tx,"MATCH (c:Customer {id:$cid})-[:LOGGED_IN]->(l:Login)-[:FROM_IP]->(i:IPAddress) WITH i,count(l) AS logins,max(l.ts) AS last OPTIONAL MATCH (i)<-[:FROM_IP]-(:Login)<-[:LOGGED_IN]-(o:Customer) WHERE o.id<>$cid RETURN i.ip AS ip,logins,last,count(DISTINCT o) AS others ORDER BY last DESC",cid=cid)
        else:
            devs=rows(tx,"MATCH (d:Device)<-[:FROM_DEVICE]-(l:Login)<-[:LOGGED_IN]-(p) RETURN d.hash AS hash,count(l) AS logins,count(DISTINCT p) AS users,max(l.ts) AS last_seen ORDER BY users DESC LIMIT 100")
            ips=rows(tx,"MATCH (i:IPAddress)<-[:FROM_IP]-(l:Login)<-[:LOGGED_IN]-(p) RETURN i.ip AS ip,count(l) AS logins,count(DISTINCT p) AS others,max(l.ts) AS last ORDER BY others DESC LIMIT 100")
        return {"devices":devs,"ips":ips}
    return work(f)

# Staff and administration
@app.get("/api/admin/overview")
def overview(u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    def f(tx):
        return one(tx,"""OPTIONAL MATCH (c:Customer) WITH count(c) AS customers
          OPTIONAL MATCH (a:Account) WITH customers,count(a) AS accounts
          OPTIONAL MATCH (t:Transaction) WITH customers,accounts,count(t) AS transactions
          OPTIONAL MATCH (e:Employee) WITH customers,accounts,transactions,count(e) AS employees
          OPTIONAL MATCH (fc:FraudCase) WITH customers,accounts,transactions,employees,count(CASE WHEN fc.status<>'CLOSED' THEN 1 END) AS open_cases
          OPTIONAL MATCH (t2:Transaction) RETURN customers,accounts,transactions,employees,open_cases,
          count(CASE WHEN t2.status='BLOCKED' THEN 1 END) AS blocked_transactions,
          count(CASE WHEN t2.fraud>=35 THEN 1 END) AS flagged_transactions""")
    return work(f)
@app.get("/api/admin/customers")
def all_customers(u=Depends(require("ADMIN","MANAGER","TELLER","SUPPORT","FRAUD_ANALYST"))):
    return work(lambda tx:rows(tx,"""MATCH (c:Customer) OPTIONAL MATCH (c)-[:OWNS]->(a:Account) OPTIONAL MATCH (a)-[:AT_BRANCH]->(b:Branch)
      RETURN c.id AS id,c.name AS name,c.email AS email,c.phone AS phone,c.status AS status,c.created AS created,
      a.id AS account_id,a.acc_no AS acc_no,a.balance AS balance,a.status AS account_status,a.type AS account_type,b.ifsc AS ifsc ORDER BY c.created DESC LIMIT 1000"""))
@app.get("/api/admin/accounts")
def all_accounts(u=Depends(require("ADMIN","MANAGER","TELLER","FRAUD_ANALYST"))):
    return work(lambda tx:rows(tx,"""MATCH (c:Customer)-[:OWNS]->(a:Account) OPTIONAL MATCH (a)-[:AT_BRANCH]->(b:Branch)
      RETURN c.id AS customer_id,c.name AS customer,a.id AS id,a.acc_no AS acc_no,a.balance AS balance,a.status AS status,a.type AS type,a.created AS created,b.ifsc AS ifsc ORDER BY a.created DESC LIMIT 1000"""))
@app.get("/api/admin/employees")
def employees(u=Depends(require("ADMIN","MANAGER"))):
    return work(lambda tx:rows(tx,"MATCH (e:Employee) OPTIONAL MATCH (e)-[:ASSIGNED_TO]->(b:Branch) RETURN e.id AS id,e.name AS name,e.email AS email,e.phone AS phone,e.role AS role,e.status AS status,e.created AS created,b.name AS branch ORDER BY e.created DESC"))
@app.post("/api/admin/employees")
def create_employee(d:EmployeeIn,u=Depends(require("ADMIN"))):
    role=d.role.upper()
    if role not in ("MANAGER","TELLER","FRAUD_ANALYST","SUPPORT"): raise HTTPException(400,"Choose MANAGER, TELLER, FRAUD_ANALYST or SUPPORT.")
    if len(d.password)<8: raise HTTPException(400,"Password must be at least 8 characters")
    eid=gen_id("EMP","Employee"); salt=secrets.token_hex(16)
    def f(tx):
        if one(tx,"MATCH (e:Employee {email:$e}) RETURN e.id AS id",e=d.email.lower().strip()):raise HTTPException(400,"Employee email already exists")
        run(tx,"""MATCH (r:Role {name:$role}),(dep:Department {id:'DEP001'}),(b:Branch {ifsc:$ifsc})
          CREATE (e:Employee {id:$id,name:$name,email:$email,phone:$phone,salt:$salt,pw:$pw,role:$role,status:'ACTIVE',created:$now})
          CREATE (e)-[:HAS_ROLE]->(r),(e)-[:IN_DEPARTMENT]->(dep),(e)-[:ASSIGNED_TO]->(b)""",role=role,ifsc=IFSC,id=eid,name=d.name.strip(),email=d.email.lower().strip(),phone=d.phone,salt=salt,pw=hpw(d.password,salt),now=time.time())
        audit(tx,u["id"],"CREATE_EMPLOYEE",eid,role)
    work(f);return {"ok":True,"employee_id":eid,"role":role}
@app.patch("/api/admin/employees/{eid}")
def update_employee(eid:str,d:StatusIn,u=Depends(require("ADMIN"))):
    if d.status not in ("ACTIVE","SUSPENDED","DISABLED"):raise HTTPException(400,"Invalid status")
    if eid==u["id"]:raise HTTPException(400,"You cannot disable your own admin login")
    def f(tx):
        run(tx,"MATCH (e:Employee {id:$id}) SET e.status=$status",id=eid,status=d.status)
        audit(tx,u["id"],"EMPLOYEE_STATUS",eid,d.status+" "+d.reason)
    work(f);return {"ok":True}
@app.patch("/api/admin/customers/{cid}")
def update_customer(cid:str,d:StatusIn,u=Depends(require("ADMIN","MANAGER"))):
    if d.status not in ("ACTIVE","SUSPENDED","DISABLED"):raise HTTPException(400,"Invalid status")
    def f(tx):
        run(tx,"MATCH (c:Customer {id:$id}) SET c.status=$status",id=cid,status=d.status)
        audit(tx,u["id"],"CUSTOMER_STATUS",cid,d.status+" "+d.reason)
    work(f);return {"ok":True}
@app.patch("/api/admin/accounts/{aid}")
def update_account(aid:str,d:StatusIn,u=Depends(require("ADMIN","MANAGER"))):
    if d.status not in ("ACTIVE","FROZEN","CLOSED"):raise HTTPException(400,"Invalid status")
    def f(tx):
        run(tx,"MATCH (a:Account {id:$id}) SET a.status=$status",id=aid,status=d.status)
        audit(tx,u["id"],"ACCOUNT_STATUS",aid,d.status+" "+d.reason)
    work(f);return {"ok":True}
@app.get("/api/admin/fraud")
def fraud_cases(u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    return work(lambda tx:rows(tx,"""MATCH (t:Transaction) WHERE coalesce(t.fraud,0)>=35 OR t.status='BLOCKED' OR t.status='PENDING_OTP'
      OPTIONAL MATCH (a:Account)-[:SENT]->(t) OPTIONAL MATCH (a)<-[:OWNS]-(c:Customer)
      OPTIONAL MATCH (t)-[:RECEIVED_BY]->(ta:Account) OPTIONAL MATCH (t)-[:FLAGGED_AS]->(fc:FraudCase)
      RETURN t.id AS id,t.ref AS ref,t.ts AS ts,t.amount AS amount,t.status AS status,t.fraud AS fraud,t.remarks AS remarks,
      c.id AS customer_id,c.name AS customer,ta.acc_no AS recipient,fc.id AS case_id,fc.status AS case_status,fc.notes AS notes
      ORDER BY t.ts DESC LIMIT 500"""))
@app.patch("/api/admin/fraud/{caseid}")
def update_case(caseid:str,d:CaseIn,u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    if d.status not in ("OPEN","UNDER_REVIEW","ESCALATED","CLOSED"):raise HTTPException(400,"Invalid case status")
    def f(tx):
        run(tx,"MATCH (fc:FraudCase {id:$id}) SET fc.status=$status,fc.notes=$notes,fc.updated=$now,fc.assigned_to=$actor",id=caseid,status=d.status,notes=d.notes,now=time.time(),actor=u["id"])
        audit(tx,u["id"],"UPDATE_FRAUD_CASE",caseid,d.status)
    work(f);return {"ok":True}
@app.get("/api/admin/audit")
def audit_logs(u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    return work(lambda tx:rows(tx,"MATCH (a:AuditLog) WHERE coalesce(a._schema_placeholder,false)=false RETURN a.id AS id,a.actor_id AS actor_id,a.action AS action,a.target AS target,a.details AS details,a.ts AS ts ORDER BY a.ts DESC LIMIT 1000"))
@app.post("/api/admin/customers")
def staff_create_customer(d:RegisterIn,u=Depends(require("ADMIN","MANAGER","TELLER"))):
    if len(d.password)<8:raise HTTPException(400,"Password must be at least 8 characters")
    if d.initial_deposit<0:raise HTTPException(400,"Invalid deposit")
    cid=gen_id("CUS","Customer");salt=secrets.token_hex(16)
    def f(tx):
        if one(tx,"MATCH (c:Customer {email:$e}) RETURN c.id AS id",e=d.email.lower().strip()):raise HTTPException(400,"Email already registered")
        run(tx,"CREATE (c:Customer {id:$id,name:$name,email:$email,phone:$phone,salt:$salt,pw:$pw,role:'CUSTOMER',status:'ACTIVE',created:$now})",id=cid,name=d.name.strip(),email=d.email.lower().strip(),phone=d.phone,salt=salt,pw=hpw(d.password,salt),now=time.time())
        aid,acc=create_account_for_customer(tx,{"id":cid},d.initial_deposit)
        if d.initial_deposit>0: deposit_txn(tx,aid,u["login_id"],d.initial_deposit,"Staff-assisted opening deposit",u["id"])
        audit(tx,u["id"],"STAFF_CREATE_CUSTOMER",cid,f"Account {acc}")
        return acc
    acc=work(f);return {"ok":True,"customer_id":cid,"account_number":acc}
@app.get("/api/admin/support")
def support_list(u=Depends(require("ADMIN","MANAGER","SUPPORT"))):
    return work(lambda tx:rows(tx,"MATCH (t:SupportTicket) WHERE coalesce(t._schema_placeholder,false)=false OPTIONAL MATCH (c:Customer)-[:RAISED]->(t) RETURN t.id AS id,t.subject AS subject,t.message AS message,t.status AS status,t.created AS created,t.updated AS updated,c.id AS customer_id,c.name AS customer ORDER BY t.created DESC LIMIT 500"))
@app.post("/api/support")
def support_create(d:TicketIn,u=Depends(require("CUSTOMER"))):
    tid=uid();now=time.time()
    work(lambda tx:run(tx,"MATCH (c:Customer {id:$cid}) CREATE (t:SupportTicket {id:$id,subject:$s,message:$m,status:'OPEN',created:$now}) CREATE (c)-[:RAISED]->(t)",cid=u["id"],id=tid,s=d.subject,m=d.message,now=now))
    return {"ok":True,"ticket_id":tid}
@app.patch("/api/admin/support/{tid}")
def support_update(tid:str,d:StatusIn,u=Depends(require("ADMIN","MANAGER","SUPPORT"))):
    if d.status not in ("OPEN","IN_PROGRESS","RESOLVED","CLOSED"):raise HTTPException(400,"Invalid ticket status")
    work(lambda tx:run(tx,"MATCH (t:SupportTicket {id:$id}) SET t.status=$status,t.updated=$now,t.assigned_to=$actor,t.staff_note=$reason",id=tid,status=d.status,now=time.time(),actor=u["id"],reason=d.reason))
    return {"ok":True}
@app.get("/api/admin/graph")
def graph_schema(u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    def f(tx):
        labels=rows(tx,"CALL db.labels() YIELD label RETURN label ORDER BY label")
        rels=rows(tx,"CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
        counts=rows(tx,"MATCH (n) UNWIND labels(n) AS label RETURN label,count(*) AS nodes ORDER BY label")
        return {"labels":labels,"relationships":rels,"counts":counts}
    return work(f)
@app.get("/api/admin/roles")
def role_data(u=Depends(require("ADMIN"))):
    return [{"role":k,"description":v} for k,v in ROLES.items()]
@app.get("/api/admin/summary")
def summary(u=Depends(require("ADMIN","MANAGER","FRAUD_ANALYST"))):
    return work(lambda tx:rows(tx,"""MATCH (n) UNWIND labels(n) AS label WITH label,count(*) AS count RETURN label,count ORDER BY label"""))

app.mount("/static",StaticFiles(directory=os.path.join(BASE,"static")),name="static")
@app.get("/")
def index():return FileResponse(os.path.join(BASE,"static","index.html"))
