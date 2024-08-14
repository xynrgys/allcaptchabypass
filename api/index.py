from fastapi import FastAPI, HTTPException
from googleIndexing import extract
from bcrypt import hashpw, gensalt, checkpw
from urllib import parse
from supabase import create_client, Client
import os

app = FastAPI()

supabaseUrl: str = os.environ.get("SUPABASE_URL")
supabaseKey: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabaseUrl, supabaseKey)

def getUserIdFromApiKey(apiKey: str):
    # Hash the provided API key
    hashed_key = hashpw(apiKey.encode(), gensalt())

    # Retrieve user_id from the api_keys table using the hashed API key
    data = supabase.table('api_keys').select('user_id').eq('hashed_key', hashed_key).execute()

    if data.status_code == 200 and data.data:
        return data.data[0]['user_id']
    else:
        return None


def retrieveApiKeyfromSupabase(user_id: str):
    # Retrieve API Key from Supabase
    data = supabase.table('api_keys').select('hashed_key').eq('user_id', user_id).execute()
    if data.status_code == 200 and data.data:
        return data.data[0]['hashed_key']
    else:
        return None

def addCountToApiKey(user_id: str, count: int):
    # Add count to API Key
    supabase.table('api_keys').update({'used_calls': supabase.func.count('used_calls') + count}).eq('user_id', user_id).execute()


@app.get("/api/python")
def hello_world():
    return {"message": "Hello World, supabase connected"}

@app.get("/api/python/google/")
async def google_indexing(keyword: str, apiKey: str):
    user_id = getUserIdFromApiKey(apiKey)

    if user_id:
        hashed_key = retrieveApiKeyfromSupabase(user_id)

        if hashed_key and checkpw(apiKey.encode(), hashed_key.encode()):
            encode_query = parse.urlencode({'q': keyword, 'oq': keyword})
            url = 'https://www.google.com/search?{}aqs=chrome.0.69i59j0l8.940j0j9&sourceid=chrome&ie=UTF-8'.format(encode_query)
            output = extract(keyword, url)
            if output.status == "Success":
                addCountToApiKey(user_id, 1)
                return output
            else:
                return {"message": "Error"}
        else:
            raise HTTPException(status_code=401, detail="Invalid API Key")
    else:
        raise HTTPException(status_code=401, detail="user_id not found")

