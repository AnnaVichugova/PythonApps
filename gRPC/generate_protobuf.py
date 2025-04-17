import os

os.system('python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. order.proto')


###### если в Colab
!pip install grpcio grpcio-tools
!python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. person.proto
