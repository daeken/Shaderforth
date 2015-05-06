from PIL import Image

data = file('pixels.txt', 'r').read().strip().split('\n')
(width, height), data = map(int, data[:2]), data[2:]
data = ''.join(map(lambda x: chr(int(x)), data))

im = Image.frombytes('RGBA', (width, height), data)
im.save('test3.png')
