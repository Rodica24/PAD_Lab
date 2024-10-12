import grpc
import user_service_pb2
import user_service_pb2_grpc

def run():
    # Establish a channel and stub to communicate with the gRPC server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)

        # Make a request to the GetUser RPC
        response = stub.GetUser(user_service_pb2.GetUserRequest(username='john_doe'))

        # Print the response from the server
        print("User found:", response.username, response.email, response.message)

if __name__ == '__main__':
    run()
