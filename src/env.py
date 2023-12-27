from google.cloud import firestore
from enum import Enum


firestore_client = firestore.Client()


def get_env_params():
        return firestore_client.collection('params').get()[0].to_dict()

def get_all_systems():
        systems_docs = firestore_client.collection('systems').get()
        system_keys = {doc.to_dict().get('name'): doc.to_dict().get('name') for doc in systems_docs if doc.to_dict().get('name') is not None}
        l = len({key: key for key in system_keys if key is not None})
        if l == 0:
           return None
        return Enum(f"SystemsType", system_keys)

def get_global_params():
    data = dict()
    params = get_env_params()
    data['openia_apikey'] = params.get('openia_apikey')
    data ['systems'] = get_all_systems()
    return data

data  = get_global_params()