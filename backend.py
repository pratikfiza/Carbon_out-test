from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dbcon import get_db_connector
from sqlalchemy import select

from fastapi import FastAPI, Request, File, UploadFile, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from dbcon import get_db_connector, select, insert
from sqlalchemy import update
from pydantic import BaseModel
import uvicorn
from pydantic import BaseModel
from  werkzeug.security import check_password_hash
import uvicorn
import jwt
from datetime import datetime, timedelta
SECRET_KEY = 'secret key'

blacklisted_tokens = []


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory='templates')









class insert_customer_msg(BaseModel):
    name: str
    email: str
    message:str
    

def insert_book_data(name,email,msg):
    table, engine = get_db_connector('customer_messages')
    query = insert(table).values(name=name,email=email,msg=msg)
    engine.execute(query)

@app.post("/add_customer_msg")
def add_data(insert_data: insert_customer_msg):
    data = jsonable_encoder(insert_data)
    print(data)
    insert_book_data(data['name'],data['email'],data['message'])
    return {'success': 'Article Inserted'}





























def get_services():
    table, engine = get_db_connector('our_services')
    query = select([table.columns.service_id, table.columns.service_header, table.columns.service_body, table.columns.service_photo_path,table.columns.service_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset


@app.get('/services/{redirect_id}')
def load_home(request: Request, redirect_id):

    table, engine = get_db_connector('our_services')

    query = select([table.columns.service_header, table.columns.service_body, table.columns.service_photo_path,table.columns.service_link]).where(table.columns.service_id == redirect_id)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchone()

    service_header, service_body = resultset[0], resultset[1]
    service_photo_path, service_link = resultset[2], resultset[3]

    return templates.TemplateResponse('services.html',context={'request': request,
    'service_header': service_header, 'service_body': service_body,
    'service_photo_path': service_photo_path, 'service_link': service_link})
    





@app.get("/admin")
def home_page(request: Request):
    return templates.TemplateResponse('signup.html', context={'request': request})





class insert_student(BaseModel):
    service_heading: str
    service_text: str
    service_link:str
   



def insert_student_data(service_header, service_body,service_photo_path,service_link):
    table, engine = get_db_connector('our_services')
    query = insert(table).values(service_header=service_header,service_body=service_body,service_photo_path=service_photo_path, service_link=service_link)

    engine.execute(query)




# Add new service
@app.post("/insert_student")
def insert_student(request: Request, service_data : insert_student = Depends(), student_image:UploadFile=File(...)):
    data = jsonable_encoder(service_data)

    

    service_heading = data['service_heading']
    service_text = data['service_text']
    service_link=data['service_link']


    file_name = student_image.filename

    file_bytes = student_image.file.read()

    service_photo_path = f'assets/images/phd_students/{file_name}'

    print(service_heading,service_text,service_link,service_photo_path)

    with open('static/'+service_photo_path, 'wb') as w:
        w.write(file_bytes)

    insert_student_data( service_heading, service_text,service_link, service_photo_path)

    



class update_student(BaseModel):
    id: str
    service_heading: str
    service_text: str
    service_link:str


def update_student_data(id, service_heading,service_body,service_photo_path,service_link):
    table, engine = get_db_connector('our_services')
    query = update(table).values(service_header=service_heading,service_body=service_body,service_photo_path=service_photo_path, service_link=service_link).where(table.columns.service_id == id)

    engine.execute(query)


#  Update Service

@app.post("/update_student")
def update_student(request: Request, student_data : update_student = Depends(), student_image:UploadFile=File(...)):
    data = jsonable_encoder(student_data)

    # student_image.file.read()

    id = data['id']
    service_header = data['update_service_heading']
    service_text = data['update_service_text']

    service_link = data['update_service_link']


    file_name = student_image.filename

    file_bytes = student_image.file.read()

    service_photo_path = f'assets/images/phd_students/{file_name}'

    with open('static/'+service_photo_path, 'wb') as w:
        w.write(file_bytes)

    update_student_data(id, service_header,service_text,service_photo_path, service_link)

    








@app.get('/logout')
def logout(request: Request, token=''):

    global blacklisted_tokens
    if token:
        blacklisted_tokens.append(token)

    def check_tokens(token):
        try:
            jwt.decode(token, SECRET_KEY)
        except Exception:
            return False
        else:
            return True
    
    blacklisted_tokens = list(filter(check_tokens, blacklisted_tokens))

    return templates.TemplateResponse('signup.html', context={'request': request})


class creds(BaseModel):
    user_name: str
    password: str


@app.post('/validate_credentials')
def check_user(creds: creds):

    creds = jsonable_encoder(creds)


    table, engine = get_db_connector('admin_login1')

    query = select([table.columns.public_id, table.columns.admin_password_hashed]).where(table.columns.admin_login_id==creds['user_name']).limit(1)
    # print(query)
    resultproxy = engine.execute(query)

    db_creds = resultproxy.fetchone()
    print(db_creds)

    if creds:
        public_id, password = db_creds

        if check_password_hash(password, creds['password']):
        
            token = jwt.encode({
                'public_id': public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, SECRET_KEY)
    
            return {'success': 'User Validated', 'token': token.decode('UTF-8')}

    
    return {'error': 'Invalid Credentials'}





def get_notications():
    table, engine = get_db_connector('customer_messages')
    query = select([table.columns.id, table.columns.name, table.columns.email, table.columns.msg]).where(table.columns.is_seen == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset



@app.get('/redirect_page')
def home(request: Request,token=''):
    
    token_valid = is_valid_token(token)

    if token_valid:
        data=get_notications()
        return templates.TemplateResponse('redirect_page.html', context={'request': request, 'notification_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


    

def is_valid_token(token):

    if token in blacklisted_tokens:
        return False
        
    
    try:
        data = jwt.decode(token, SECRET_KEY)
        public_id = data['public_id']

    except Exception:
        return False

    table, engine = get_db_connector('admin_login1')
    query = select(1).where(table.columns.public_id==public_id)

    data = engine.execute(query)

    return bool(data.fetchone())

















def get_services():
    table, engine = get_db_connector('our_services')
    query = select([table.columns.service_id, table.columns.service_header, table.columns.service_body, table.columns.service_photo_path,table.columns.service_link]).where(table.columns.is_deleted == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset

@app.get("/adminservices")
def show_team(request: Request, token: str = ''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_services()

        return templates.TemplateResponse('show_students.html', context={'request': request, 'services_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})


def get_Contacts():
    table, engine = get_db_connector('customer_messages')
    query = select([table.columns.id, table.columns.name, table.columns.email, table.columns.msg]).where(table.columns.is_seen == 0)

    resultproxy = engine.execute(query)
    resultset = resultproxy.fetchall()

    return resultset



@app.get("/messages_all")
def show_team(request: Request, token: str = ''):

    token_valid = is_valid_token(token)

    if token_valid:
        data = get_Contacts()

        return templates.TemplateResponse('Show_messages.html', context={'request': request, 'services_data': data})
    else:
        return templates.TemplateResponse('invalid_token.html', context={'request': request})







# Delete Service
class delete_student(BaseModel):
    id: str

def delete_student_db(id):
    table, engine = get_db_connector('our_services')
    query = update(table).values(is_deleted = 1).where(table.columns.service_id == id)
    engine.execute(query)

@app.post("/delete_student")
def delete_student(request: Request, delete_id:delete_student):
    
    data = jsonable_encoder(delete_id)
    id = data['id']

    delete_student_db(id)
    








@app.get('/')
def load_home(request: Request):
    data = get_services()

    return templates.TemplateResponse('index.html',context={'request': request, 'services_data': data})


if __name__ == "__main__":
    uvicorn.run('backend:app', host='0.0.0.0', port=8003, reload=True)