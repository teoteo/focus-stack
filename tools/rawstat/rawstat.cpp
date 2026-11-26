// fs-rawstat: livelli di un'immagine per la calibrazione e l'esposizione automatica di Focus Stack.
//
//   fs-rawstat <file>      →  una riga JSON su stdout (exit 0), oppure {"error": "..."} (exit 1)
//   fs-rawstat --ptc f1 f2 d1 d2  →  analisi del sensore da due flat e due dark (vedi ptc() più sotto)
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
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "libraw/libraw.h"

// stb_image (pubblico dominio / MIT, third_party/stb): JPEG e PNG per la misura della nitidezza, su ogni sistema
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_JPEG
#define STBI_ONLY_PNG
#define STBI_NO_STDIO_FAILURE_STRINGS
#include "stb_image.h"

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

// ---------------- nitidezza di un'area (autofocus) ----------------
//
//   fs-rawstat --focus <x0> <y0> <x1> <y1> [--source auto|preview|raw] <file>
//
// L'area è in frazioni (0–1) dell'immagine come la si vede (già ruotata). Misura: Tenengrad, cioè la media del
// gradiente di Sobel al quadrato sulla luminosità, diviso per la luminosità media al quadrato (così non dipende
// dall'esposizione). Più è alto, più l'area è a fuoco.
// RAW: di solito l'anteprima JPEG incorporata (veloce, già sviluppata dalla fotocamera; nelle prove sulle pile
// vere dà gli stessi picchi del RAW con meno rumore). Se l'area nell'anteprima è più piccola di MIN_FOCUS_PX
// pixel, si usa il RAW a metà risoluzione (somma di ogni cella 2×2 del mosaico, senza demosaicizzare).
// JPEG, PNG…: l'immagine stessa (stb_image). L'orientamento EXIF dei JPEG non si applica.
const int MIN_FOCUS_PX = 32;

struct Gray {
  int w = 0, h = 0;
  std::vector<double> v;
};

// Tenengrad normalizzato sull'intera immagine g (che è già l'area ritagliata)
bool tenengrad(const Gray &g, double &focus, double &mean) {
  if (g.w < 3 || g.h < 3) return false;
  double sum = 0;
  for (double x : g.v) sum += x;
  mean = sum / g.v.size();
  double acc = 0;
  for (int y = 1; y < g.h - 1; y++) {
    const double *a = &g.v[(size_t)(y - 1) * g.w], *b = &g.v[(size_t)y * g.w], *c = &g.v[(size_t)(y + 1) * g.w];
    for (int x = 1; x < g.w - 1; x++) {
      double gx = (a[x + 1] + 2 * b[x + 1] + c[x + 1]) - (a[x - 1] + 2 * b[x - 1] + c[x - 1]);
      double gy = (c[x - 1] + 2 * c[x] + c[x + 1]) - (a[x - 1] + 2 * a[x] + a[x + 1]);
      acc += gx * gx + gy * gy;
    }
  }
  double n = (double)(g.w - 2) * (g.h - 2);
  focus = mean > 1e-9 ? acc / n / (mean * mean) : 0;
  return true;
}

// rettangolo in pixel di un'immagine W×H dalle frazioni (almeno 3×3, dentro l'immagine)
void roi_px(const double f[4], int W, int H, int &x0, int &y0, int &x1, int &y1) {
  x0 = (int)std::floor(f[0] * W); y0 = (int)std::floor(f[1] * H);
  x1 = (int)std::ceil(f[2] * W); y1 = (int)std::ceil(f[3] * H);
  if (x0 < 0) x0 = 0;
  if (y0 < 0) y0 = 0;
  if (x1 > W) x1 = W;
  if (y1 > H) y1 = H;
  if (x1 - x0 < 3) { x0 = std::max(0, std::min(W - 3, (x0 + x1) / 2 - 1)); x1 = std::min(W, x0 + 3); }
  if (y1 - y0 < 3) { y0 = std::max(0, std::min(H - 3, (y0 + y1) / 2 - 1)); y1 = std::min(H, y0 + 3); }
}

// area da un'immagine RGB a 8 bit (stessa luminosità dell'Ispettore: 0,21 R + 0,72 G + 0,07 B)
Gray crop_rgb(const unsigned char *px, int W, int H, int comp, const double f[4]) {
  int x0, y0, x1, y1;
  roi_px(f, W, H, x0, y0, x1, y1);
  Gray g;
  g.w = x1 - x0; g.h = y1 - y0;
  g.v.resize((size_t)g.w * g.h);
  for (int y = y0; y < y1; y++)
    for (int x = x0; x < x1; x++) {
      const unsigned char *p = px + ((size_t)y * W + x) * comp;
      double l = comp >= 3 ? (54.0 * p[0] + 183.0 * p[1] + 19.0 * p[2]) / 256.0 : p[0];
      g.v[(size_t)(y - y0) * g.w + (x - x0)] = l;
    }
  return g;
}

// frazioni dell'immagine vista → frazioni del sensore (LibRaw sizes.flip: 3 = 180°, 5 = 90° antiorario, 6 = orario)
void unflip(int flip, const double in[4], double out[4]) {
  double u[2] = {in[0], in[2]}, v[2] = {in[1], in[3]};
  double xs[4], ys[4];
  for (int i = 0; i < 4; i++) {
    double a = u[i & 1], b = v[i >> 1];
    if (flip == 3) { xs[i] = 1 - a; ys[i] = 1 - b; }
    else if (flip == 6) { xs[i] = b; ys[i] = 1 - a; }
    else if (flip == 5) { xs[i] = 1 - b; ys[i] = a; }
    else { xs[i] = a; ys[i] = b; }
  }
  out[0] = *std::min_element(xs, xs + 4); out[2] = *std::max_element(xs, xs + 4);
  out[1] = *std::min_element(ys, ys + 4); out[3] = *std::max_element(ys, ys + 4);
}

void print_focus(const char *source, double focus, double mean, const Gray &g, int W, int H) {
  printf("{\"focus\":%s,\"mean\":%s,\"source\":\"%s\",\"roi_px\":[%d,%d],\"image\":[%d,%d]}\n",
         num(focus, 8).c_str(), num(mean, 3).c_str(), source, g.w, g.h, W, H);
}

// RAW a metà risoluzione: ogni cella 2×2 del mosaico sommata, meno il nero (valori lineari)
int focus_raw_cells(LibRaw *rp, const double s[4]) {
  int r = rp->unpack();
  if (r != LIBRAW_SUCCESS) return fail(libraw_strerror(r));
  auto &d = rp->imgdata;
  const auto &sz = d.sizes;
  if (!d.rawdata.raw_image) return fail("RAW senza mosaico: usa l'anteprima");
  int W = sz.width / 2, H = sz.height / 2, x0, y0, x1, y1;
  roi_px(s, W, H, x0, y0, x1, y1);
  double black = d.rawdata.color.black + (d.rawdata.color.cblack[0] + d.rawdata.color.cblack[1] +
                 d.rawdata.color.cblack[2] + d.rawdata.color.cblack[3]) / 4.0;
  int pitch = sz.raw_pitch / 2;
  Gray g;
  g.w = x1 - x0; g.h = y1 - y0;
  g.v.resize((size_t)g.w * g.h);
  for (int y = y0; y < y1; y++) {
    const unsigned short *l0 = d.rawdata.raw_image + (size_t)(2 * y + sz.top_margin) * pitch + sz.left_margin;
    const unsigned short *l1 = l0 + pitch;
    for (int x = x0; x < x1; x++) {
      double v = (double)l0[2 * x] + l0[2 * x + 1] + l1[2 * x] + l1[2 * x + 1] - 4 * black;
      g.v[(size_t)(y - y0) * g.w + (x - x0)] = v > 0 ? v : 0;
    }
  }
  double focus, mean;
  if (!tenengrad(g, focus, mean)) return fail("area troppo piccola");
  print_focus("raw", focus, mean, g, W, H);
  return 0;
}

int focus_file(const char *path, const double f[4], const std::string &want) {
  LibRaw *rp = new LibRaw;
  int r = rp->open_file(path);
  if (r == LIBRAW_SUCCESS) {
    double s[4];
    unflip(rp->imgdata.sizes.flip, f, s);
    if (want != "raw" && rp->unpack_thumb() == LIBRAW_SUCCESS) {
      const auto &th = rp->imgdata.thumbnail;
      int W = 0, H = 0, comp = 0;
      unsigned char *px = nullptr;
      bool owned = false;
      if (th.tformat == LIBRAW_THUMBNAIL_JPEG) {
        px = stbi_load_from_memory((const unsigned char *)th.thumb, (int)th.tlength, &W, &H, &comp, 3);
        comp = 3; owned = px != nullptr;
      } else if (th.tformat == LIBRAW_THUMBNAIL_BITMAP && th.tcolors == 3) {
        px = (unsigned char *)th.thumb; W = th.twidth; H = th.theight; comp = 3;
      }
      int x0, y0, x1, y1;
      if (px) roi_px(s, W, H, x0, y0, x1, y1);
      bool big = px && std::min(x1 - x0, y1 - y0) >= MIN_FOCUS_PX;
      if (px && (big || want == "preview")) {
        Gray g = crop_rgb(px, W, H, comp, s);
        if (owned) stbi_image_free(px);
        double focus, mean;
        delete rp;
        if (!tenengrad(g, focus, mean)) return fail("area troppo piccola");
        print_focus("preview", focus, mean, g, W, H);
        return 0;
      }
      if (owned) stbi_image_free(px);
      if (want == "preview") { delete rp; return fail("anteprima incorporata non leggibile"); }
    }
    int out = focus_raw_cells(rp, s);
    delete rp;
    return out;
  }
  delete rp;
  int W, H, comp;
  unsigned char *px = stbi_load(path, &W, &H, &comp, 3);
  if (!px) return fail(r == LIBRAW_FILE_UNSUPPORTED ? "formato non riconosciuto" : libraw_strerror(r));
  Gray g = crop_rgb(px, W, H, 3, f);
  stbi_image_free(px);
  double focus, mean;
  if (!tenengrad(g, focus, mean)) return fail("area troppo piccola");
  print_focus("image", focus, mean, g, W, H);
  return 0;
}

// ---------------- analisi del sensore (curva di trasferimento dei fotoni) ----------------
// Ritaglio centrale di un canale verde del mosaico, valori grezzi: niente demosaicizzazione né bilanciamento.
struct Plane {
  std::vector<double> v;
  double black = 0, white = 0, iso = 0, shutter = 0;
  std::string camera, error;
};

Plane green_plane(const char *path, int side) {
  Plane p;
  LibRaw *rp = new LibRaw;
  int r = rp->open_file(path);
  if (r == LIBRAW_SUCCESS) r = rp->unpack();
  if (r != LIBRAW_SUCCESS) { p.error = std::string(path) + ": " + libraw_strerror(r); delete rp; return p; }
  auto &d = rp->imgdata;
  const auto &sz = d.sizes;
  const auto &col = d.rawdata.color;
  unsigned short *raw = d.rawdata.raw_image;
  if (!raw) { p.error = std::string(path) + ": non è un RAW a mosaico"; delete rp; return p; }
  p.black = col.black + col.cblack[1];
  // bianco dichiarato nei metadati (Sony: 15360) se c'è, altrimenti il massimo teorico di LibRaw (16383)
  p.white = col.linear_max[1] > 0 ? (double)col.linear_max[1] : (double)col.maximum;
  p.iso = d.other.iso_speed; p.shutter = d.other.shutter;
  p.camera = std::string(d.idata.make) + " " + d.idata.model;
  int n = std::min(side, std::min(sz.height, sz.width) / 2 - 4);
  int y0 = (sz.top_margin + sz.height / 2 - n) & ~1, x0 = (sz.left_margin + sz.width / 2 - n) & ~1;
  int dy = -1, dx = -1;
  for (int yy = 0; yy < 2 && dy < 0; yy++)
    for (int xx = 0; xx < 2; xx++)
      if (rp->COLOR(y0 + yy - sz.top_margin, x0 + xx - sz.left_margin) == 1) { dy = yy; dx = xx; break; }
  if (dy < 0) { p.error = std::string(path) + ": nessun pixel verde"; delete rp; return p; }
  p.v.reserve((size_t)n * n);
  for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++) p.v.push_back(raw[(size_t)(y0 + dy + 2 * i) * (sz.raw_pitch / 2) + x0 + dx + 2 * j]);
  delete rp;
  return p;
}

double mean_of(const std::vector<double> &a) { double s = 0; for (double x : a) s += x; return a.empty() ? 0 : s / a.size(); }

double diff_var(const std::vector<double> &a, const std::vector<double> &b) {
  double s = 0, s2 = 0; size_t n = std::min(a.size(), b.size());
  for (size_t i = 0; i < n; i++) { double d = a[i] - b[i]; s += d; s2 += d * d; }
  return n > 1 ? (s2 - s * s / n) / (n - 1) : 0;
}

// --ptc flat1 flat2 dark1 dark2: due flat e due dark con le stesse impostazioni. La differenza fra due scatti uguali
// toglie tutto quello che è fisso (polvere, vignettatura, pixel caldi) e lascia solo il rumore:
// guadagno (e-/ADU) = segnale / (varianza della differenza dei flat − quella dei dark), rumore di lettura =
// deviazione della differenza dei dark / √2, pieno pozzetto = (bianco − nero) × guadagno.
int ptc(char **files, int side) {
  Plane f1 = green_plane(files[0], side), f2 = green_plane(files[1], side);
  Plane d1 = green_plane(files[2], side), d2 = green_plane(files[3], side);
  for (Plane *p : {&f1, &f2, &d1, &d2}) if (!p->error.empty()) return fail(p->error);
  if (f1.v.size() != f2.v.size() || f1.v.size() != d1.v.size() || f1.v.size() != d2.v.size())
    return fail("flat e dark di dimensioni diverse");
  double dm = (mean_of(d1.v) + mean_of(d2.v)) / 2, fm1 = mean_of(f1.v) - dm, fm2 = mean_of(f2.v) - dm;
  double vd = diff_var(d1.v, d2.v), vf = diff_var(f1.v, f2.v);
  double range = f1.white - f1.black;
  unsigned long long sat = 0;
  for (const Plane *p : {&f1, &f2}) for (double x : p->v) if (x >= p->white - 1) sat++;
  double gain = vf > vd ? (fm1 + fm2) / (vf - vd) : NAN;
  double rn_adu = std::sqrt(vd / 2), rn_e = rn_adu * gain, fw = range * gain;
  printf("{\"kind\":\"ptc\",\"camera\":\"%s\",\"iso\":%s,\"shutter_s\":%s,\"black\":%s,\"white\":%s,"
         "\"dark_mean\":%s,\"flat_signal_adu\":%s,\"flat_level_pct\":%s,\"flat_diff_var\":%s,\"dark_diff_var\":%s,"
         "\"gain_e_adu\":%s,\"read_noise_adu\":%s,\"read_noise_e\":%s,\"full_well_e\":%s,\"dynamic_range_stops\":%s,"
         "\"saturated_pct\":%s,\"samples\":%zu,\"libraw\":\"%s\"}\n",
         esc(f1.camera.c_str()).c_str(), num(f1.iso, 0).c_str(), num(f1.shutter, 6).c_str(), num(f1.black, 1).c_str(),
         num(f1.white, 0).c_str(), num(dm, 2).c_str(), num((fm1 + fm2) / 2, 1).c_str(),
         num(range > 0 ? (fm1 + fm2) / 2 / range * 100 : NAN, 2).c_str(), num(vf, 3).c_str(), num(vd, 3).c_str(),
         num(gain, 4).c_str(), num(rn_adu, 3).c_str(), num(rn_e, 3).c_str(), num(fw, 0).c_str(),
         num(rn_e > 0 && fw > 0 ? std::log2(fw / rn_e) : NAN, 2).c_str(),
         num(100.0 * sat / (f1.v.size() + f2.v.size()), 4).c_str(), f1.v.size(), LibRaw::version());
  return 0;
}

}  // namespace

int main(int argc, char **argv) {
  if (argc >= 2 && !strcmp(argv[1], "--ptc")) {
    // --ptc [--side N] flat1 flat2 dark1 dark2   (N = metà del lato del ritaglio, in pixel verdi; predefinito 400)
    int side = 400, first = 2;
    if (argc >= 4 && !strcmp(argv[2], "--side")) { side = atoi(argv[3]); first = 4; }
    if (argc - first != 4 || side < 16) return fail("uso: --ptc [--side N] flat1 flat2 dark1 dark2");
    return ptc(argv + first, side);
  }
  if (argc >= 2 && !strcmp(argv[1], "--focus")) {
    // --focus x0 y0 x1 y1 [--source auto|preview|raw] file
    if (argc != 7 && argc != 9) return fail("uso: --focus x0 y0 x1 y1 [--source auto|preview|raw] file");
    double f[4];
    for (int i = 0; i < 4; i++) f[i] = atof(argv[2 + i]);
    if (!(f[0] >= 0 && f[1] >= 0 && f[2] <= 1 && f[3] <= 1 && f[2] > f[0] && f[3] > f[1])) return fail("area non valida");
    std::string want = "auto";
    if (argc == 9) {
      if (strcmp(argv[6], "--source")) return fail("opzione sconosciuta");
      want = argv[7];
      if (want != "auto" && want != "preview" && want != "raw") return fail("sorgente non valida");
    }
    return focus_file(argv[argc - 1], f, want);
  }
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
