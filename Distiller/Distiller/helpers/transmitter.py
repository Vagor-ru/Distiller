from Distiller import socketio

def Transmit(DataFromServer):
    '''Transmit data in dictioner DataFromServer'''
    socketio.emit('DataFromServer', DataFromServer)
