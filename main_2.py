from fastapi import FastAPI, Depends, HTTPException
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
import os
import json
from datetime import datetime


app = FastAPI()

##DB接続
config = {
    "user": "tozawa92",
    "password": "Hiroya-92",  # 実際のパスワードに置き換えてください
    "host": "kurost-myaql.mysql.database.azure.com",
    "port": 3306,
    "database": "kurost-pos",  # 実際のデータベース名に置き換えてください
}


def get_db():
    try:
        db = mysql.connector.connect(**config)
        yield db
    finally:
        db.close()


##CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Items(BaseModel):
    PRD_ID: int
    PRD_CODE: str
    PRD_NAME: str
    PRD_PRICE: int


class PurchaseList(BaseModel):
    EMP_CD: str
    STORE_CD: str
    POS_NO: str
    items: List[Items]

@app.get("/products")
async def get_products(
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor()
    query = "SELECT ProductID, ProductCode, ProductName, Price FROM product_dummy"
    cursor.execute(query)
    results = cursor.fetchall()

    products = []
    for result in results:
        product_ID, product_Code, product_name, price = result
        productmaster = {
            "PRD_ID": product_ID,
            "PRD_CODE": product_Code,
            "PRD_NAME": product_name,
            "PRD_PRICE": price,
        }
        products.append(productmaster)

    return {"products": products}


@app.post("/create_purchase")
async def create_purchase(
    purchase: PurchaseList,
    db: mysql.connector.MySQLConnection = Depends(get_db),
):  # Listのアノテーションを修正
    #  [Next]一回の受け取りになるように変更
    # 1 変数受け取る
    # 2 合計金額取得
    # 3 最新のTRD_ID取得
    # 4 Transaction tableに追加
    # 5 最新のID取得
    # 6 Transactiondetail tableの更新
    # 7 return(Status, 合計金額)

    cursor = db.cursor()

    # 最新TRD_ID取得
    cursor.execute("SELECT MAX(TRD_ID) FROM transactions;")
    max_id_result = cursor.fetchone()
    if max_id_result and max_id_result[0] is not None:
        new_trd_id = max_id_result[0] + 1
    else:
        new_trd_id = 1  # テーブルが空の場合のため

    # Transaction table用
    TRD_ID = new_trd_id
    DATETIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    EMP_CD = purchase.EMP_CD
    STORE_CD = purchase.STORE_CD
    POS_NO = purchase.POS_NO
    TOTAL_AMT = sum(item.PRD_PRICE for item in purchase.items)

    # Transaction table　更新
    query = """
        INSERT INTO transactions (TRD_ID, DATETIME, EMP_CD, STORE_CD, POS_NO, TOTAL_AMT) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (TRD_ID, DATETIME, EMP_CD, STORE_CD, POS_NO, TOTAL_AMT)
    cursor.execute(query, values)

    # transactiondetails table書き込み
    for index, item in enumerate(purchase.items, 1):
        query = """
        INSERT INTO transactiondetails (TRD_ID, DTL_ID, PRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (TRD_ID, index, item.PRD_ID, item.PRD_CODE, item.PRD_NAME, item.PRD_PRICE),
        )

    db.commit()
    return {"TOTAL_AMT": TOTAL_AMT}

    # try:
    #     for purchase in purchase:
    #         cursor.execute(
    #             "INSERT INTO TransactionDetails (TRD_ID, DTL_ID, PRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE) VALUES (%s, %s, %s, %s, %s, %s)",
    #             (
    #                 detail.TRD_ID,
    #                 detail.DTL_ID,
    #                 detail.PRD_ID,
    #                 detail.PRD_CODE,
    #                 detail.PRD_NAME,
    #                 detail.PRD_PRICE,
    #             ),
    #         )
    #     db.commit()
    #     return {"status": "success", "message": "Details inserted successfully."}

    # except mysql.connector.Error as e:
    #     db.rollback()
    #     raise HTTPException(status_code=400, detail=f"MySQL Error: {e}")
