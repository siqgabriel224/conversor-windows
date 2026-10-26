from PIL import Image, ImageDraw
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'assets';out.mkdir(exist_ok=True)
im=Image.new('RGBA',(256,256),(0,0,0,0));d=ImageDraw.Draw(im)
d.rounded_rectangle((7,7,249,249),radius=58,fill='#151f2c')
d.line([(59,89),(191,89)],fill='#70e0bc',width=20)
d.polygon([(190,57),(222,89),(190,121)],fill='#70e0bc')
d.line([(65,169),(197,169)],fill='#70e0bc',width=20)
d.polygon([(66,137),(34,169),(66,201)],fill='#70e0bc')
im.save(out/'conversor.png');im.save(out/'conversor.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
