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
    PURCHASE_PRICE: int
    quantity: int


class DeliveryList(BaseModel):
    STORE_CD: str
    items: List[Items]


@app.get("/products")
async def get_products(db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor()
    query = "SELECT ProductID, ProductCode, ProductName, Price FROM productmaster"
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


# @app.get("/productcode/{number}")
# async def product_test(
#     number: int, db: mysql.connector.MySQLConnection = Depends(get_db)
# ):
#     cursor = db.cursor()
#     productCode_to_search = number
#     query = (
#         "SELECT ProductID, ProductName, Price FROM ProductMaster WHERE ProductCode = %s"
#     )
#     cursor.execute(query, (productCode_to_search,))
#     result = cursor.fetchall()

#     if result:
#         product_ID, product_name, price = result[0]
#         singleproduct = {
#             "PRD_ID": product_ID,
#             "PRD_NAME": product_name,
#             "PRD_PRICE": price,
#         }
#         # singleproduct_json = json.dumps(singleproduct, ensure_ascii=False, indent=4)
#         return singleproduct
#     else:
#         return {}


@app.post("/create_delivery")
async def create_delivery(
    delivery: DeliveryList,
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
    cursor.execute("SELECT MAX(DLV_ID) FROM deliveries;")
    max_id_result = cursor.fetchone()
    if max_id_result and max_id_result[0] is not None:
        new_trd_id = max_id_result[0] + 1
    else:
        new_trd_id = 1  # テーブルが空の場合のため

    # Transaction table用
    DLV_ID = new_trd_id
    DATETIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    STORE_CD = delivery.STORE_CD

    # Transaction table　更新
    query = """
        INSERT INTO deliveries (DLV_ID, DATETIME, STORE_CD) 
        VALUES (%s, %s, %s)
    """
    values = (DLV_ID, DATETIME, STORE_CD)
    cursor.execute(query, values)

    # transactiondetails table書き込み

    for index, item in enumerate(delivery.items, 1):
        query = """
        INSERT INTO deliverydetails (DLV_ID, DDV_ID, PRD_ID, PRD_CODE, PRD_NAME, PURCHASE_PRICE, quantity)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                DLV_ID,
                index,
                item.PRD_ID,
                item.PRD_CODE,
                item.PRD_NAME,
                item.PURCHASE_PRICE,
                item.quantity,
            ),
        )

    db.commit()
    return {"TOTAL_AMT": 1111}

    # try:
    #     fordelivery indelivery:
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
