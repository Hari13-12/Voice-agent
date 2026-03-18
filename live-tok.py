from livekit import api
import json

def get_token():
    user_id = "005fK000001oNIbQAM"
    access_token = ""
    url = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com"
    token = api.AccessToken("APIybMjqNVgiCPd", "kShwFd8nIhU1SwGLbncqCz2B8dFkdXp1ez9j0BEmCiN") \
        .with_identity("visits-agent") \
        .with_name("Visit Agent") \
        .with_metadata(json.dumps({
            "user_id": user_id,
            "access_token": access_token,
            "url": url
        })) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="my-room"
        ))
    return token.to_jwt()


if __name__ == "__main__":
    tok = get_token()
    print(tok)