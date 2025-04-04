import json
def createMessage(type:str, payload:str, reply_flag:bool):
	message = {
		"type": type,
		"data": payload,
		"reply_required": reply_flag  
	}
	return json.dumps(message).encode()
def decodeMessage(message):
	return json.loads(message.decode())			