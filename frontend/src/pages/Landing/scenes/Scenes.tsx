import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import type { Palette } from "./palette";
import type { SceneKind } from "./Stage";

interface SceneProps {
  p: Palette;
  reduced: boolean;
  mouse: React.RefObject<{ x: number; y: number }>;
  broken?: boolean[];
}

function usePointer() {
  const m = useRef({ x: 0, y: 0 });
  useEffect(() => {
    const f = (e: PointerEvent) => {
      m.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      m.current.y = -((e.clientY / window.innerHeight) * 2 - 1);
    };
    window.addEventListener("pointermove", f, { passive: true });
    return () => window.removeEventListener("pointermove", f);
  }, []);
  return m;
}


/* ------------------------------------------------------------ shared pieces */

/** A ring of interlocked links: the hash chain, made physical. */
function ChainRing({ radius, count, color, link = 0.17 }: { radius: number; count: number; color: string; link?: number }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const m = ref.current;
    if (!m) return;
    const d = new THREE.Object3D();
    d.rotation.order = "YXZ";
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2;
      d.position.set(Math.cos(a) * radius, 0, Math.sin(a) * radius);
      d.rotation.set(i % 2 ? Math.PI / 2 : 0, Math.PI / 2 - a, 0);
      d.scale.set(1.55, 1, 1);
      d.updateMatrix();
      m.setMatrixAt(i, d.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
  }, [radius, count]);
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, count]}>
      <torusGeometry args={[link, link * 0.3, 10, 26]} />
      <meshStandardMaterial color={color} roughness={0.38} metalness={0.15} />
    </instancedMesh>
  );
}

function Lights() {
  return (
    <>
      <ambientLight intensity={1.05} />
      <directionalLight position={[4, 6, 5]} intensity={2.4} />
      <directionalLight position={[-5, -2, -3]} intensity={0.7} color="#6c8cff" />
    </>
  );
}

/* --------------------------------------------------------------- hero orbit */

function Orbit({ p, reduced, mouse }: SceneProps) {
  const g = useRef<THREE.Group>(null);
  const orbs = useRef<(THREE.Mesh | null)[]>([]);
  const kinds = [
    { color: p.ok, r: 2.15, s: 0.55, ph: 0.2, size: 0.3 },
    { color: p.bad, r: 2.75, s: -0.4, ph: 2.3, size: 0.24 },
    { color: p.gap, r: 3.3, s: 0.3, ph: 4.4, size: 0.27 },
  ];
  useFrame((s) => {
    const grp = g.current;
    if (!grp) return;
    const t = reduced ? 0 : s.clock.elapsedTime;
    const sc = window.scrollY / Math.max(1, window.innerHeight);
    grp.rotation.y = t * 0.14 + sc * 1.1 + mouse.current.x * 0.35;
    grp.rotation.x = 1.08 + mouse.current.y * 0.16 - sc * 0.25;
    kinds.forEach((k, i) => {
      const o = orbs.current[i];
      if (!o) return;
      const a = t * k.s + k.ph;
      o.position.set(Math.cos(a) * k.r, Math.sin(t * 0.9 + i) * 0.18, Math.sin(a) * k.r);
    });
  });
  return (
    <group ref={g}>
      <ChainRing radius={2.5} count={20} color={p.bright} />
      <ChainRing radius={3.55} count={26} color={p.surface2} link={0.15} />
      {kinds.map((k, i) => (
        <mesh key={i} ref={(el) => { orbs.current[i] = el; }}>
          <sphereGeometry args={[k.size, 28, 20]} />
          <meshStandardMaterial color={k.color} roughness={0.3} metalness={0.1} />
        </mesh>
      ))}
    </group>
  );
}

/* ------------------------------------------------------------- sealed case */

function SealedCase({ p, reduced, mouse }: SceneProps) {
  const g = useRef<THREE.Group>(null);
  const sheets = useRef<THREE.Group>(null);
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(2.42, 1.62, 1.62)), []);
  useEffect(() => () => edges.dispose(), [edges]);
  useFrame((s) => {
    const t = reduced ? 0 : s.clock.elapsedTime;
    if (g.current) {
      g.current.rotation.y = -0.55 + Math.sin(t * 0.35) * 0.35 + mouse.current.x * 0.4;
      g.current.rotation.x = 0.22 + mouse.current.y * 0.18;
      g.current.position.y = Math.sin(t * 0.8) * 0.06;
    }
    if (sheets.current) sheets.current.rotation.y = t * 0.2;
  });
  return (
    <group ref={g}>
      <mesh>
        <boxGeometry args={[2.4, 1.6, 1.6]} />
        <meshStandardMaterial color={p.accent} roughness={0.42} metalness={0.12} />
      </mesh>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color={p.deep} />
      </lineSegments>
      <mesh position={[0, 0.42, 0]}>
        <boxGeometry args={[2.46, 0.05, 1.66]} />
        <meshStandardMaterial color={p.deep} roughness={0.5} />
      </mesh>
      <group position={[0, -0.1, 0.83]} rotation={[Math.PI / 2, 0, 0]}>
        <mesh>
          <cylinderGeometry args={[0.4, 0.4, 0.07, 40]} />
          <meshStandardMaterial color={p.bg} roughness={0.35} />
        </mesh>
        <mesh position={[0, 0.03, 0]}>
          <cylinderGeometry args={[0.25, 0.25, 0.07, 40]} />
          <meshStandardMaterial color={p.bright} roughness={0.35} />
        </mesh>
      </group>
      <group rotation={[0.08, 0, 0.05]}>
        <ChainRing radius={2.15} count={16} color={p.deep} />
      </group>
      <group ref={sheets}>
        {Array.from({ length: 6 }, (_, i) => {
          const a = (i / 6) * Math.PI * 2;
          return (
            <mesh key={i} position={[Math.cos(a) * 3.05, Math.sin(a * 2) * 0.35, Math.sin(a) * 3.05]} rotation={[0, Math.PI / 2 - a, 0]}>
              <boxGeometry args={[0.9, 1.15, 0.03]} />
              <meshStandardMaterial color={i % 2 ? p.bg : p.surface2} roughness={0.6} />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

/* ----------------------------------------------------------------- pipeline */

const PIPE_N = 5;

function Pipeline({ p, reduced }: SceneProps) {
  const { viewport } = useThree();
  const nodes = useRef<(THREE.Mesh | null)[]>([]);
  const packets = useRef<(THREE.Mesh | null)[]>([]);
  const xs = useMemo(
    () => Array.from({ length: PIPE_N }, (_, i) => (((i + 0.5) / PIPE_N) - 0.5) * viewport.width),
    [viewport.width],
  );
  const y = (x: number) => Math.sin(x * 0.9) * 0.22;
  const start = useMemo(() => new THREE.Color(p.gap), [p.gap]);
  const end = useMemo(() => new THREE.Color(p.ok), [p.ok]);
  const tmp = useMemo(() => new THREE.Color(), []);
  const x0 = xs[0];
  const x1 = xs[PIPE_N - 1];
  useFrame((s) => {
    const t = reduced ? 0 : s.clock.elapsedTime;
    nodes.current.forEach((n, i) => {
      if (!n) return;
      n.rotation.y = t * 0.6 + i;
      n.rotation.x = t * 0.3 + i * 0.5;
    });
    packets.current.forEach((m, i) => {
      if (!m) return;
      const u = reduced ? (i + 0.5) / 4 : (t * 0.12 + i / 4) % 1;
      const x = x0 + (x1 - x0) * u;
      m.position.set(x, y(x), 0.4);
      tmp.copy(start).lerp(end, u);
      (m.material as THREE.MeshStandardMaterial).color.copy(tmp);
    });
  });
  const geo = [
    <icosahedronGeometry key="a" args={[0.5, 0]} />,
    <octahedronGeometry key="b" args={[0.55, 0]} />,
    <boxGeometry key="c" args={[0.7, 0.7, 0.7]} />,
    <dodecahedronGeometry key="d" args={[0.5, 0]} />,
    <torusKnotGeometry key="e" args={[0.32, 0.12, 64, 10]} />,
  ];
  const line = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 48; i++) {
      const x = x0 + ((x1 - x0) * i) / 48;
      pts.push(new THREE.Vector3(x, y(x), 0));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [x0, x1]);
  useEffect(() => () => line.dispose(), [line]);
  return (
    <group>
      <line>
        <primitive object={line} attach="geometry" />
        <lineBasicMaterial color={p.surface2} />
      </line>
      {xs.map((x, i) => (
        <mesh key={i} position={[x, y(x), 0]} ref={(el) => { nodes.current[i] = el; }}>
          {geo[i]}
          <meshStandardMaterial color={i === PIPE_N - 1 ? p.deep : p.accent} roughness={0.38} metalness={0.12} />
        </mesh>
      ))}
      {[0, 1, 2, 3].map((i) => (
        <mesh key={`p${i}`} ref={(el) => { packets.current[i] = el; }}>
          <sphereGeometry args={[0.1, 16, 12]} />
          <meshStandardMaterial color={p.gap} roughness={0.3} />
        </mesh>
      ))}
    </group>
  );
}

/* --------------------------------------------------------------- hash chain */

function HashChain({ p, reduced, broken = [] }: SceneProps) {
  const { viewport, invalidate } = useThree();
  const n = 4;
  const blocks = useRef<(THREE.Mesh | null)[]>([]);
  const links = useRef<(THREE.Mesh | null)[]>([]);
  const xs = useMemo(() => Array.from({ length: n }, (_, i) => (((i + 0.5) / n) - 0.5) * viewport.width), [viewport.width]);
  const okC = useMemo(() => new THREE.Color(p.accent), [p.accent]);
  const badC = useMemo(() => new THREE.Color(p.bad), [p.bad]);
  const key = broken.join(",");
  useEffect(() => { invalidate(); }, [key, invalidate]);
  useFrame((s, dt) => {
    const t = reduced ? 0 : s.clock.elapsedTime;
    const k = reduced ? 1 : 1 - Math.exp(-7 * dt);
    blocks.current.forEach((b, i) => {
      if (!b) return;
      const bad = !!broken[i];
      const mat = b.material as THREE.MeshStandardMaterial;
      mat.color.lerp(bad ? badC : okC, k);
      b.position.y += ((bad ? -0.3 : Math.sin(t * 0.9 + i) * 0.08) - b.position.y) * k;
      b.rotation.z += ((bad ? (i % 2 ? 0.28 : -0.22) : 0) - b.rotation.z) * k;
      b.rotation.y = t * 0.35 + i * 0.6;
    });
    links.current.forEach((l, i) => {
      if (!l) return;
      const gone = !!broken[i + 1];
      const mat = l.material as THREE.MeshStandardMaterial;
      mat.color.lerp(gone ? badC : okC, k);
      l.visible = true;
      l.scale.x += ((gone ? 0.55 : 1) - l.scale.x) * k;
    });
  });
  return (
    <group>
      {xs.map((x, i) => (
        <mesh key={i} position={[x, 0, 0]} ref={(el) => { blocks.current[i] = el; }}>
          <boxGeometry args={[0.95, 0.95, 0.95]} />
          <meshStandardMaterial color={p.accent} roughness={0.4} metalness={0.1} />
        </mesh>
      ))}
      {xs.slice(0, -1).map((x, i) => (
        <mesh key={`l${i}`} position={[(x + xs[i + 1]) / 2, 0, 0]} rotation={[0, 0, Math.PI / 2]} ref={(el) => { links.current[i] = el; }}>
          <cylinderGeometry args={[0.07, 0.07, Math.max(0.2, xs[i + 1] - x - 1.1), 12]} />
          <meshStandardMaterial color={p.accent} roughness={0.4} />
        </mesh>
      ))}
    </group>
  );
}

/* ----------------------------------------------------------- evidence field */

const FIELD_N = 640;

function EvidenceField({ p, reduced, mouse }: SceneProps) {
  const { viewport } = useThree();
  const ref = useRef<THREE.InstancedMesh>(null);
  const seeds = useMemo(() => {
    let s = 7;
    const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    return Array.from({ length: FIELD_N }, () => ({ x: r() - 0.5, y: r() - 0.5, z: r() * 7 - 4, ph: r() * 6.283, sz: 0.6 + r() * 1.1 }));
  }, []);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  useFrame((s) => {
    const m = ref.current;
    if (!m) return;
    const t = reduced ? 0 : s.clock.elapsedTime;
    const w = viewport.width * 1.15;
    const h = viewport.height * 1.15;
    const mx = mouse.current.x * w * 0.5;
    const my = mouse.current.y * h * 0.5;
    for (let i = 0; i < FIELD_N; i++) {
      const o = seeds[i];
      let x = o.x * w + Math.sin(t * 0.25 + o.ph) * 0.25;
      let y = o.y * h + Math.cos(t * 0.3 + o.ph) * 0.25;
      const dx = x - mx;
      const dy = y - my;
      const d2 = dx * dx + dy * dy;
      if (d2 < 2.4) {
        const f = (1 - d2 / 2.4) * 0.9;
        const d = Math.sqrt(d2) || 1;
        x += (dx / d) * f;
        y += (dy / d) * f;
      }
      dummy.position.set(x, y, o.z);
      dummy.scale.setScalar(o.sz);
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
  });
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, FIELD_N]} frustumCulled={false}>
      <octahedronGeometry args={[0.06, 0]} />
      <meshBasicMaterial color={p.inkOn} transparent opacity={0.38} />
    </instancedMesh>
  );
}

/* ------------------------------------------------------------------- canvas */

interface Props {
  kind: SceneKind;
  palette: Palette;
  active: boolean;
  reduced: boolean;
  broken?: boolean[];
}

export default function Scenes({ kind, palette, active, reduced, broken }: Props) {
  const mouse = usePointer();
  const ortho = kind === "pipeline" || kind === "chain";
  const camera = ortho
    ? { zoom: 48, position: [0, 0, 10] as [number, number, number] }
    : kind === "case"
      ? { position: [0, 0.4, 8.2] as [number, number, number], fov: 38 }
      : kind === "field"
        ? { position: [0, 0, 7] as [number, number, number], fov: 55 }
        : { position: [0, 0, 10] as [number, number, number], fov: 36 };
  const shared: SceneProps = { p: palette, reduced, mouse, broken };
  return (
    <Canvas
      orthographic={ortho}
      camera={camera}
      dpr={[1, 1.75]}
      frameloop={active && !reduced ? "always" : "demand"}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      resize={{ scroll: false }}
    >
      {kind !== "field" ? <Lights /> : null}
      {kind === "orbit" ? <Orbit {...shared} /> : null}
      {kind === "case" ? <SealedCase {...shared} /> : null}
      {kind === "pipeline" ? <Pipeline {...shared} /> : null}
      {kind === "chain" ? <HashChain {...shared} /> : null}
      {kind === "field" ? <EvidenceField {...shared} /> : null}
    </Canvas>
  );
}
