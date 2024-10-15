from flask import Flask, request, render_template, jsonify
import grpc
import order_pb2
import order_pb2_grpc
import random
import datetime
from datetime import datetime, timedelta

app = Flask(__name__)

# списки полей в заявке
products = ['яблоки желтые', 'малина', 'вода', 'хлеб белый','хлеб серый', 'креветки', 'форель', 'апельсины', 'кета','курица','яйцо перепелиное','яйцо куриное','лаваш',
            'булка сдобная','булка сахарная','помидоры бакинские','помидоры чери','огурцы','перец сладкий','перец острый','перец болгарский','мандарины','укроп свежий',
            'укроп сушеный','клубника свежая','клубника мороженная','мороженое','картошка','морковь', 'свекла','пангасиус','семга','кальмар замороженный','горошек зеленый',
            'смородина черная','смородина красная','соль поваренная пищевая йодированная','чай черный байховый','чай зеленый','чай красный','кофе','кофе с молоком','какао',
            'молоко','кефир','сыр с плесенью','сыр плавленый','сыр твердый','сыр мягкий','яблоки красные','яблоки зеленые','яблоки сушеные','икра красная',
            'икра черная','икра заморская баклажанная','масло сливочное','масло оливковое','масло подсолнечное','масло кокосовое','орех грецкий','орех бразильский',
            'лист лавровый','куркума','кукуруза','печенье сладкое','пряники сдобные','тесто слоеное','варенц','ряженка','снежок','шоколад молочный']

# Функция для получения информации по ИНН от gRPC сервера
def get_info_by_inn(inn):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)
        provider_request = order_pb2.ProviderINN(inn=inn)
        response = stub.GetInfoByINN(provider_request)
        provider_info = {
            'inn': response.inn,
            'name': response.name,
            'phone': response.phone,
            'email': response.email,
            'address': response.address
        }
    return provider_info

# Функция для отправки потока заказов на gRPC сервер
def stream_orders(provider_info, items):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)

        def order_request_iterator():
            for item in items:
                yield order_pb2.OrderRequest(
                    provider=order_pb2.ProviderINN(
                        inn=provider_info['inn']
                    ),
                    item=[
                        order_pb2.OrderItem(
                            product=o['product'],
                            quantity=int(o['quantity']),
                            price=float(o['price'])
                        )
                        for o in item
                    ]
                )
        server_answer = stub.StreamOrders(order_request_iterator())
        return server_answer

#Обработчик HTTP-запросов
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'inn' in request.form:
            inn = request.form['inn']
            provider_info = get_info_by_inn(inn)
            return render_template('index.html', provider_info=provider_info)
        elif 'send_orders' in request.form:
            provider_info = {
                'inn': request.form['inn_r'],
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'address': request.form['address']
            }
            k = 0
            items = []  # Создаем список заказов вне цикла
            while True:
                item = {
                    'product': random.choice(products),
                    'quantity': random.randint(1, 10),
                    'price': round(random.uniform(1, 1000), 2)
                }
                items.append(item)  # Добавляем новый элемент в список

                # Отправка заказа и получение ответа от сервера
                unary_server_answer = stream_orders(provider_info, [items])
                # Преобразуем временную метку в объект datetime
                timestamp_seconds = unary_server_answer.orderdate.seconds
                timestamp_nanos = unary_server_answer.orderdate.nanos
                order_datetime = datetime.fromtimestamp(timestamp_seconds) + timedelta(
                    microseconds=timestamp_nanos / 1000)

                # Форматируем дату и время в нужный формат
                formatted_date = order_datetime.strftime('%Y-%m-%d %H:%M:%S')

                if unary_server_answer.quantity>50:
                    break

            return render_template('index.html', provider_info=provider_info, orderdate=formatted_date,
                                   quantity=unary_server_answer.quantity,amount=unary_server_answer.amount, products=items)
    else:
        return render_template('index.html', provider_info=None, server_answer=None)

if __name__ == '__main__':
    app.run()
