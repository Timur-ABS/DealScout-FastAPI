import psycopg2
import psycopg2

# Параметры подключения к базе данных
host = 'localhost'
port = '5432'
dbname = 'user'
user = 'postgres'
password = '3557'

# Установка соединения с базой данных

connection = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)

cursor = connection.cursor()

cursor.execute('SELECT * FROM test')

# Получение результатов запроса
results = cursor.fetchall()

# Вывод результатов
for row in results:
    print(row)

# Закрытие курсора и соединения
cursor.close()
connection.close()
