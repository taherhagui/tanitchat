from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.routers import systems_router, chat_router


app = FastAPI(docs_url="/", title="OpenAi ChatBoot",description="""### Api that allow to handle user prompt and provide  customized responses lavereging from OpenIA and VertexIA chatbot
        ### Notes:
        * All the api responses are in application/json format.
        """,version="1.0")
app.include_router(systems_router)
app.include_router(chat_router)
#app.include_router(user_router)

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )





    




