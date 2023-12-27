from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from .env import firestore_client, data
from typing import Literal, Optional
from pydantic import BaseModel
from google.cloud import storage
import os
from pathlib import Path
from datetime import datetime

storage_client = storage.Client()
destination_path = Path(__file__).parent if  not os.environ.get("GAE_INSTANCE") else '/tmp'

def define_chat_prompt_system(system_template:str):
    return ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            system_template
        ),
        # The `variable_name` here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)
    
def get_system_template(system_type,uid: str):
    system = firestore_client.collection('systems').where('name','==',system_type).get()[0].to_dict()
    personalized_template = system.get('personalization')
    template = system.get('prompt_sys')
    if personalized_template:
        user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
        system_uid = firestore_client.collection('systems').where('name','==',system_type).get()[0]
        personal_inf_doc = firestore_client.collection('chatbot-users').document(user_doc.id).collection('systems').document(system_uid.id).get().to_dict()
        variables_values = personal_inf_doc.get('keys')
        template = template.format(*tuple(variables_values))
    return template

def get_system_model_params(system_type):
    system_doc = firestore_client.collection('systems').where('name','==',system_type).get()[0].to_dict()
    return system_doc


def upload_file_to_gcs(bucket_name: Literal['systems_avatars','systems_images'], source_file):
    file_name = source_file.filename
    destination_file = os.path.join(destination_path,file_name)
    with open(destination_file,'wb') as file_obj:
        file_obj.write(source_file.file.read())
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file.filename)
    blob.upload_from_filename(destination_file)
    file_url = blob.public_url
    os.remove(destination_file)
    return file_url


def delete_file(bucket_name: Literal['systems_avatars','systems_images'],system: data.get('systems')):
    # Initialize Google Cloud Storage client
    doc_data = firestore_client.collection('systems').where('name','==',system).get()[0].to_dict()
    file_name = doc_data.get('avatar_url') if bucket_name == 'systems_avatars' else doc_data.get('image_url')
    if not file_name:
        return
    file_name = file_name.split('/')[-1]
    client = storage.Client()
    try:
        # Get the bucket
        bucket = client.bucket(bucket_name)

        # Get the blob (file) to delete
        blob = bucket.blob(file_name)

        # Delete the blob
        blob.delete()
    except Exception as ex:
        print(str(ex))
        return f"{file_name} doesn't deleted frol GCS => str(ex)"

    return f"File {file_name} deleted from bucket {bucket_name}"

def create_current_time():
    current_time = datetime.now()
    format='%Y-%m-%d %H:%M:%S'
    str_current_time = current_time.strftime(format)
    return str_current_time