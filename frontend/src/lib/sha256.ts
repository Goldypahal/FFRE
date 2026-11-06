/* Small synchronous SHA-256 for the in-page demos. Returns lowercase hex. */
export const sha256 = (() => {
  const K: number[] = [], H: number[] = [];
  const frac = (x: number) => ((x - Math.floor(x)) * 4294967296) | 0;
  for (let c = 2, n = 0; n < 64; c++) {
    let prime = true;
    for (let d = 2; d * d <= c; d++) if (c % d === 0) { prime = false; break; }
    if (!prime) continue;
    if (n < 8) H[n] = frac(Math.pow(c, 0.5));
    K[n++] = frac(Math.pow(c, 1 / 3));
  }
  return function (text: string): string {
    const bytes = new TextEncoder().encode(text);
    const len = bytes.length;
    const size = ((len + 9 + 63) >> 6) << 6;
    const buf = new Uint8Array(size);
    buf.set(bytes);
    buf[len] = 0x80;
    const dv = new DataView(buf.buffer);
    dv.setUint32(size - 8, Math.floor((len * 8) / 4294967296));
    dv.setUint32(size - 4, (len * 8) >>> 0);
    const h = H.slice();
    const w = new Int32Array(64);
    for (let o = 0; o < size; o += 64) {
      for (let t = 0; t < 16; t++) w[t] = dv.getInt32(o + t * 4);
      for (let t = 16; t < 64; t++) {
        const a = w[t - 15], b = w[t - 2];
        const s0 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
        const s1 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
      }
      let [a, b, c, d, e, f, g, hh] = h as [number, number, number, number, number, number, number, number];
      for (let t = 0; t < 64; t++) {
        const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
        const ch = (e & f) ^ (~e & g);
        const t1 = (hh + S1 + ch + K[t] + w[t]) | 0;
        const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
        const mj = (a & b) ^ (a & c) ^ (b & c);
        const t2 = (S0 + mj) | 0;
        hh = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      h[0] = (h[0] + a) | 0; h[1] = (h[1] + b) | 0; h[2] = (h[2] + c) | 0; h[3] = (h[3] + d) | 0;
      h[4] = (h[4] + e) | 0; h[5] = (h[5] + f) | 0; h[6] = (h[6] + g) | 0; h[7] = (h[7] + hh) | 0;
    }
    return h.map((x) => (x >>> 0).toString(16).padStart(8, '0')).join('');
  };
})();
