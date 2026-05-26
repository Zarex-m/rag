from typing import Any

def ok(data:Any=None,message:str="Success")->dict:
    return{
        "success":True,
        "code":"ok",
        "message":message,
        "data":data
    }
    
def fail(message:str="An error occurred",code:str="error",data:Any=None)->dict:
    return{
        "success":False,
        "code":code,
        "message":message,
        "data":data
    }
