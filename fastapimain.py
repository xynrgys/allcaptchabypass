from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from supabase import create_client, Client
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import os
import stripe
import tweepy
from datetime import datetime, timezone

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="YOUR_SESSION_SECRET")

# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Stripe setup
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

# OAuth setup
config = Config('.env')
oauth = OAuth(config)
oauth.register(
    name='twitter',
    client_id='YOUR_TWITTER_CLIENT_ID',
    client_secret='YOUR_TWITTER_CLIENT_SECRET',
    access_token_url='https://api.twitter.com/2/oauth2/token',
    access_token_params=None,
    authorize_url='https://twitter.com/i/oauth2/authorize',
    authorize_params=None,
    api_base_url='https://api.twitter.com/2/',
    client_kwargs={'scope': 'tweet.read tweet.write users.read'},
)

class User(BaseModel):
    twitter_id: str
    access_token: str
    refresh_token: str
    credits: int = 0

# ... (keep the login, auth, and dashboard routes from the previous example)

@app.post('/create-checkout-session')
async def create_checkout_session(request: Request):
    user_id = request.session.get('user')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 1000,  # $10.00
                        'product_data': {
                            'name': '100 Credits',
                            'description': '100 credits for tweet deletion',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url='https://yourapp.com/success',
            cancel_url='https://yourapp.com/cancel',
            client_reference_id=user_id,
        )
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/webhook')
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail='Invalid payload')
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail='Invalid signature')

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve the user from the client_reference_id
        user_id = session.get('client_reference_id')
        if not user_id:
            raise HTTPException(status_code=400, detail='No user ID provided')

        # Add credits to the user's account
        result = supabase.table('users').select('credits').eq('twitter_id', user_id).execute()
        if len(result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_credits = result.data[0]['credits']
        new_credits = current_credits + 100  # Assuming 100 credits per purchase
        supabase.table('users').update({'credits': new_credits}).eq('twitter_id', user_id).execute()

    return Response(status_code=200)

@app.post('/delete_oldest_tweets')
async def delete_oldest_tweets(request: Request, number_to_delete: int):
    user_id = request.session.get('user')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = supabase.table('users').select('*').eq('twitter_id', user_id).execute()
    if len(result.data) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = result.data[0]
    if user['credits'] < number_to_delete:
        raise HTTPException(status_code=402, detail="Not enough credits")

    # Set up Tweepy client with user's access token
    client = tweepy.Client(
        consumer_key=os.environ.get("TWITTER_CONSUMER_KEY"),
        consumer_secret=os.environ.get("TWITTER_CONSUMER_SECRET"),
        access_token=user['access_token'],
        access_token_secret=user['refresh_token']  # Note: In OAuth 2.0, this would be handled differently
    )

    deleted_tweets = 0
    pagination_token = None

    while deleted_tweets < number_to_delete:
        try:
            # Fetch user's tweets
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=100,  # Adjust as needed, max is 100
                pagination_token=pagination_token,
                tweet_fields=['created_at']
            )

            if not tweets.data:
                break  # No more tweets to delete

            # Sort tweets by creation date
            sorted_tweets = sorted(tweets.data, key=lambda x: x.created_at)

            for tweet in sorted_tweets:
                if deleted_tweets >= number_to_delete:
                    break

                try:
                    client.delete_tweet(tweet.id)
                    deleted_tweets += 1
                except tweepy.TweepError as e:
                    print(f"Error deleting tweet {tweet.id}: {str(e)}")

            # Prepare for next page of results
            pagination_token = tweets.meta.get('next_token')
            if not pagination_token:
                break  # No more pages

        except tweepy.TweepError as e:
            raise HTTPException(status_code=500, detail=f"Twitter API error: {str(e)}")

    # Update credits
    new_credits = user['credits'] - deleted_tweets
    supabase.table('users').update({'credits': new_credits}).eq('twitter_id', user_id).execute()

    return {"message": f"Deleted {deleted_tweets} tweets. Remaining credits: {new_credits}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)