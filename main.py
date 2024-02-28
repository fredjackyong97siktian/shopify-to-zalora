from typing import Union

import os
import sys
import hmac
import hashlib
import base64
import json 
from fastapi import FastAPI, Request
from fastapi.logger import logger
from fastapi.responses import JSONResponse

from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()

class Settings(BaseSettings):
    # ... The rest of our FastAPI settings

    BASE_URL :str = "http://localhost:8000"
    USE_NGROK : bool = os.getenv("USE_NGROK", "False") == "True"


settings = Settings()


def init_webhooks(base_url):
    # Update inbound traffic via APIs to use the public-facing ngrok URL
    pass


# Initialize the FastAPI app for a simple web server
app = FastAPI()

if settings.USE_NGROK and os.environ.get("NGROK_AUTHTOKEN"):
    # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
    from pyngrok import ngrok

    # Get the dev server port (defaults to 8000 for Uvicorn, can be overridden with `--port`
    # when starting the server
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8000"

    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(port).public_url
    logger.info(f"ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:{port}\")")

    # Update any base URLs or webhooks to use the public ngrok URL
    settings.BASE_URL = public_url
    init_webhooks(public_url)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items")
def read_item(request: Request):
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        str(request.method) + ' ' + str(request.url),
        '\r\n'.join('{}: {}'.format(k, v) for k, v in request.headers.items()),
        request.body,
    ))
    return {"item_id": "Checked Successful."}


def verify_webhook(data, hmac_header):
    CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET")
    digest = hmac.new(CLIENT_SECRET.encode('utf-8'), data, digestmod=hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

@app.post("/webhook/sync/zalora")
async def read_item(request: Request):
    # try:
    content = await request.body()
    verified = verify_webhook(content, request.headers.get('x-shopify-hmac-sha256'))
    
    # print(content)
    # print(verified)
    
    # if not verified:
    #     return {"status": "fail"}
    
    # data = json.loads(content.decode('utf-8'))

    # name = data['title']
    # SKU_supplier = data['variants'][0]['sku'] #recheck
    # sub_cat_type="Dresses"
    # size_system="International"
    # gender="female"
    # care_label=""
    # description= data['body_html']
    # price_myr=data['variants'][0]['price'] * 0.7
    # price_sgd=data['variants'][0]['price'] * 0.7 / 2.5
    # weight=data['variants'][0]['weight']
    # size="One Size"
    # image=""
    # color_english= data['title'].split("-")[0:2]
    # color_family= ""#empty
    # primary_category= "Dresses" 
    # browse_node = "Ethnic Wear"
    # # {"admin_graphql_api_id":"gid:\\/\\/shopify\\/Product\\/9061736284459","body_html":"just testing from Yong","created_at":"2024-02-28T01:19:44+08:00","handle":"product-for-testing","id":9061736284459,"product_type":"","published_at":null,"template_suffix":"","title":"product for testing","updated_at":"2024-02-28T01:19:45+08:00","vendor":"Yeshan Sarees","status":"draft","published_scope":"web","tags":"","variants":[{"admin_graphql_api_id":"gid:\\/\\/shopify\\/ProductVariant\\/48044834357547","barcode":null,"compare_at_price":null,"created_at":"2024-02-28T01:19:44+08:00","fulfillment_service":"manual","id":48044834357547,"inventory_management":null,"inventory_policy":"deny","position":1,"price":"0.00","product_id":9061736284459,"sku":"","taxable":true,"title":"l","updated_at":"2024-02-28T01:19:45+08:00","option1":"l","option2":null,"option3":null,"grams":0,"image_id":null,"weight":0.0,"weight_unit":"kg","inventory_item_id":50096477110571,"inventory_quantity":0,"old_inventory_quantity":0,"requires_shipping":true}],"options":[{"name":"Size","id":11406870708523,"product_id":9061736284459,"position":1,"values":["l"]}],"images":[],"image":null,"variant_ids":[{"id":48044834357547}]}
    # # {"admin_graphql_api_id":"gid:\\/\\/shopify\\/Product\\/9061825446187","body_html":"halllo","created_at":"2024-02-28T02:15:06+08:00","handle":"another-testing-from-yong","id":9061825446187,"product_type":"","published_at":null,"template_suffix":"","title":"another testing from Yong","updated_at":"2024-02-28T02:15:07+08:00","vendor":"Yeshan Sarees","status":"draft","published_scope":"web","tags":"","variants":[{"admin_graphql_api_id":"gid:\\/\\/shopify\\/ProductVariant\\/48044935479595","barcode":"","compare_at_price":null,"created_at":"2024-02-28T02:15:07+08:00","fulfillment_service":"manual","id":48044935479595,"inventory_management":"shopify","inventory_policy":"deny","position":2,"price":"2.00","product_id":9061825446187,"sku":"","taxable":true,"title":"Default Title","updated_at":"2024-02-28T02:15:07+08:00","option1":"Default Title","option2":null,"option3":null,"grams":0,"image_id":null,"weight":0.0,"weight_unit":"kg","inventory_item_id":50096578167083,"inventory_quantity":0,"old_inventory_quantity":0,"requires_shipping":true}],"options":[{"name":"Title","id":11406974845227,"product_id":9061825446187,"position":1,"values":["Default Title"]}],"images":[],"image":null,"variant_ids":[{"id":48044935479595}]}


    # # Create product in Zalora - https://sellercenter-api.zalora.com.my/docs/#/Product/post_v2_product_set__productSetId__products
    # zalora_instance = ""
    # product_set_id = '"'
    # zalora_url=f'https://sellercenter-api.{zalora_instance}/v2/product-set/{product_set_id}/products'


    return {"status": "success"}
    # except:
    #     return {"status": "exception fail"}
