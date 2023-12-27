from vertexai.preview.language_models import ChatModel
from fastapi import APIRouter, Depends, Body, HTTPException
from src.env import data, get_global_params
from src.permissions import auth_required
from src.utils import get_system_template, get_system_model_params, define_chat_prompt_system
from collections import defaultdict
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from typing import Literal

router = APIRouter(prefix='/chat',tags=['chat'])

vertex_model = ChatModel.from_pretrained("chat-bison@001")
openia_model =ChatOpenAI()


ia_models = dict(openia=openia_model,vertexia=vertex_model)
conversations = defaultdict(dict)


@router.post('/conversations/{system}')
def converse(system: str, uid: str = Depends(auth_required()),prompt: str= Body(...),initialize_chat : bool = True):
    all_system = get_global_params().get('systems').__members__.keys()
    if system not in all_system:
        raise HTTPException(422, detail=f'system should be in {",".join(all_system)}')
    system_model = get_system_model_params(system)
    ia: Literal['openia','vertexia'] = system_model.get('ia')
    system_temperature =  system_model.get('temperature')
    system_max_tokens = system_model.get('max_tokens')
    if initialize_chat:
        system_template = get_system_template(system,uid)
        model_ia_user = ia_models[ia]
        if ia == 'openia':
            llm_user = ia_models['openia']
            if system_temperature is not None:
                model_ia_user.temperature = system_temperature
            if system_max_tokens is not None:
                model_ia_user.max_tokens = system_max_tokens
            if system_model.get('openia_model_name'):
                model_ia_user.model_name = system_model.get('openia_model_name')
            memory = ConversationBufferMemory(memory_key="chat_history",return_messages=True)
            system_prompt = define_chat_prompt_system(system_template)
            chat = LLMChain(
                llm=llm_user,
                prompt=system_prompt,
                verbose=True,
                memory=memory
            )
        else:
            chat = ia_models[ia].start_chat(context=system_template)
        
        conversations[uid].update({system: chat})

    if ia == 'vertexia':
        response = conversations[uid][system].send_message(prompt,temperature = system_temperature if system_temperature else None,max_output_tokens=system_max_tokens if system_max_tokens else None).text
    else:
        response = conversations[uid][system](dict(question=prompt)).get('text')
    return response