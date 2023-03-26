from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from data_collection import populate_commits_table, populate_repositories_table
import asyncpg

import log

app = FastAPI()

LOG = log.get_logger(__name__)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>gh-livetracker</title>
    </head>
    <body>
        <h1>Github Livetracker</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Search</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        keyword = await websocket.receive_text()
        LOG.info(f"Got new keyword: {keyword}")
        await populate_repositories_table(keyword)
        await populate_commits_table(keyword)
        new_reps_query = """
            SELECT r.repo_name FROM repositories r
            WHERE r.keyword = $1
            ORDER BY r.created_at DESC
            LIMIT 5
        """
        top_reps_query = """
            SELECT c.REPO_NAME, count(c.REPO_ID) AS commit_count FROM COMMITS C
            WHERE c.keyword = $1
            GROUP BY c.REPO_ID, c.REPO_NAME 
            ORDER BY commit_count DESC
            LIMIT 5
        """
        conn = await asyncpg.connect("postgres://docker:docker@postgres:5432/docker")
        
        repo_rows = await conn.fetch(new_reps_query, (keyword))
        commit_rows = await conn.fetch(top_reps_query, (keyword))
        new_reps = [dict(row).get("repo_name") for row in repo_rows]
        top_reps = [dict(row).get("repo_name") for row in commit_rows]
        LOG.info(f"FETCHED REPO ROWS: {new_reps}")
        LOG.info(f"FETCHED COMMIT ROWS: {top_reps}")
        await websocket.send_text(f"New reps for keyword {keyword}: {new_reps}")
        await websocket.send_text(f"Top reps for keyword {keyword}: {top_reps}")
