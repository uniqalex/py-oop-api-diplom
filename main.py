import requests
import json
from datetime import datetime
import os

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
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': '1', 'count': photo_count, 'rev': '1', 'photo_sizes': '1'}
        response = requests.get(url, params={**self.params, **params})
        if response.status_code == 200:
            photos = {}
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
        return json.dumps(photos)

class YaUploader:

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

    def upload(self, file_path_local: str, file_name_remote):
        """Метод загружает файлы по списку file_list на яндекс диск"""
        href = self.get_upload_href(destination_file_path=file_name_remote).get('href', '')
        with open(file_path_local, 'rb') as file:
            f = file.read()
            response = requests.put(url=href, data=f)
            if response.status_code == 201:
                print(f'File {file_path_local} is uploaded')

if __name__ == '__main__':
    access_token = ''
    user_id = ''
    ya_oauth_token = ''

    vk = VK(access_token, user_id)

    photo = json.loads(vk.get_user_profile_photo())
    dest_folder_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    yDisk = YaUploader(ya_oauth_token)

    #Сохраняем метаданные по полученным фото
    json_file = [{'filename': f'{f}.jpg', 'size': val['type']} for f, val in photo.items()]
    with open('photos_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(json_file, f, ensure_ascii=False, indent=4)

    # теперь сохраняем полученные фото профиля
    os.makedirs(f'VkProfilePhotos_{dest_folder_name}', exist_ok=True)

    for f, val in photo.items():
        result = requests.get(val['url'])
        if result.status_code == 200:
            with open(rf'VkProfilePhotos_{dest_folder_name}\{f}.jpg', 'wb') as file:
                file.write(result.content)
            print(f'{f}.jpg is downloaded')
            yDisk.upload(rf'VkProfilePhotos_{dest_folder_name}\{f}.jpg', f'{f}.jpg')
