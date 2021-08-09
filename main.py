import vk_api, requests, json, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops
from vk_api.longpoll import VkLongPoll, VkEventType


fonts_path = '/root/delBot/vk.ttf'
key_log = '!л'
key_logchat = '!лог'
key_unlogchat = '!анлог'

vk_session = vk_api.VkApi(token='token')

try:
    file = open('log.json')
except IOError as e:
    print('Создание файла с логами...')
    with open("log.json", "w", encoding="utf-8") as name_dump_out:
        json.dump({}, name_dump_out, indent=2, ensure_ascii=False)
    print('Файл создан\nЗапустите скрипт еще раз')
    sys.exit()
else:
    with file:
        with open("log.json", encoding="utf-8") as name_file:
            json_log = json.load(name_file)


def json_dump(json_log):
    with open("log.json", "w", encoding="utf-8") as name_dump_out:
        json.dump(json_log, name_dump_out, indent=2, ensure_ascii=False)


def crop_to_circle(im):
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)


def get_name_ava(id, i2):
    ava = vk.users.get(user_ids=id, fields='photo_50')
    name = ava[0]['first_name']
    picture = requests.get(ava[0]['photo_50'])
    photoPath = f"ava{i2}.jpg"
    out = open(photoPath, "wb")
    out.write(picture.content)
    out.close()
    ava = Image.open(f"ava{i2}.jpg").convert('RGBA')
    crop_to_circle(ava)
    ava = ava.resize((40, 40), Image.ANTIALIAS)
    return ava, name


def slice_text(text):
    text = text.replace('<br>', ' ')
    text = text.replace('\n', ' ')
    return text


longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()
for event in longpoll.listen():
    if event.from_chat:
        if event.type == VkEventType.MESSAGE_NEW and event.message == key_log and str(event.peer_id) in json_log and event.from_me:
            if len(list(json_log[str(event.peer_id)]['edits'].values())) != 0:
                pic_len = 0
                for i in (list(json_log[str(event.peer_id)]['edits'].keys())):
                    if len(json_log[str(event.peer_id)]['edits'][i][0]) > 40:
                        pic_len += 40
                img = Image.new('RGBA', (900, (len(list(json_log[str(event.peer_id)]['edits'].values())) * 105) + 40 + pic_len), 'white')
                idraw = ImageDraw.Draw(img)
                font = ImageFont.truetype(fonts_path, size=25)
                px1, px2, i2 = 40, 80, 0
                sorted_keys = sorted(list(json_log[str(event.peer_id)]['edits'].keys()))
                for i in sorted_keys:
                    ava, name = get_name_ava(json_log[str(event.peer_id)]['edits'][i][1], i2)
                    i2+=1
                    if len(json_log[str(event.peer_id)]['edits'][i]) == 3:
                        if len(json_log[str(event.peer_id)]['edits'][i][2]) > 40:
                            un_text = '(Ред.) '+json_log[str(event.peer_id)]['edits'][i][2][0:40]+'...'
                        else:
                            un_text = '(Ред.) '+json_log[str(event.peer_id)]['edits'][i][2][0:40]
                    else:
                        un_text = 'Удалено'
                    text = json_log[str(event.peer_id)]['edits'][i][0]
                    if len(text) > 40:
                        text1 = text[0:40]
                        if len(text[40:]) > 40:
                            text2 = text[40:80] + '...'
                        else:
                            text2 = text[40:]
                        idraw.multiline_text((100, px1), un_text, 'gray', font=font)
                        idraw.multiline_text((100, px2), f'{name}: {text1}', 'black', font=font)
                        idraw.multiline_text((100, px2 + 40), text2, 'black', font=font)
                        img.paste(ava, (40, px2))
                        px1 += 145
                        px2 += 145
                    else:
                        idraw.multiline_text((100, px1), un_text, 'gray', font=font)
                        idraw.multiline_text((100, px2), f'{name}: {text}', 'black', font=font)
                        img.paste(ava, (40, px2))
                        px1 += 105
                        px2 += 105
                img.save('result.png')
                upload = vk_api.VkUpload(vk)
                photo = upload.photo_messages('result.png')
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                access_key = photo[0]['access_key']
                attachment = f'photo{owner_id}_{photo_id}_{access_key}'
                vk.messages.edit(peer_id=event.peer_id, message_id=event.message_id, attachment=attachment)
                json_log[str(event.peer_id)]['edits'].clear()
                json_dump(json_log)
            else: vk.messages.delete(peer_id=event.peer_id, delete_for_all=1, message_ids=event.message_id)

        if event.type == VkEventType.MESSAGE_NEW and (str(event.peer_id) not in json_log) and (event.message == key_logchat) and event.from_me:
            json_log[str(event.peer_id)] = {'all': {}, 'edits': {}}
            json_dump(json_log)
            vk.messages.edit(peer_id=event.peer_id, message='Чат успешно добавлен!', message_id=event.message_id)
            vk.messages.delete(peer_id=event.peer_id, delete_for_all=1, message_ids=event.message_id)

        if event.type == VkEventType.MESSAGE_NEW and (str(event.peer_id) in json_log) and (event.message == key_unlogchat) and event.from_me:
            del json_log[str(event.peer_id)]
            json_dump(json_log)
            vk.messages.edit(peer_id=event.peer_id, message='Чат успешно убран!', message_id=event.message_id)
            vk.messages.delete(peer_id=event.peer_id, delete_for_all=1, message_ids=event.message_id)

        if (event.raw[0] == 4 or event.raw[0] == 2 or event.raw[0] == 5) and str(event.peer_id) in json_log and not event.from_me:
            if event.raw[0] == 4 and event.text != '' and event.user_id > 0:
                json_log[str(event.peer_id)]['all'][str(event.message_id)] = event.raw
            if event.raw[0] == 2 and str(event.message_id) in json_log[str(event.peer_id)]['all']:
                json_log[str(event.peer_id)]['edits'][str(event.message_id)] = ([slice_text(json_log[str(event.peer_id)]['all'][str(event.message_id)][5]), str(json_log[str(event.peer_id)]['all'][str(event.message_id)][6]['from'])])
            if event.raw[0] == 5 and event.text != '' and str(event.message_id) in json_log[str(event.peer_id)]['all'] and event.text != json_log[str(event.peer_id)]['all'][str(event.message_id)][5]:
                json_log[str(event.peer_id)]['edits'][str(event.message_id)] = ([slice_text(event.text), str(event.user_id), slice_text(json_log[str(event.peer_id)]['all'][str(event.message_id)][5])])

            if len(list(json_log[str(event.peer_id)]['all'].keys())) > 200:
                json_log[str(event.peer_id)]['all'].pop(list(json_log[str(event.peer_id)]['all'].keys())[0])
            if len(list(json_log[str(event.peer_id)]['edits'].keys())) > 10:
                json_log[str(event.peer_id)]['edits'].pop(list(json_log[str(event.peer_id)]['edits'].keys())[0])
            json_dump(json_log)
