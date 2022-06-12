import os

import tweepy

AUTH_ARGS = {
    "consumer_key": os.environ['TWITTER_API_KEY'],
    "consumer_secret": os.environ['TWITTER_API_KEY_SECRET'],
    "access_token": os.environ['TWITTER_ACCESS_TOKEN'],
    "access_token_secret": os.environ['TWITTER_ACCESS_TOKEN_SECRET']
}

# API V1
api = tweepy.API(tweepy.OAuth1UserHandler(**AUTH_ARGS))

# API v2, does not handle tweet with medias
client = tweepy.Client(bearer_token=os.environ['TWITTER_BEARER_TOKEN'],
                       **AUTH_ARGS)


class TweetPostman:
    apiv1: tweepy.API
    apiv2: tweepy.Client

    def __init__(self):
        self.apiv1 = api
        self.apiv2 = client

    def post_tweet(self, text: str, medias: list[str] = None):
        if bool(os.getenv('DEBUG')):
            print("=" * 14, "Tweet of length:", len(text), "=" * 14)
            print(f"{text}")
            if medias:
                print("With medias", medias)
            print("-" * 50, "\n")
        else:
            medias_ids = []
            for image in (medias or []):
                media = self.apiv1.media_upload(filename=image)
                medias_ids.append(media.media_id_string)

            rep = self.apiv2.create_tweet(text=text, media_ids=medias_ids)

            tweet = rep.data
            tweet_id = tweet['id']
            rep = self.apiv2.create_tweet(text="Pensez-vous qu'il aurait fallu plus de votants pour ce vote ?",
                                          in_reply_to_tweet_id=tweet_id,
                                          poll_duration_minutes=60 * 24,
                                          poll_options=["Oui", "Non"])
