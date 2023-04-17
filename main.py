import requests
import json
from datetime import datetime
import os
from progress.bar import IncrementalBar
from config import ACCESS_TOKEN
from config import USER_ID
from config import YA_OAUTH_TOKEN

class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_user_profile_photo(self, photo_count=5):
        url = 'https://api.vk.com/method/photos.get'
        #Обертка с проверкой на качество ввода
        while True:
            user_count = input(f'Укажите кол-во загружаемых фото профиля (по умолчанию {photo_count}):')
            try:
                test4num = int(user_count)
            except ValueError:
                print('Ошибка! Введите число.')
            else:
                photo_count = test4num
                break

        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': '1', 'count': photo_count, 'rev': '1', 'photo_sizes': '1'}
        response = requests.get(url, params={**self.params, **params})
        photos = {}
        if response.status_code == 200:
            array_lenght = len(response.json()['response']['items'])
            print(f'Метаданные фото профиля получены')
            #bar = IncrementalBar('Recieving photos', max=array_lenght)
            for item in response.json()['response']['items']:
                #в списке sizes размеры картинок по умолчанию упорядочены от мал к бол, поэтому всегда берем последнее значение
                #!!! не всегда список отсортирован по размеру, поэтому сперва сортируем, а потом берем последний
                sorted_sizes = sorted(item['sizes'], key=lambda d: d['type'])
                jpg_url = sorted_sizes[-1]['url']
                size_type = sorted_sizes[-1]['type']

                likes_count = item['likes']['count']
                if likes_count in photos:
                    jpg_date_int = int(item['date'])
                    jpg_date = datetime.utcfromtimestamp(jpg_date_int).strftime('%Y-%m-%d_%H-%M-%S')
                    filename = f'{str(likes_count)}_{jpg_date}'
                    photos[filename] = {'url': jpg_url, 'type': size_type}

                else:
                    photos[likes_count] = {'url': jpg_url, 'type': size_type}

                #bar.next()

            #bar.finish()
        return json.dumps(photos)

    def save_photo_metadata(self, photos_json, filename):
        json_file = [{'filename': f'{f}.jpg', 'size': val['type']} for f, val in photos_json.items()]
        with open(f'{filename}.json', 'w', encoding='utf-8') as f:
            json.dump(json_file, f, ensure_ascii=False, indent=4)

class YaUploader(VK):

    def __init__(self, token: str):
        self.token = token
        self.yandex_api = 'https://cloud-api.yandex.net:443/'

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def get_upload_href(self, destination_file_path):
        upload_ulr = f'{self.yandex_api}v1/disk/resources/upload'
        hdrs = self.get_headers()
        params = {'path': destination_file_path, 'overwrite': 'true'}
        response = requests.get(upload_ulr, headers=hdrs, params=params)
        return response.json()
    def create_folder(self, folder_name):
        upload_ulr = f'{self.yandex_api}v1/disk/resources'
        hdrs = self.get_headers()
        params = {'path': folder_name, 'overwrite': 'true'}
        if requests.get(upload_ulr, headers=hdrs, params=params).status_code != 200:
            response = requests.put(upload_ulr, headers=hdrs, params=params)
            if response.status_code == 201:
                return print(f'На Я-диске создана папка {folder_name}')

    def upload(self, file_path_local: str, file_name_remote):
        """Метод загружает файлы по списку file_list на яндекс диск"""
        href = self.get_upload_href(destination_file_path=file_name_remote).get('href', '')
        with open(file_path_local, 'rb') as file:
            f = file.read()
            requests.put(url=href, data=f)

    def dupload(self, photos, dest_folder_name):
        '''Ф-ция сохряняет из переданного json photos файлы локально и отправляет их на Я-диск'''
        #Создаем локальную папку
        os.makedirs(f'{dest_folder_name}', exist_ok=True)
        #Создаем одноименную папку на Я-диске
        self.create_folder(dest_folder_name)
        print(f'Старт загрузки фото профиля')
        bar = IncrementalBar('Recieving photos', max=len(photos))
        for f, val in photos.items():
            result = requests.get(val['url'])
            if result.status_code == 200:
                with open(rf'{dest_folder_name}\{f}.jpg', 'wb') as file:
                    file.write(result.content)
                self.upload(rf'{dest_folder_name}\{f}.jpg', rf'{dest_folder_name}/{f}.jpg')
                bar.next()
        bar.finish()

if __name__ == '__main__':
    if 'None' in (ACCESS_TOKEN, USER_ID, YA_OAUTH_TOKEN):
        print('Не заданы обязательные параметры:access_token, user_id, ya_oauth_token')
        exit()

    #Получаем фото профиля
    vk = VK(ACCESS_TOKEN, USER_ID)
    photo = json.loads(vk.get_user_profile_photo())
    #Сохраняем метаданные в json файд
    vk.save_photo_metadata(photo, 'photos_metadata')

    dest_folder_name = f'VkProfilePhotos_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
    #dest_folder_name = f'VkProfilePhotos'

    #Сохраняем фото профиля на локальный диск и в Я-диск
    yDisk = YaUploader(YA_OAUTH_TOKEN)

    #Сохраняем фото ВК профиля
    yDisk.dupload(photo, dest_folder_name)