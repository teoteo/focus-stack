// fs-rawstat: livelli di un'immagine per la calibrazione e l'esposizione automatica di Focus Stack.
//
//   fs-rawstat <file>      →  una riga JSON su stdout (exit 0), oppure {"error": "..."} (exit 1)
//
// RAW: LibRaw (stessa versione e stessi sorgenti di Focus Fusion, third_party/LibRaw) senza demosaicizzare:
// per ogni pixel dell'area visibile il valore grezzo meno il nero del suo canale (black + cblack), diviso per
// (bianco − nero), in percentuale. Così 50 % vuol dire «metà della saturazione del sensore», qualunque sia la
// profondità in bit della fotocamera. I due verdi del Bayer vanno insieme in G.
//
// JPEG, PNG, TIFF a 8/16 bit: ImageIO di macOS; i valori sRGB vengono linearizzati con la curva sRGB, quindi la
// percentuale è una stima ("linear": false nel JSON): la fotocamera applica le sue curve e il suo bilanciamento.
//
// Statistiche per canale R, G, B e su tutti i pixel ("all"): media, mediana, percentili 0,5 e 99,5, minimo,
// massimo (in %), quota di pixel bruciati (≥ bianco) e neri (≤ nero), più la media del riquadro centrale (metà
// larghezza × metà altezza), utile per i flat.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "libraw/libraw.h"

#ifdef __APPLE__
#include <CoreFoundation/CoreFoundation.h>
#include <CoreGraphics/CoreGraphics.h>
#include <ImageIO/ImageIO.h>
#endif

namespace {

const int BINS = 4096;   // risoluzione degli istogrammi: 0,025 % della scala

struct Acc {
  std::vector<unsigned long long> hist = std::vector<unsigned long long>(BINS + 1, 0);
  unsigned long long n = 0, burnt = 0, black = 0;
  double sum = 0, mn = 1e9, mx = -1e9;
  void add(double pct, bool is_burnt, bool is_black) {
    double v = pct < 0 ? 0 : pct > 100 ? 100 : pct;
    hist[(int)(v / 100.0 * BINS + 0.5)]++;
    n++; sum += pct;
    if (pct < mn) mn = pct;
    if (pct > mx) mx = pct;
    if (is_burnt) burnt++;
    if (is_black) black++;
  }
  double pctile(double q) const {
    if (!n) return 0;
    unsigned long long want = (unsigned long long)std::ceil(q * n), acc = 0;
    if (!want) want = 1;
    for (int i = 0; i <= BINS; i++) { acc += hist[i]; if (acc >= want) return i * 100.0 / BINS; }
    return 100;
  }
};

std::string esc(const char *s) {
  std::string o;
  for (; s && *s; s++) {
    unsigned char c = (unsigned char)*s;
    if (c == '"' || c == '\\') { o += '\\'; o += (char)c; }
    else if (c < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); o += b; }
    else o += (char)c;
  }
  return o;
}

std::string num(double v, int dec = 3) {
  if (!std::isfinite(v)) return "null";
  char b[64];
  snprintf(b, sizeof b, "%.*f", dec, v);
  return b;
}

std::string acc_json(const Acc &a) {
  if (!a.n) return "null";
  std::string o = "{";
  o += "\"mean\":" + num(a.sum / a.n) + ",\"median\":" + num(a.pctile(0.5)) + ",\"p0_5\":" + num(a.pctile(0.005)) +
       ",\"p99_5\":" + num(a.pctile(0.995)) + ",\"min\":" + num(a.mn) + ",\"max\":" + num(a.mx) +
       ",\"burnt_pct\":" + num(100.0 * a.burnt / a.n, 4) + ",\"black_pct\":" + num(100.0 * a.black / a.n, 4) +
       ",\"pixels\":" + std::to_string(a.n) + "}";
  return o;
}

int fail(const std::string &msg) {
  printf("{\"error\":\"%s\"}\n", esc(msg.c_str()).c_str());
  return 1;
}

void print(const char *kind, bool linear, int w, int h, Acc ch[3], const Acc &all, double center, const std::string &extra) {
  printf("{\"kind\":\"%s\",\"linear\":%s,\"width\":%d,\"height\":%d,\"channels\":{\"R\":%s,\"G\":%s,\"B\":%s},"
         "\"all\":%s,\"center_mean\":%s%s}\n",
         kind, linear ? "true" : "false", w, h, acc_json(ch[0]).c_str(), acc_json(ch[1]).c_str(), acc_json(ch[2]).c_str(),
         acc_json(all).c_str(), num(center).c_str(), extra.c_str());
}

int stat_raw(const char *path) {
  LibRaw *rp = new LibRaw;
  int r = rp->open_file(path);
  if (r != LIBRAW_SUCCESS) { std::string e = libraw_strerror(r); delete rp; return r == LIBRAW_FILE_UNSUPPORTED ? -1 : fail(e); }
  r = rp->unpack();
  if (r != LIBRAW_SUCCESS) { std::string e = libraw_strerror(r); delete rp; return fail(e); }
  auto &d = rp->imgdata;
  const auto &sz = d.sizes;
  const auto &col = d.rawdata.color;   // nero e bianco come letti dal file (prima di ogni elaborazione)
  int W = sz.width, H = sz.height;
  double white = col.maximum;
  Acc ch[3], all;
  double csum = 0; unsigned long long cn = 0;
  // istogramma dei valori grezzi per canale: serve a trovare la saturazione vera (molte fotocamere, es. Sony,
  // saturano un po' sotto il "maximum" teorico: i pixel bruciati si accumulano tutti sullo stesso valore)
  std::vector<std::vector<unsigned>> rawh(3, std::vector<unsigned>(65536, 0));
  auto black_of = [&](int c, int row, int colm) {
    double b = col.black + col.cblack[c];
    if (col.cblack[4] && col.cblack[5])
      b += col.cblack[6 + (row % col.cblack[4]) * col.cblack[5] + (colm % col.cblack[5])];
    return b;
  };
  auto take = [&](int row, int c, double v, double b) {
    double range = white - b;
    if (range <= 0) return;
    double pct = (v - b) / range * 100.0;
    int k = c == 3 ? 1 : c;   // secondo verde
    bool blk = v <= b;
    ch[k].add(pct, false, blk);
    all.add(pct, false, blk);
    rawh[k][(unsigned)v > 65535 ? 65535 : (unsigned)v]++;
    (void)row;
  };
  if (d.rawdata.raw_image) {   // Bayer o X-Trans: un valore per pixel
    const unsigned short *raw = d.rawdata.raw_image;
    int pitch = sz.raw_pitch / 2;
    for (int row = 0; row < H; row++) {
      const unsigned short *line = raw + (size_t)(row + sz.top_margin) * pitch + sz.left_margin;
      bool crow = row >= H / 4 && row < H * 3 / 4;
      for (int c0 = 0; c0 < W; c0++) {
        int c = rp->COLOR(row, c0);
        if (c < 0 || c > 3) continue;
        double b = black_of(c, row, c0), v = line[c0];
        take(row, c, v, b);
        if (crow && c0 >= W / 4 && c0 < W * 3 / 4 && white > b) { csum += (v - b) / (white - b) * 100.0; cn++; }
      }
    }
  } else if (d.rawdata.color4_image || d.rawdata.color3_image) {   // RAW già a colori (alcuni DNG, sRAW)
    int nc = d.rawdata.color4_image ? 4 : 3;
    for (int row = 0; row < H; row++) {
      bool crow = row >= H / 4 && row < H * 3 / 4;
      for (int c0 = 0; c0 < W; c0++) {
        size_t i = (size_t)(row + sz.top_margin) * (sz.raw_pitch / (2 * nc)) + c0 + sz.left_margin;
        for (int c = 0; c < 3; c++) {
          double v = nc == 4 ? d.rawdata.color4_image[i][c] : d.rawdata.color3_image[i][c];
          double b = black_of(c, row, c0);
          take(row, c, v, b);
          if (c == 1 && crow && c0 >= W / 4 && c0 < W * 3 / 4 && white > b) { csum += (v - b) / (white - b) * 100.0; cn++; }
        }
      }
    }
  } else {
    delete rp;
    return fail("RAW senza dati leggibili");
  }
  // saturazione per canale: il valore massimo osservato, se lì si accumulano molti pixel (picco), altrimenti il bianco
  std::string sat_json = ",\"saturation\":[";
  all.burnt = 0;
  for (int k = 0; k < 3; k++) {
    int top = 65535;
    while (top > 0 && !rawh[k][top]) top--;
    unsigned long long nk = ch[k].n;
    double sat = white;
    if (nk && top >= 0.85 * white && rawh[k][top] >= 0.0005 * nk && rawh[k][top] > 3ULL * (top > 0 ? rawh[k][top - 1] : 0))
      sat = top < white ? top : white;
    unsigned long long b = 0;
    for (int v = (int)std::ceil(sat); v <= 65535; v++) b += rawh[k][v];
    ch[k].burnt = b;
    all.burnt += b;
    sat_json += (k ? "," : "") + num(sat, 0);
  }
  sat_json += "]";
  std::string extra = sat_json + ",\"black\":" + num(col.black + (col.cblack[0] + col.cblack[1] + col.cblack[2] + col.cblack[3]) / 4.0, 1) +
                      ",\"white\":" + num(white, 0) +
                      ",\"camera\":\"" + esc(d.idata.make) + " " + esc(d.idata.model) + "\"" +
                      ",\"iso\":" + num(d.other.iso_speed, 0) + ",\"shutter_s\":" + num(d.other.shutter, 6) +
                      ",\"aperture\":" + num(d.other.aperture, 1) + ",\"libraw\":\"" + esc(LibRaw::version()) + "\"";
  print("raw", true, W, H, ch, all, cn ? csum / cn : NAN, extra);
  delete rp;
  return 0;
}

#ifdef __APPLE__
double srgb_to_linear(double v) { return v <= 0.04045 ? v / 12.92 : std::pow((v + 0.055) / 1.055, 2.4); }

int stat_image(const char *path) {
  CFURLRef url = CFURLCreateFromFileSystemRepresentation(nullptr, (const UInt8 *)path, strlen(path), false);
  CGImageSourceRef src = url ? CGImageSourceCreateWithURL(url, nullptr) : nullptr;
  if (url) CFRelease(url);
  CGImageRef img = src ? CGImageSourceCreateImageAtIndex(src, 0, nullptr) : nullptr;
  if (src) CFRelease(src);
  if (!img) return fail("formato non riconosciuto");
  size_t W = CGImageGetWidth(img), H = CGImageGetHeight(img);
  int bits = (int)CGImageGetBitsPerComponent(img) > 8 ? 16 : 8;
  // copia in RGBA a 8 o 16 bit nello spazio sRGB (stessi valori del file per le immagini sRGB)
  CGColorSpaceRef cs = CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
  size_t bpp = bits / 8 * 4, stride = W * bpp;
  std::vector<unsigned char> buf(stride * H);
  CGBitmapInfo info = (CGBitmapInfo)kCGImageAlphaNoneSkipLast | (bits == 16 ? kCGBitmapByteOrder16Host : 0);
  CGContextRef ctx = CGBitmapContextCreate(buf.data(), W, H, bits, stride, cs, info);
  CGColorSpaceRelease(cs);
  if (!ctx) { CGImageRelease(img); return fail("immagine non leggibile"); }
  CGContextDrawImage(ctx, CGRectMake(0, 0, W, H), img);
  CGContextRelease(ctx);
  CGImageRelease(img);
  double top = bits == 16 ? 65535.0 : 255.0;
  std::vector<double> lut(bits == 16 ? 65536 : 256);
  for (size_t i = 0; i < lut.size(); i++) lut[i] = srgb_to_linear(i / top) * 100.0;
  Acc ch[3], all;
  double csum = 0; unsigned long long cn = 0;
  for (size_t y = 0; y < H; y++) {
    bool crow = y >= H / 4 && y < H * 3 / 4;
    for (size_t x = 0; x < W; x++) {
      for (int c = 0; c < 3; c++) {
        unsigned v = bits == 16 ? ((unsigned short *)(buf.data() + y * stride))[x * 4 + c] : buf[y * stride + x * 4 + c];
        double pct = lut[v];
        bool burnt = v == (unsigned)top, blk = v == 0;
        ch[c].add(pct, burnt, blk);
        all.add(pct, burnt, blk);
        if (c == 1 && crow && x >= W / 4 && x < W * 3 / 4) { csum += pct; cn++; }
      }
    }
  }
  std::string extra = ",\"bits\":" + std::to_string(bits);
  print(bits == 16 ? "rgb16" : "rgb8", false, (int)W, (int)H, ch, all, cn ? csum / cn : NAN, extra);
  return 0;
}
#endif

}  // namespace

int main(int argc, char **argv) {
  if (argc != 2 || !strcmp(argv[1], "--version")) {
    printf("{\"tool\":\"fs-rawstat\",\"libraw\":\"%s\"}\n", LibRaw::version());
    return argc == 2 ? 0 : 2;
  }
  int r = stat_raw(argv[1]);
  if (r >= 0) return r;
#ifdef __APPLE__
  return stat_image(argv[1]);   // non è un RAW: JPEG, PNG, TIFF…
#else
  return fail("formato non supportato");
#endif
}
