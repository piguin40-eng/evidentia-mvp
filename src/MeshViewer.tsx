import { Canvas, useLoader } from '@react-three/fiber'
import { Bounds, Grid, OrbitControls } from '@react-three/drei'
import { useEffect, useMemo, useRef, useState } from 'react'
import { FileUp, Focus, RotateCcw } from 'lucide-react'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js'
import type { BufferGeometry } from 'three'

function PreparedMesh({ geometry, color = '#dedbd2' }: { geometry: BufferGeometry; color?: string }) {
  const prepared = useMemo(() => {
    const clone = geometry.clone()
    clone.center()
    clone.computeVertexNormals()
    return clone
  }, [geometry])
  useEffect(() => () => prepared.dispose(), [prepared])
  return <mesh geometry={prepared} castShadow receiveShadow>
    <meshPhysicalMaterial color={color} roughness={0.48} metalness={0.02} clearcoat={0.22}/>
  </mesh>
}

function StlModel({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url)
  return <PreparedMesh geometry={geometry}/>
}

function PlyModel({ url }: { url: string }) {
  const geometry = useLoader(PLYLoader, url)
  return <PreparedMesh geometry={geometry}/>
}

type MeshSource = { url: string; kind: 'stl' | 'ply'; name: string }

export function MeshViewer({ onFileSelected, source }: { onFileSelected?: (file: File) => void; source?: MeshSource }) {
  const input = useRef<HTMLInputElement>(null)
  const controls = useRef<any>(null)
  const [file, setFile] = useState<{ url: string; kind: 'stl' | 'ply'; name: string; objectUrl: boolean }>(() => source ? { ...source, objectUrl: false } : {
    url: '/synthetic-dental-arch.stl',
    kind: 'stl',
    name: 'Malla dental sintética · sin datos clínicos',
    objectUrl: false,
  })
  const [cameraKey, setCameraKey] = useState(0)

  useEffect(() => {
    if (source) setFile({ ...source, objectUrl: false })
  }, [source])
  useEffect(() => () => { if (file.objectUrl) URL.revokeObjectURL(file.url) }, [file])
  const chooseFile = (selected: File | undefined) => {
    if (!selected) return
    const extension = selected.name.split('.').pop()?.toLowerCase()
    if (extension !== 'stl' && extension !== 'ply') return
    onFileSelected?.(selected)
    setFile({ url: URL.createObjectURL(selected), kind: extension, name: selected.name, objectUrl: true })
  }

  return <div className="viewer-shell">
    <div className="viewer-toolbar">
      <div><span className="live-dot"/> {file.name}</div>
      <div className="viewer-actions">
        <button onClick={() => input.current?.click()}><FileUp size={15}/> Cargar STL/PLY</button>
        <button title="Centrar" onClick={() => setCameraKey(value => value + 1)}><Focus size={16}/></button>
        <button title="Restablecer cámara" onClick={() => controls.current?.reset()}><RotateCcw size={16}/></button>
      </div>
      <input id="mesh-file-input" ref={input} hidden type="file" accept=".stl,.ply" onChange={event => { chooseFile(event.target.files?.[0]); event.target.value = '' }}/>
    </div>
    <Canvas key={cameraKey} shadows dpr={[1, 1.7]} camera={{ position: [0, 32, 72], fov: 35 }}>
      <color attach="background" args={['#090a0c']}/>
      <fog attach="fog" args={['#090a0c', 120, 240]}/>
      <ambientLight intensity={0.65}/>
      <directionalLight castShadow position={[32, 48, 30]} intensity={2.8}/>
      <directionalLight position={[-26, 12, -18]} intensity={1.15} color="#e34f45"/>
      <Grid position={[0, -11, 0]} args={[130, 130]} cellSize={5} cellThickness={0.3} cellColor="#2a2d33" sectionSize={25} sectionColor="#4b515a" fadeDistance={115} infiniteGrid/>
      <Bounds fit clip observe margin={window.innerWidth <= 760 ? 1.08 : 0.92}>{file.kind === 'stl' ? <StlModel url={file.url}/> : <PlyModel url={file.url}/>}</Bounds>
      <OrbitControls ref={controls} makeDefault enableDamping dampingFactor={0.08} minDistance={18} maxDistance={180}/>
    </Canvas>
    <div className="viewer-foot"><span>ARRASTRA PARA ROTAR · PELLIZCA PARA ZOOM</span><strong>GEOMETRÍA CENTRADA</strong></div>
  </div>
}
