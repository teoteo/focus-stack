import sys, glob, subprocess, numpy as np, os
S=sys.argv[1]; R="/Volumes/NVMe4TB/Focus Stacking e Fusion/Prove focuser"
def read(path):
    tmp=S+"/pencil/tmp.ppm"; subprocess.run([S+"/rawdump/rawdump",path,tmp],check=True)
    with open(tmp,"rb") as f:
        assert f.readline().strip()==b"P6"; w,h=map(int,f.readline().split()); f.readline()
        a=np.frombuffer(f.read(),dtype=">u2").reshape(h,w,3).astype(np.float32)/65535
    os.remove(tmp); return a
def master(folder):
    fs=sorted(glob.glob(f"{R}/_calibrazione/{folder}/*.ARW")); acc=None
    for f in fs:
        a=read(f); acc=a if acc is None else acc+a
    return acc/len(fs)
for name,folder in (("flat","flat_20261126-101412"),("dark","dark_20261126-101753"),("fdark","flat-dark_20261126-101609")):
    m=master(folder); np.save(f"{S}/pencil/{name}.npy",m); print(name, m.shape, m.mean(axis=(0,1)))
fs=sorted(glob.glob(f"{R}/Pencil_20261126-100229/*.ARW"))
for i in (0, len(fs)//2, len(fs)-1):
    a=read(fs[i]); np.save(f"{S}/pencil/frame_{i:02d}.npy",a); print(os.path.basename(fs[i]), a.mean(axis=(0,1)))
