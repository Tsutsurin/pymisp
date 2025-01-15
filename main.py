from path_to_file import path_to_txt, path_to_log
import logging
import urllib3
import json
from datetime import datetime, timedelta
from pymisp import ExpandedPyMISP
from pymisp import MISPEventBlocklist
from settings import url, key, ssl, outputdir, filters, valid_attribute_distribution_levels
try:
    from settings import with_distribution
except ImportError:
    with_distribution = False

try:
    from settings import with_local_tags
except ImportError:
    with_local_tags = True

try:
    from settings import include_deleted
except ImportError:
    include_deleted = False

try:
    from settings import exclude_attribute_types
except ImportError:
    exclude_attribute_types = []


valid_attribute_distributions = []
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# подключение к MISP
def init():
    global valid_attribute_distributions
    try:
        valid_attribute_distributions = [
            int(v) for v in valid_attribute_distribution_levels]
    except Exception:
        valid_attribute_distributions = [0, 1, 2, 3, 4, 5]
    return ExpandedPyMISP(url, key, ssl)


# проверка на существование ID
# функция возвращает Истину, если удалось найти ID события, Лож в ином случае
def subsist(event_id):
    try:
        result = misp.search(eventid=event_id)
        if result != []:
            return True
        else:
            return False
    except Exception as e:
        print(f'Ошибка поиска события {e}') 


# работа с файлом
# функцию сделал для красоты, чтобы каждый раз не открывать файл, а вызывать одной строкой
def fileread():
    try:
        with open(path_to_txt(), 'r') as f:
            lines = f.readlines()
            lines = [line.rstrip() for line in lines]
            return lines
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при открытие файла: {e}')


# 1. Функция удаляет событие полученное от пользователя. 
# удаление событий по одному ID
def del_by_hand(event_id):
    if subsist(event_id):
        try:
            misp.delete_event(event_id)
            print(f'Событие успешно удалено id: {event_id}')
        except Exception as e:
            logger.error('Ошибка: ', exc_info=True)
            print(f'Ошибка при удалении cобытия: {e}')
    else:
        print(f'ID {event_id} не существует')
        logger.info(f'{event_id} не существует')


# 2. Работа с файлом id.txt, все события из файла будут удалены
# удаление событий с ID из txt документа
def del_by_list():
    lines = fileread()
    for line in lines:
        if subsist(line):
            try:
                misp.delete_event(line)
                print(f'Объект успешно удален {line}.')
            except Exception as e:
                logger.error('Ошибка: ', exc_info=True)
                print(f'Ошибка при удалении объекта: {e}')
        else:
            print(f'ID {line} не существует')
            logger.info(f'{line} не существует')


# 3. На вход ожидается первое и последнее событие, они и все события между ними с шагом 1, будут удалены
# удаление событий по диапазону ID
def del_by_range():
    try:
        
        first = int(input('ID события с какого начать удаление '))
        if subsist(first):
            last = int(input('ID события по какое удалить '))
            if subsist(last):
                for i in range(first, last+1):
                    del_by_hand(i)
            else:
                print(f'ID {last} не существует')
                logger.info(f'{last} не существует')
        else:
            print(f'ID {first} не существует')
            logger.info(f'{first} не существует')    

    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при удалении объекта: {e}')        


# 4. Из файла id.txt берутся исключения, все события что не в файле - удаляются    
# удалиние всех событий с исключением по ID
def del_with_exception():
    lines = fileread()
    try:
        events = misp.search(controller='events')
        if not events or not isinstance(events, list):
            logger.info('Не нашлись события')
            print('События не найдены')
            return

        for event_date in events:
            if not isinstance(event_date, dict) or 'Event' not in event_date:
                print('Некорректное событие, пропускаю...')
                continue
            
            event = event_date['Event']

            if event['id'] not in lines:
                print(f'Удаление события с ID {event['id']}')
                misp.delete_event(event['id'])
            else:
                print(f'пропускаю событие с ID {event['id']}')
        print('Удаление завершено')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при удалении событий: {e}')


# 5.
# удалиние всех событий
def del_all():
    try:
        events = misp.search(controller='events')
        if not events or not isinstance(events, list):
            logger.info('Не нашались события')
            print('События не найдены')
            return

        for event_date in events:
            if not isinstance(event_date, dict) or 'Event' not in event_date:
                print('Некорректное событие, пропускаю...')
                continue
            
            event = event_date['Event']            
            print(f'Удаление события с ID {event['id']}')
            misp.delete_event(event['id'])
        print('Удаление завершено')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при удалении событий: {e}')


# без номера. сделал удаления СОБЫТИЙ по ID UUID IOC. Чтобы включить добавьте название функции (то что после def, со скобочками) в самый конец кода
# удаление IOC по UUID или ID события!
def del_attribute_by_id_uuid():
    try:
        event_identifier = int(input('Введите ID или UUID '))
        event = misp.get_event(event_identifier)
        print(event)
        if 'Event' not in event:
            print(f'Событие с ID/UUID {event_identifier} не найдено.')
            return
        
        event_id = event['Event']['id']
        attributes = event['Event'].get('Attribute', [])

        if not attributes:
            print(f'У события {event_id} отсутсвуют атрибуты.')
            return
        for attribute in attributes:
            print(attribute)
            attribute_id = attribute['id']
            misp.delete_attribute(attribute_id)
            print(f'Атрибут c ID {attribute_id} успешно удален.')
        print(f'Все атрибуты для событий с ID/UUID {event_id} удалены.')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при удалении атрибутов: {e}')


# 6. На вход ожидается ID || UUID атрибута и удалется атрибут
# удалить IOC по UUID или ID атрибута!
def del_attribute_by_id_uuid_attr():
    try:
        attribute_id = int(input('Введите ID или UUID '))
        attribute_info = misp.get_attribute(attribute_id)

        if not 'errors' in attribute_info:
            misp.delete_attribute(attribute_id)
            print(f'Удаление атрибута {attribute_id} прошло успешно!')
        else:
            print(f'Атрибута с {attribute_id} не существует')

    except Exception as e:
        print(f'Ошибка при удалении атрибута {e}')


# 7. Вычитает 30 дней от времени в компьютере. Переводит полученный результат в timestamp (особый формат даты, с которым работает процессор). Все что младше полученной даты - удаляется
# удалить атрибут по времени
def del_old_ioc():
    now = datetime.now()
    old_date = now - timedelta(days=30)
    old_date_timestamp = int(old_date.timestamp())

    try:
        result = misp.search(controller='attributes')
        if not result or not isinstance(result['Attribute'], list):
            logger.info('Не нашлись события')
            print('События не найдены')
            return

        if result.get('Attribute'):
            attributes = result['Attribute']
            for attr in attributes:
                
                attr_id = attr['id']
                attr_date = int(attr.get('timestamp'))
                print(attr_date)
                if attr_date <= old_date_timestamp:
                    print(f'Атрибут с ID {attr_id} устарело, удаляю!')
                    misp.delete_attribute(attr_id)

    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при поиске атрибутов: {e}')


# 8. Удаляет атрибуты score = 0
# удалить score=0
def del_ioc_score_zero():
    try:
        result = misp.search(controller='attributes', include_decay_score=True)
        if not result or not isinstance(result['Attribute'], list):
            logger.info('Не нашлись события')
            print('События не найдены')
            return
    
        if result.get('Attribute'):
            attributes = result['Attribute']
            print(f'Найдено {len(attributes)} атрибутов с Decay Model')

            for attr in attributes:
                decay_score = float(attr.get('decay_score')[0].get('score'))
                print(decay_score)
                attr_id = attr['id']

                if decay_score == 0:
                    try:
                        misp.delete_attribute(attr_id)
                        print(f'Атрибут ID {attr_id} (score=0) успешно удален')
                    except Exception as e:
                        print(f'Ошибка при удалении атрибута ID {attr_id}: {e}')
        else:
            print('Нет атрибутов с Decay Model и score=0')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при поиске атрибутов: {e}')


# 9. Выгружает атрибуты в json
# выгрузка атрибутов по времени
def fetch_attribures_with_date():
    try:
        now = datetime.now()
        old_date = now - timedelta(days=30)
        old_date_timestamp = int(old_date.timestamp())
        result = misp.search(controller='attributes', return_format='json')
        attributes = result.get('Attribute', [])

        filtered_attributes = []
        for attr in attributes:
            attribute_date = int(attr.get('timestamp'))
            if old_date_timestamp < attribute_date:
                filtered_attributes.append(attr)

        if filtered_attributes:
            print(f'Найдено {len(filtered_attributes)} атрибутов за 30 дней')
            name_f = (f'Выгрузка за 30 дней {datetime.today().strftime('%d.%m.%Y')}.json')
            with open(name_f, 'w', encoding='utf-8') as f:
                json.dump(filtered_attributes, f, ensure_ascii=False, indent=4)
            print(f'Файл "{name_f}" создан')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при выгрузке атрибутов {e}')


# 10. Выгружает атрибуты в json
# выгрузка атрибутов по score > 0
def fetch_attribures_with_score():
    try:
        result = misp.search(controller='attributes', include_decay_score=True, return_format='json')
        attributes = result.get('Attribute', [])

        filtered_attributes = []
        for attr in attributes:
            decay_score = float(attr.get('decay_score')[0].get('score'))
            if decay_score > 0:
                filtered_attributes.append(attr)

        if filtered_attributes:
            print(f'Найдено {len(filtered_attributes)} атрибутов с score > 0')
            name_f = (f'Выгрузка за {datetime.today().strftime('%d.%m.%Y')} score.json')
            with open(name_f, 'w', encoding='utf-8') as f:
                json.dump(filtered_attributes, f, ensure_ascii=False, indent=4)
            print(f'Файл "{name_f}" создан')
    except Exception as e:
        logger.error('Ошибка: ', exc_info=True)
        print(f'Ошибка при выгрузке атрибутов {e}')


# 11. Создает событие с атрибутом
# функция для теста, создание события
def create_event():
    try:
        event_data = { 'info': 'Тестовое событие', 'distribution': 0, 'threat_level_id': 2, 'analysis': 0}
        event = misp.add_event(event_data)
        event_id = event['Event']['id']
        print(f'Событие успешно создано с ID: {event_id}')
        ioc_date = {'type': 'ip-src', 'value': '192.168.1.1'}
        added_attribure = misp.add_attribute(event_id, ioc_date)
        print(f'Добавлен атрибут: {added_attribure['Attribute']['value']} к событию ID: {event_id}')
        return event
    except Exception as e:
        logger.error('Ошибка при создании события:', exc_info=True)
        print(f'Ошибка при создании события: {e}')
        return None 


# основной код     
if __name__ == '__main__':
    misp = init()
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename= path_to_log(), encoding='utf-8', level=logging.DEBUG)
    logger.info(f'\n    Новый запуск{datetime.now()}    \n')
    
    while True:
        # просит пользователя ввести данные, типа выбрать 1, 2, 3.. \n переход на новую строку
        choice = input('\n1: удаление события по ID вручную'
                    '\n2: удаление событий по ID из файла'
                    '\n3: удаление событий по диапазону ID'
                    '\n4: удалить все события кроме'
                    '\n5: удаление всех событий'
                    '\n6: удаление IOC по ID или UUID'
                    '\n7: удаление IOC по времени'
                    '\n8: удаление IOC score=0'
                    '\n9: выгрузка IOC по времени'
                    '\n10: выгрузка IOC по score>0'
                    '\n11: создать событие'
                    '\n12: отчистить EventBlocklist'
                    '\n13: Выйти\n')
        # если пользователь ввел 1, 2, 3... то вызвать функцию
        match choice:
            case '1':
                event_id = int(input('Введите ID '))
                del_by_hand(event_id)
            case '2':
                del_by_list()
            case '3':
                del_by_range()
            case '4':
                del_with_exception()
            case '5':
                del_all()
            case '6':
                del_attribute_by_id_uuid_attr()
            case '7':
                del_old_ioc()
            case '8':
                del_ioc_score_zero()
            case '9':
                fetch_attribures_with_date()
            case '10':
                fetch_attribures_with_score()
            case '11':
                create_event()
            case '12':
                clear_blocklost()
            case '13':
                break
