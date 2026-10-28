import CameraPanel from "@/components/CameraPanel"
import Card from "@/components/Card"
import PowerPanel from "@/components/PowerPanel"
import CameraControls from "@/components/CameraControls"
import ImuAttitude from "@/components/ImuAttitude"

export default function Home() {
  return (
    <main className="grid flex-1 grid-cols-12 auto-rows-[100px] gap-2.5 p-3">
      <div className="col-span-6 row-span-6 flex flex-col gap-2.5">
        <Card title="Map" className="flex-1" />
        <Card title="Autonomy Mission"/>
      </div>
      <CameraPanel title="Camera 1" status="live" className="col-span-3 row-span-3" />
      <CameraPanel title="Camera 2" status="no-signal" className="col-span-3 row-span-3" />
      <CameraPanel title="Camera 3" status="live" className="col-span-3 row-span-3" />
      <CameraPanel title="Camera 4" status="no-signal" className="col-span-3 row-span-3" />
      <Card title="Compass" className="col-span-3 row-span-3" />
      <PowerPanel className="col-span-3 row-span-3" />
      <ImuAttitude className="col-span-3 row-span-3" />
      <CameraControls className="col-span-3 row-span-3" />
      <Card title="Quick Command Console" className="col-span-12 row-span-2" />
    </main>
  )
}