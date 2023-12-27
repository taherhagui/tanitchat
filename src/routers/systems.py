from fastapi import APIRouter, Depends, Body, status,HTTPException, UploadFile, File, Query
import os
from src.env import data, firestore_client, get_global_params
from src.permissions import auth_required
from src.models.systems import System, NewSystem,UpdateSystem
from src.utils import upload_file_to_gcs, delete_file, create_current_time

router = APIRouter(prefix='/systems',tags=['systems'])

os.environ["OPENAI_API_KEY"] = data.get('openia_apikey')

conversations = dict()

@router.get('/all')
def display_systems(api=Query(True,include_in_schema=False)):
    systems_collection = firestore_client.collection('systems').get()
    if api:
        systems_doc = [System(**doc.to_dict()) for doc in systems_collection if doc.to_dict().get('draft')== False]
    else:
        systems_doc = [doc.to_dict().get('name') for doc in systems_collection]
    return systems_doc
#: str = Depends(auth_required())
@router.post('/new_system')
def add_new_global_system(new_system:NewSystem,uid: str = Depends(auth_required()),img_file: UploadFile = File(None),avatar_file: UploadFile = File(None)):
    all_systems = display_systems(api=False)
    if new_system.name in all_systems:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Oops! The name {new_system.name} that you've chosen is already taken. Please double-check and ensure that your new system doesn't overlap with any existing ones to avoid conflicts.")
    if img_file:
       img_url = upload_file_to_gcs('systems_images',img_file)
       new_system.image_url = img_url
    if avatar_file:
        avatar_url = upload_file_to_gcs('systems_avatars',avatar_file)
        new_system.avatar_url = avatar_url
    new_system.owner_id = uid
    current_time = create_current_time()
    new_system.created_at = current_time
    new_system.updated_at = current_time
    firestore_client.collection('systems').add(new_system.model_dump())
    add_sytem_to_current_user(uid,new_system.name, api=False)
    return 'New system was added succefully!'

@router.patch('/update_system/{system}')
def update_system(system:str,system_data: UpdateSystem,uid: str = Depends(auth_required()),img_file: UploadFile = File(None), avatar_file: UploadFile = File(None)):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    doc_ref =firestore_client.collection('systems').where("name","==",system).get()[0]
    doc_ref = firestore_client.collection('systems').document(doc_ref.id)
    doc_data = doc_ref.get().to_dict()
    if doc_data.get('owner_id') != uid:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE,detail=f'{system} not belong to current user systems')
    if getattr(system_data,'image_url'):
        delete_file('systems_images',system)
    if getattr(system_data,'avatar_url'):
        delete_file('systems_avatars',system)
    if img_file:
        delete_file('systems_images',system)
        img_url = upload_file_to_gcs('systems_images',img_file)
        system_data.image_url = img_url
    if avatar_file:
        delete_file('systems_avatars',system)
        avatar_url = upload_file_to_gcs('systems_avatars',avatar_file)
        system_data.avatar_url = avatar_url
    system_data.updated_at = create_current_time()
    system_data_dict = system_data.model_dump(exclude_none=True)
    doc_ref.update(system_data_dict)

    return f'{system} system has been updated succefully!'
    
@router.delete('/delete_system/{system}')
def delete_system(system:str,uid: str = Depends(auth_required())):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    system_data = UpdateSystem(is_active=False)
    update_system(system=system,uid=uid,system_data=system_data,img_file=None,avatar_file=None)
    return f'{system} system had been deactivated'

@router.get('/get_system/{system}')
def get_system_by_name(system:str,uid: str = Depends(auth_required())):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    doc_ref =firestore_client.collection('systems').where("name","==",system).get()[0]
    doc_ref = firestore_client.collection('systems').document(doc_ref.id)
    doc_data = doc_ref.get().to_dict()
    if doc_data.get('owner_id') != uid:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE,detail=f'{system} not belong to current user systems')
    return NewSystem(**doc_data)
    
    

@router.get('/current_user_all')
def display_current_user_systems(uid: str = Depends(auth_required()),api=Query(True,include_in_schema=False)):
    user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
    user_doc_ref = firestore_client.collection('chatbot-users').document(user_doc.id)
    system_collection_ref = user_doc_ref.collection('systems').get()
    current_user_systems = []
    for doc in system_collection_ref:
        system_data = firestore_client.collection('systems').document(doc.id).get()
        if api:
            current_user_systems.append(System(**system_data.to_dict()))
        else:
            current_user_systems.append(system_data.to_dict().get('name'))
    return current_user_systems

@router.post('/add_system')
def add_sytem_to_current_user(uid: str = Depends(auth_required()), system: str = Body(...), api=Query(True,include_in_schema=False)):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
    user_doc_ref = firestore_client.collection('chatbot-users').document(user_doc.id)
    system_uid = firestore_client.collection('systems').where('name','==',system).get()[0]
    check_system = user_doc_ref.collection('systems').document(system_uid.id).get()
    if check_system.exists:
        raise HTTPException(status.HTTP_409_CONFLICT,detail=f'{system} already belong to your systems list')
    doc_data = dict(keys=[])
    user_doc_ref.collection('systems').document(system_uid.id).set(doc_data)
    return f'{system} has been added to current user'

@router.delete('/delete_system/{system}')
def remove_system_to_current_user(system: str,uid: str = Depends(auth_required())):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    user_systems = display_current_user_systems(uid=uid,api=False)
    if system.value not in user_systems:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE,detail=f'{system.value} not belong to current user systems')
    user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
    sys_doc = firestore_client.collection('systems').where('name','==',system.value).get()[0]
    doc_ref = firestore_client.document(f"chatbot-users/{user_doc.id}/systems/{sys_doc.id}")
    doc_ref.delete()
    return f'{system.value} has been removed from current user systems'

@router.post('/personal_info/{system}')
def add_personal_info_of_current_user_for_given_system(system: str,uid: str = Depends(auth_required()),keys: list = Body(...)):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    user_systems = display_current_user_systems(uid=uid,api=False)
    if system not in user_systems:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE,detail=f'{system.value} not belong to current user systems')
    user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
    user_doc_ref = firestore_client.collection('chatbot-users').document(user_doc.id)
    doc_data = dict(keys=keys)
    sys_doc = firestore_client.collection('systems').where('name','==',system).get()[0]
    user_doc_ref.collection('systems').document(sys_doc.id).update(doc_data)
    return f'personal info of current user has been added to {system}'

@router.get('/personal_info/{system}')
def get_personal_info_of_current_user_for_given_system(system: str,uid='A0rIkwEq5bWVw0s8eTu7jl0SNKi1'):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    user_systems = display_current_user_systems(uid=uid,api=False)
    if system not in user_systems:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE,detail=f'{system} not belong to current user systems')
    user_doc = firestore_client.collection('chatbot-users').where('uid','==',uid).get()[0]
    user_doc_ref = firestore_client.collection('chatbot-users').document(user_doc.id)
    sys_doc = firestore_client.collection('systems').where('name','==',system).get()[0]
    personal_info_doc = user_doc_ref.collection('systems').document(sys_doc.id).get().to_dict()
    personal_info = personal_info_doc.get('keys')
    response = dict(fields= sys_doc.to_dict().get('variables'),values = personal_info)
    return response





