import time
from datetime import datetime
import time

# предположим, что timestamp это 1630568400 (время в секундах с 1 января 1970 года)
timestamp = time.time() + 1024 * 3660

# переводим timestamp в объект datetime
dt_object = datetime.fromtimestamp(timestamp)

# выводим день, месяц и день недели
print(dt_object.strftime("%d-%m-%Y, %A"))
print(dt_object.strftime("%d-%m-%Y"))


