import requests

CHESS_API_URL = "https://api.chess.com/pub/player/dextre4/stats"

def fetch_stats():
    # Adding a User-Agent is mandatory for Chess.com
    headers = {
        "User-Agent": "MyChessApp/1.0 (Contact: your-email@example.com)"
    }
    
    try:
        # Pass the headers into the get request
        response = requests.get(CHESS_API_URL, headers=headers, timeout=5)

        if response.status_code != 200:
            # Printing the status code here helps you debug in the terminal
            print(f"Error: Chess.com returned status {response.status_code}")
            raise Exception("Chess API failure")

        data = response.json()

        return {
            "blitz": data.get("chess_blitz", {}).get("last", {}).get("rating"),
            "rapid": data.get("chess_rapid", {}).get("last", {}).get("rating"),
            "bullet": data.get("chess_bullet", {}).get("last", {}).get("rating"),
        }
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        raise Exception("Failed to connect to Chess.com")