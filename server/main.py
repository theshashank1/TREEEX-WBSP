from fastapi import FastAPI
from server.api import webhooks


app = FastAPI()

app.include_router(webhooks.router)

if __name__ == "__main__":
    import uvicorn
<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
    uvicorn.run(app, host="0.0.0.0", port=8000, reload = True)