from typing_extensions import Optional
from requests import  Session

def get_salesforce_access_token(
    # username: str="mahesh.p@appstrail.com.appstrail-sfadev",
    # password: str="Ascii@12345rutx",
    username: str="purveesha.parmar@appstrail.com.rutx",
    password: str="Delta@2025",
    client_id: str="3MVG9FINO1nsxRuAhDRVB5PyN2t21ByCFEe9udNFIQZq8ycRt1c7gJs_RWyMaB7gOTLoO5aQbMtzp416FnHsQ",
    client_secret: str = "90AB70013803B717B6E391B2130BF3BCDD26DE399D114F40E784DC74CB164AC7",
    login_url: str = "https://login.salesforce.com/services/oauth2/token"
) -> Optional[str]:
    """
    Get a Salesforce access token using password authentication flow.
    
    Args:
        username: Salesforce username
        password: Salesforce password
        client_id: Connected App's consumer key
        client_secret: Connected App's consumer secret
        login_url: Salesforce login URL (default is production)
        
    Returns:
        Access token string if successful, None otherwise
    """
    session = Session()
    
    auth_data = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password
    }
    
    try:
        response = session.post(login_url, data=auth_data)
        response.raise_for_status()  # Raise exception for non-200 status codes
        token_data = response.json()
        return token_data.get("access_token")
    except Exception as e:
        print(f"Error getting Salesforce access token: {e}")
        return None
