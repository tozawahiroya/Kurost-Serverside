from fastapi import FastAPI, Request, status
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from pydantic import BaseModel  # リクエストbodyを定義するために必要
from typing import List  # ネストされたBodyを定義するために必要
from fastapi.exceptions import RequestValidationError
import json


openai.api_key = os.environ.get("OPEN_AI_KEY")
openai.api_base = os.environ.get("OPEN_AI_ENDPOINT")
openai.api_type = "azure"
openai.api_version = "2023-03-15-preview"


# 商品マスター
products_data = [
        {
            "id": 1,
            "unique_id":1111111111,
            "product_name": "おーいお茶",
            "amount": 1,
            "price": 150,
            "total_amount": 5000
        },
        {
            "id": 2,
            "unique_id":2222222222,
            "product_name": "サイダー",
            "amount": 1,
            "price": 300,
            "total_amount": 1
        },
        {
            "id": 3,
            "unique_id":3333333333,
            "product_name": "山崎ぱん",
            "amount": 1,
            "price": 100,
            "total_amount": 1
        }
        # 他の商品情報も追加できます
        ]
# リクエストbodyを定義
class ProductItem(BaseModel):
    id: int
    unique_id: int
    product_name: str
    amount: int
    price: int
    total_amount: int
# 空の配列を用意
purchaseItems = []

app = FastAPI()

# エラー確認
@app.exception_handler(RequestValidationError)
async def handler(request:Request, exc:RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

# アクセス制限解除
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://example.com"],  # 許可するフロントエンドのオリジン
    allow_origin_regex=r"^https://example-(.+)\.com$",  # 追加で許可するフロントエンドのオリジンの正規表現
    allow_credentials=True,  # 資格情報の共有の可否
    allow_methods=["*"],  # 許可するHTTPリクエストメソッド
    allow_headers=["*"],  # フロントエンドからの認可するHTTPヘッダー情報
    expose_headers=["Example-Header"],  # フロントエンドがアクセスできるHTTPヘッダー情報
)

#React側から製品データ1個ずつ受け取り、「purchaseItems」に格納
@app.post("/productcode/api")
async def product(productitem: ProductItem):
    #辞書型へ変更
    product_dict = {
        "id": productitem.id,
        "unique_id": productitem.unique_id,
        "product_name": productitem.product_name,
        "amount": productitem.amount,
        "price": productitem.price,
        "total_amount": productitem.total_amount
    }
    purchaseItems.append(product_dict)

#受け取った商品データから合計金額を計算、「purchaseItems」をリセット
@app.get("/productcode/api/{count}")
async def register_product_list(count: int):
    #DBに引き渡す処理
    # print(purchaseItems)

    #合計金額を計算
    total_price = 0
    print(len(purchaseItems))
    
    for i in range(len(purchaseItems)):
        print(total_price)
        total_price = purchaseItems[i]["price"] + total_price
    #商品リストをクリア
    del purchaseItems[:]

    return {"total_price":total_price}

#商品コードを受け取り、DBとマッチングする？
@app.get("/productcode/{number}")
async def get_products(number: int):
    # DBに繋いで処理するバージョン
    #########################
    #pending
    #########################

    # FastAPI内で処理するバージョン
    for i in range(len(products_data)):
        temp_data = products_data[i]
        product_code = temp_data["unique_id"]
        if product_code == number:
            matching_data = {"product": temp_data}
            break
    return matching_data
