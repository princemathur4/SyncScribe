import uvicorn
from dotenv import load_dotenv

load_dotenv()

from modules.application import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)