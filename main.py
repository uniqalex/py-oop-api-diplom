import requests
import json
from datetime import datetime

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
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': '1', 'count': photo_count, 'rev': '1'}
        response = requests.get(url, params={**self.params, **params})
        if response.status_code == 200:
            photos = {}
            for item in response.json()['response']['items']:
                #в списке sizes размеры картинок по умолчанию упорядочены от мал к бол, поэтому всегда берем последнее значение
                jpg_url = item['sizes'][-1]['url']
                likes_count = item['likes']['count']
                if likes_count in photos:
                    jpg_date_int = int(item['date'])
                    jpg_date = datetime.utcfromtimestamp(jpg_date_int).strftime('%Y-%m-%d_%H-%M-%S')
                    filename = f'{str(likes_count)}_{jpg_date}'
                    photos[filename] = jpg_url
                else:
                    photos[likes_count] = jpg_url
        return json.dumps(photos)

class VkSaver:
    def __init__(self, token: str):
        self.token = token
        self.vk_api = 'https://oauth.vk.com/authorize?client_id=51588303&scope=65536&response_type=token'


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

    def upload(self, file_path: str):
        """Метод загружает файлы по списку file_list на яндекс диск"""
        href = self.get_upload_href(destination_file_path=file_path).get('href', '')
        with open(file_path, 'rb') as file:
            f = file.read()
            response = requests.put(url=href, data=f)
            if response.status_code == 201:
                print('File uploaded')

if __name__ == '__main__':
    access_token = 'vk1.a.iqcAvra8aA3Tdj5xF1lU1ouefE9LgExDVmHxIPTWtNIVX6amX69bc0YwrG4ZeJKoQy3naFj3Jd6-JkalXzugWxbAMyJ56Qi6yNOI9u-458gmmq9k_y7yMzh5JpRRALq4HuSem-XR2_y90Ver6PO1j__wZY2uZX-q8h-xTJUY_kPZtIPNZd-SaQl-IfRfk4OoXICGyocxMx8mAghXky0ZNw'
    user_id = '50544115'
    ya_oauth_token = 'y0_AgAAAAAtDcTsAADLWwAAAADdxg1YTGHhQaIvTLq2UQOO5MTz3ouFUL0'

    vk = VK(access_token, user_id)
    #Test vk token
    #print(vk.users_info())
    print(vk.get_user_profile_photo())
    photo = json.loads(vk.get_user_profile_photo())
    dest_folder_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    for f, url in photo.items():

        result = requests.get(url)
        if result.status_code == 200:
            pass
