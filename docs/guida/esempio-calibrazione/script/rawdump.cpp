// Decodifica un RAW in luce lineare (gamma 1, niente schiarimento automatico, bilanciamento della fotocamera,
// metà risoluzione, sRGB lineare) e scrive un PPM a 16 bit. Solo per preparare le figure della guida.
#include "libraw/libraw.h"
#include <cstdio>
int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "uso: rawdump in.ARW out.ppm\n"); return 2; }
  LibRaw r;
  r.imgdata.params.output_bps = 16;
  r.imgdata.params.gamm[0] = 1.0; r.imgdata.params.gamm[1] = 1.0;
  r.imgdata.params.no_auto_bright = 1;
  r.imgdata.params.use_camera_wb = 1;
  r.imgdata.params.half_size = 1;
  r.imgdata.params.output_color = 1;
  r.imgdata.params.user_flip = 0;
  if (r.open_file(argv[1]) || r.unpack() || r.dcraw_process()) { fprintf(stderr, "errore LibRaw\n"); return 1; }
  int err = 0; libraw_processed_image_t* im = r.dcraw_make_mem_image(&err);
  if (!im) return 1;
  FILE* f = fopen(argv[2], "wb");
  fprintf(f, "P6\n%d %d\n65535\n", im->width, im->height);
  unsigned short* d = (unsigned short*)im->data;
  for (unsigned i = 0; i < (unsigned)im->width * im->height * 3; i++) { unsigned char b[2] = {(unsigned char)(d[i] >> 8), (unsigned char)(d[i] & 255)}; fwrite(b, 1, 2, f); }
  fclose(f); LibRaw::dcraw_clear_mem(im);
  return 0;
}
