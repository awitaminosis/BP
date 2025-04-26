import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Response
import pyairtable
import traceback
from pyairtable import Api
from decouple import config
import time
from pydantic import BaseModel
from typing import Annotated


app = FastAPI()
security = HTTPBasic()

class BP(BaseModel):
    p_upper: int
    p_lower: int
    heart_beat_rate: int
    comment: str | None = None
    date: str
    time: str


def get_airtable():
    api = Api(config('AIRTABLE_API_KEY'))
    table = api.table(config('AIRTABLE_BASE'), config('AIRTABLE_TABLE'))
    return table


def add_record(date='2025-04-02', p_upper=130.0, p_lower=84.0, rate=102.0, time='19:00', comment=''):
    table = get_airtable()
    table.create(
        {
         'Date': date,
         'P_upper': p_upper,
         'P_lower': p_lower,
         'Heart_beat_rate': rate,
         'Time': time,
         'Notes': comment
        }
    )


def get_records():
    try:
        table = get_airtable()
        result = table.all(sort=["Date"])
    except Exception as e:
        print(traceback.format_exc())
    return result


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    allowed_login = config('AUTH_LOGIN')
    allowed_password = config('AUTH_PASSWORD')
    config('AIRTABLE_API_KEY')
    if credentials.username != allowed_login or credentials.password != allowed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.post('/add')
def add(form_data: Annotated [BP, Form()], username: str = Depends(authenticate)):
    date = form_data.date
    p_upper = form_data.p_upper
    p_lower = form_data.p_lower
    rate = form_data.heart_beat_rate
    comment = form_data.comment
    time = form_data.time
    add_record(date=date, p_upper=p_upper, p_lower=p_lower, rate=rate, time=time, comment=comment)
    return {'added':'ok'}


@app.get('/',response_class=HTMLResponse)
def root(username: str = Depends(authenticate)) -> HTMLResponse:
    records = get_records()
    old_data = '<h1>Старые данные</h1>'
    for record in records:
        date = record['fields'].get('Date','')
        time_ = record['fields'].get('Time','')
        p_upper = record['fields'].get('P_upper','')
        p_lower = record['fields'].get('P_lower','')
        hr = record['fields'].get('Heart_beat_rate','')
        notes = record['fields'].get('Notes','')
        if p_upper and p_lower and hr:
            old_data += f'''<div class="row">
                    <div><b>{date} {time_}</b> <b>{p_upper}</b> / <b>{p_lower}</b>. {hr}. {notes}</div>
                </div>'''

    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BP Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        form {
            max-width: 400px;
            margin: 0 auto;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            margin-bottom: 15px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
''' + old_data + '''
    <h1>Новые данные</h1>
    <form action="/add" method="POST" enctype="application/json">
        <!-- p_upper field -->
        <label for="date">Date:</label>
        <input id="date" name="date" required placeholder="2025-04-01" value="2025-04-01">
        <label for="time">Time:</label>
        <input id="time" name="time" required placeholder="19:00" value="19:00">
        <br>
        <br>
        <!-- p_upper field -->
        <label for="p_upper">Upper Blood Pressure:</label>
        <input id="p_upper" name="p_upper" required placeholder="Enter upper BP value" value="120">

        <!-- p_lower field -->
        <label for="p_lower">Lower Blood Pressure:</label>
        <input id="p_lower" name="p_lower" required placeholder="Enter lower BP value" value="80">

        <!-- heart_beat_rate field -->
        <label for="heart_beat_rate">Heart Beat Rate:</label>
        <input  id="heart_beat_rate" name="heart_beat_rate" required placeholder="Enter heart beat rate" value="80">

        <!-- comment field -->
        <label for="comment">Comment:</label>
        <textarea id="comment" name="comment" rows="4" placeholder="Optional comment"></textarea>

        <!-- Submit button -->
        <button type="submit">Submit</button>
    </form>
    
    <script>
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        document.getElementById('time').value=`${hours}:${minutes}`;
        
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0'); // Months are zero-based
        const day = String(now.getDate()).padStart(2, '0');
        document.getElementById('date').value=`${year}-${month}-${day}`;
    </script>
</body>
</html>    
    '''
    return html


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
