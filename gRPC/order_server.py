import grpc
import datetime
from concurrent import futures
import order_pb2
import order_pb2_grpc
from faker import Faker
from collections import defaultdict

class OrderServiceServicer(order_pb2_grpc.OrderServiceServicer):
    def __init__(self):
        self.fake = Faker('ru_RU')

    def GetInfoByINN(self, request, context):
        data = order_pb2.ProviderData(
            inn=request.inn,
            name=self.fake.name(),
            phone=self.fake.phone_number(),
            address=self.fake.address(),
            email=self.fake.free_email()
        )
        print('Принят от клиента запрос на поставщика с ИНН ', data.inn)
        print('Поставщик с ИНН ', data.inn, ' имеет следующие реквизиты: ')
        print('Название ', data.name)
        print('Телефон ', data.phone)
        print('Адрес ', data.address)
        print('Емейл ', data.email)
        return data

    def StreamOrders(self, request_iterator, context):
        total_quantity = 0
        total_amount = 0
        items = defaultdict(int)

        for order_request in request_iterator:
            print('Принят от клиента заказ с товарами', order_request)
            print('текущее дата и время: ', datetime.datetime.now())
            for item in order_request.item:
                print('товар: ', item)
                total_quantity += item.quantity
                items[item.product] += item.quantity
                print('общее количество товаров', total_quantity)
                total_amount += item.price * item.quantity
                total_amount = round(total_amount, 2)
                print('общая сумма заказа', total_amount)
                print('')

        return order_pb2.OrderResponse(
            quantity=total_quantity,
            amount=total_amount,
            orderdate = datetime.datetime.now()
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
