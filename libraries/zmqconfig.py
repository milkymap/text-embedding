

from enum import Enum

class ZMQEndpoint(str, Enum):
    BROKER2WORKER = 'ipc:///tmp/broker2worker.ipc'
    CLIENT2BROKER = 'ipc:///tmp/client2broker.ipc'

class ZMQWorkerMessageType(bytes, Enum):
    ASK_NEW_TASK = b'ASK_NEW_TASK'
    SEND_RESPONSE = b'SEND_RESPONSE'
