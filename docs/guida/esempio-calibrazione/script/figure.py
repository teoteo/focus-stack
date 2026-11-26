import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
S=sys.argv[1]+"/pencil"; OUT=sys.argv[2]
flat=np.load(S+"/flat.npy"); fd=np.load(S+"/fdark.npy"); D=np.load(S+"/dark.npy")
M=np.maximum(flat-fd,0); F=np.maximum(M/M.mean(axis=(0,1)),0.05)
I=np.load(S+"/frame_34.npy"); C=np.maximum(I-D,0)/F
def srgb(a):
    a=np.clip(a,0,1); return (np.where(a<=0.0031308,a*12.92,1.055*a**(1/2.4)-0.055)*255+0.5).astype(np.uint8)
k=0.8/np.percentile(C,99.5)                     # stessa resa per originale e corretto
orig=Image.fromarray(srgb(I*k)); corr=Image.fromarray(srgb(C*k))
g=F.mean(axis=2); lo,hi=np.percentile(g,0.5),np.percentile(g,99.8)
fl=Image.fromarray((np.clip((g-lo)/(hi-lo),0,1)*255).astype(np.uint8)).convert("RGB")
# file a piena risoluzione (metà del sensore) per le guide di Focus Stack e Focus Fusion
fl.save(OUT+"/flat-normalizzato.png"); orig.save(OUT+"/originale.jpg",quality=92); corr.save(OUT+"/corretto.jpg",quality=92)
# figura: tre pannelli con il numero e un ingrandimento della stessa macchia di polvere
X,Y,R=2177,880,70; Z=4
PW=960; scale=PW/fl.width; PH=round(fl.height*scale); GAP=24
W=Image.new("RGB",(3*PW+2*GAP,PH),(255,255,255)); dr=ImageDraw.Draw(W)
try: font=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",34)
except OSError: font=ImageFont.load_default()
for i,im in enumerate((fl,orig,corr)):
    x0=i*(PW+GAP); W.paste(im.resize((PW,PH),Image.LANCZOS),(x0,0))
    cx,cy=x0+X*scale,Y*scale; r=R*scale
    dr.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(255,170,40),width=3)
    crop=im.crop((X-R,Y-R,X+R,Y+R)).resize((2*R*Z//2,2*R*Z//2),Image.LANCZOS)
    ix,iy=x0+PW-crop.width-14,PH-crop.height-14
    W.paste(crop,(ix,iy)); dr.rectangle((ix-2,iy-2,ix+crop.width+1,iy+crop.height+1),outline=(255,170,40),width=4)
    dr.line((cx+r*0.7,cy+r*0.7,ix,iy),fill=(255,170,40),width=2)
    dr.ellipse((x0+14,14,x0+70,70),fill=(242,180,40)); dr.text((x0+42,42),str(i+1),fill=(15,28,46),font=font,anchor="mm")
W.save(OUT+"/calibrazione-esempio.jpg",quality=86)
print(W.size)
