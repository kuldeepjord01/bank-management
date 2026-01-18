from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from supabase import create_client


db_url = "https://cujtcsptszocpxbogbzn.supabase.co"
db_key = "sb_publishable_U8TJ3usJyNH64THobkXDzw_v4NSpXyb"


db = create_client(db_url, db_key)
   
app = FastAPI(title="Royal Bank")

# ---------- MODELS ----------

class AccountCreate(BaseModel):
    account_no: int
    username: str
    balance: int


class TransactionCreate(BaseModel):
    source: int
    dest: int
    amount: int


# ---------- ACCOUNTS ----------

@app.get("/accounts")
def get_accounts():
    return db.table("Accounts").select("*").execute().data


@app.post("/accounts", status_code=201)
def create_account(account: AccountCreate):

    exists = db.table("Accounts") \
        .select("account_no") \
        .eq("account_no", account.account_no) \
        .execute()

    if exists.data:
        raise HTTPException(400, "Account already exists")

    db.table("Accounts").insert({
        "account_no": account.account_no,
        "username": account.username,
        "balance": account.balance
    }).execute()

    return {"message": "Account created"}


# ---------- TRANSACTIONS ----------

@app.get("/transactions")
def get_transactions():
    return db.table("Transection").select("*").execute().data


@app.post("/transactions", status_code=201)
def transfer(tx: TransactionCreate):

    src = db.table("Accounts").select("*").eq("account_no", tx.source).execute()
    dest = db.table("Accounts").select("*").eq("account_no", tx.dest).execute()

    if not src.data:
        raise HTTPException(404, "Source account not found")
    if not dest.data:
        raise HTTPException(404, "Destination account not found")

    src_balance = float(src.data[0]["balance"])
    dest_balance = float(dest.data[0]["balance"])

    if src_balance < tx.amount:
        raise HTTPException(400, "Insufficient balance")

    # update balances
    db.table("Accounts").update({
        "balance": src_balance - tx.amount
    }).eq("account_no", tx.source).execute()

    db.table("Accounts").update({
        "balance": dest_balance + tx.amount
    }).eq("account_no", tx.dest).execute()

    # log transactions
    db.table("Transection").insert([
        {"account_no": tx.source, "amount": tx.amount, "type": "debit"},
        {"account_no": tx.dest, "amount": tx.amount, "type": "credit"}
    ]).execute()

    return {"message": "Transfer successful"}

