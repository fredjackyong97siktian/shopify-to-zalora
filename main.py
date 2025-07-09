import os
import sys
import hmac
import hashlib
import base64
import json 
import requests
import time
import asyncio

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.logger import logger
from base64 import b64encode
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

@app.get("/", status_code=200)
async def read_root():
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

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'

async def add_data(request : requests):
    try:
        content = await request.body()
        verified = verify_webhook(content, request.headers.get('x-shopify-hmac-sha256'))

        # If it is not verified
        if not verified:
            return {"status": "fail"}
    
        print("receive data")
        #time.sleep(5)
        await asyncio.sleep(5)
        print("wakeup")
        ###  SHOPIFY  ###
        data = json.loads(content.decode('utf-8'))
        print(data['id'])

        #print(data)
        inventory_stock = []
        SHOPIFY_ACCESS_TOKEN=os.environ.get("SHOPIFY_ACCESS_TOKEN")
        SHOPIFY_NAME = os.environ.get("SHOPIFY_NAME")
        SHOPIFY_URL_GET_PRODUCT = f"https://{SHOPIFY_NAME}.myshopify.com/admin/api/2024-01/products/{data['id']}.json"
        product = requests.get(SHOPIFY_URL_GET_PRODUCT,headers={"Content-Type":"application/json","X-Shopify-Access-Token":SHOPIFY_ACCESS_TOKEN})
        product = json.loads(product.content.decode('utf-8'))['product']
        
        if product['variants'][0]['sku'] == '':
            print("SKU is empty")
            return {"status": "fail", "reason": "SKU is empty"}
            
        print("Calling Shopify URL Product")
        # print(product_images)
        print("-----------------------")
        # JSON content
        name = product['title'] 
        description= product['body_html'].replace('"','\"').replace("\xa0","").replace("\n","") #/
        price_myr_label = "67"
        SKU_supplier = product['variants'][0]['sku'] 
        price_myr=round(float(product['variants'][0]['price']) * 1.07,2)#/
        price_sgd=round(float(product['variants'][0]['price']) * 1.07 / 2.5 ,2)#/
        price_sgd_label = "64"
        weight_label="315"
        weight=float(product['variants'][0]['weight'])
        color_english_label= "20"
        title_split = name.split(" ")
        color_english = title_split[0] 

        brandId = 17802 
        sub_cat_type_label="103"
        sub_cat_type= 604 #"Dresses"
        size_system_label="186"
        size_system= 1630 # "International"
        gender_label = "39"
        gender= 417 #"female"
        official_label="299"
        official=False
        fragile_label ="321"
        fragile=False
        price_status_sg_label = "323"
        price_status_sg=15171550
        price_status_myr_label= "324"
        price_status_myr=15171552
        primary_category= 242 #"Dresses" 
        browse_node = 2160 # "Ethnic Wear"
        care_label_label = "11"
        care_label = "<ul><li>Prefer Dry Clean.</li><li>Cold dip wash.</li><li>Expect embroidery irregularities.</li><li>Turn inside out for washing. Handlooms may have variations.</li><li>Block prints may vary.</li></ul>"
        skusupplierconfig_label = "96"
        print("Done Assignment")
        # Get Images from Shopify
        print(data['id'])
        shopify_product_id=data['id']
        SHOPIFY_URL_GET_IMAGES = f"https://{SHOPIFY_NAME}.myshopify.com/admin/api/2024-01/products/{shopify_product_id}/images.json"

        # Call Shopify API to get Image
        product_images = requests.get(SHOPIFY_URL_GET_IMAGES,headers={"Content-Type":"application/json","X-Shopify-Access-Token":SHOPIFY_ACCESS_TOKEN})
        product_images = json.loads(product_images.content.decode('utf-8'))
        print("Calling Shopify URL Images")
        # print(product_images)
        print("-----------------------")

        SHOPIFY_URL_GET_VARIANTS= f"https://{SHOPIFY_NAME}.myshopify.com/admin/api/2024-01/products/{shopify_product_id}/variants.json"
        variants =  requests.get(SHOPIFY_URL_GET_VARIANTS,headers={"Content-Type":"application/json","X-Shopify-Access-Token":SHOPIFY_ACCESS_TOKEN})
        variants = json.loads(variants.content.decode('utf-8'))['variants']
        variants = sorted(variants,key=lambda x:x['position'])
        if len(variants) == 1:
            variation = "one size"
            quantity = variants[0]['inventory_quantity']
        elif variants[0]['title'].lower() == "x-small":
            quantity = variants[0]['inventory_quantity']
            variation = "XS"
        elif variants[0]['title'].lower() == "small":
            quantity = variants[0]['inventory_quantity']
            variation = "S"
        elif variants[0]['title'].lower() == "medium":
            quantity = variants[0]['inventory_quantity']
            variation = "M"
        elif variants[0]['title'].lower() == "large":
            quantity = variants[0]['inventory_quantity']
            variation = "L"
        elif variants[0]['title'].lower() == "x-large":
            quantity = variants[0]['inventory_quantity']
            variation = "XL"
        elif variants[0]['title'].lower() == "xx-large":
            quantity = variants[0]['inventory_quantity']
            variation = "XXL"

        print("Calling Shopify URL Product Variants")
        print("-----------------------")
        ###  ZALORA  ###
        ZALORA_URL_PREFIX = "https://sellercenter-api.zalora.com/v2"

        # OAUTH
        ZALORA_APP_ID = os.environ.get("ZALORA_APP_ID")
        ZALORA_APP_SECRET = os.environ.get("ZALORA_APP_SECRET")
        headers = { 'Authorization' : basic_auth(ZALORA_APP_ID, ZALORA_APP_SECRET) }
        payload = { 'grant_type': 'client_credentials'}
        ZALORA_OAUTH_URL = "https://sellercenter.zalora.com/oauth/client-credentials"
        oauth_creation =   requests.post(ZALORA_OAUTH_URL,data=payload, headers=headers)
        print("Calling ZALORA OAUTH")
        # print(oauth_creation.content)
        print("-----------------------")
        oauth_creation = json.loads(oauth_creation.content)
        ZALORA_ACCESS_TOKEN=oauth_creation['access_token']

        # Create ProductSet
        ZALORA_PRODUCTSET_URL = f"{ZALORA_URL_PREFIX}/product-set"
        ZALORA_PRODUCTSET_URL_BODY = {
            "name": name,
            "price" : price_myr,
            "sellerSku":SKU_supplier,
            "parentSku":SKU_supplier,
            "description" :description,
            "brandId":brandId,
            "primaryCategoryId":primary_category,
            "browseNodes":[browse_node],
            "attributes":{
                care_label_label : care_label,
                size_system_label: size_system ,
                color_english_label : color_english,
                gender_label : gender,
                price_myr_label : price_myr,
                price_sgd_label : price_sgd,
                sub_cat_type_label : sub_cat_type,
                official_label: official,
                fragile_label: fragile,
                price_status_sg_label : price_status_sg,
                price_status_myr_label:price_status_myr,
                weight_label:weight,
                skusupplierconfig_label:SKU_supplier
            },
            "size_system":size_system,
            "variation": variation
        }
        #print(ZALORA_PRODUCTSET_URL_BODY)
        productset_creation =   requests.post(ZALORA_PRODUCTSET_URL, json = ZALORA_PRODUCTSET_URL_BODY, headers={
            "accept":"application/json",
            "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
        })
        print("Product Creation")
        print(productset_creation.content)
        print("-----------------------")
        productset_creation = json.loads(productset_creation.content)
        try:
            productset_id = productset_creation['id']
        except:
            return {"status":"fail", "message":productset_creation['detail']}
        #Get Variation

        product_first_variation_fetch = f"{ZALORA_URL_PREFIX}/product-set/{productset_id}/products"
        product_first_variation_fetch_creation =  requests.get(product_first_variation_fetch, headers={
            "accept":"application/json",
            "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
        })
        print("Product Fetch 1st Variation")
        print(product_first_variation_fetch_creation.content)

        inventory_stock.append({
            "productId": json.loads(product_first_variation_fetch_creation.content)[0]['id'],
            "quantity" : quantity
        })                  

        print("-----------------------")

        if len(variants) > 1:
            i = 1
            for v in variants:
                if v['title'].lower() == variants[0]['title'].lower():
                    continue

                if v['title'].lower() == "x-small":
                    size = "XS"
                elif v['title'].lower() == "small":
                    size = "S"
                elif v['title'].lower() == "medium":
                    size = "M"
                elif v['title'].lower() == "large":
                    size = "L"
                elif v['title'].lower() == "x-large":
                    size = "XL"
                elif v['title'].lower() == "xx-large":
                    size = "XXL"
                else:
                    size = "XS"

                v_quantity = v['inventory_quantity']

                variant_payload = {
                    "sellerSku": SKU_supplier+"-"+str(i),
                    "status": "active",
                    "variation": size,
                }
                ZALORA_PRODUCTSET_PRODUCT_URL = f"{ZALORA_URL_PREFIX}/product-set/{productset_id}/products"

                productset_product_creation = requests.post(ZALORA_PRODUCTSET_PRODUCT_URL, json = variant_payload, headers={
                    "accept":"application/json",
                    "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
                })

                inventory_stock.append({
                    "productId": json.loads(productset_product_creation.content)['id'],
                    "quantity" : v_quantity
                })
                i = i + 1
            print("Product Sub")
            print("-----------------------")

            print("Update Browse Node")
            product_productset_update_browse_node_url = f"{ZALORA_URL_PREFIX}/product-set/{productset_id}"
            browse_node_payload = {"browseNodes": [
                                        browse_node
                                    ]}
            product_productset_update = requests.put(product_productset_update_browse_node_url, json=browse_node_payload,headers={
                    "Content-Type": "application/json",
                    "accept":"application/json",
                    "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
                })
            print(product_productset_update.content)
            print("-----------------------")

        print(inventory_stock)

        # Import from Shopify Image to Zalora
        product_stock = requests.put(f"{ZALORA_URL_PREFIX}/stock/product",json=inventory_stock,headers={
            "accept":"application/json",
            "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
        })
        
        print("Update Stock Quantity")
        print(product_stock.content)
        print("-----------------------")
        position = 1
        ZALORA_PRODUCTSET_IMAGE_URL = f"{ZALORA_URL_PREFIX}/product-set/{productset_id}/images"
        print(f"Insert total images: {len(product_images['images'])}")
        for image in product_images['images']:
            print(f"Inserting: {image}")
            data = {
                "position": position,
                "displayUrl": image['src'] + '&width=762',
                "overwrite": False
                }
            productset_img_creation = requests.post(ZALORA_PRODUCTSET_IMAGE_URL, json = data, headers={
                "accept":"application/json",
                "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
            })
            print(productset_img_creation.status_code)
            if productset_img_creation.status_code != 201 or productset_img_creation.status_code != 200:
                print(productset_img_creation.content)
                #await asyncio.sleep(5)
                productset_img_creation = requests.post(ZALORA_PRODUCTSET_IMAGE_URL, json = data, headers={
                    "accept":"application/json",
                    "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
                })
                if productset_img_creation.status_code != 201 or productset_img_creation.status_code != 200:
                    message = message + f" Position {position} Image is not uploaded.\n"
                    print(message)
            position = position + 1
            await asyncio.sleep(2)
        print("Productset image upload")
        # Check Zalora content score
        ZALORA_PRODUCTSET_CONTENTSCORE_URL = f"{ZALORA_URL_PREFIX}/content-score/product-set/{productset_id}"
        product_check = requests.get(ZALORA_PRODUCTSET_CONTENTSCORE_URL,headers={
                        "accept":"application/json",
                        "Authorization": f"Bearer {ZALORA_ACCESS_TOKEN}"
                    })
        score = json.loads(product_check.content)["score"]
        print(score)
        print("Score recorded")
    except Exception as e:
        print(e)

@app.post("/webhook/sync/zalora", status_code=200)
def read_item(request: Request):
    asyncio.run(add_data(request))
    return {"status": "success", "message":"receive data"}

