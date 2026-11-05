import CameraPanel from "@/components/CameraPanel"
import Card from "@/components/Card"
import PowerPanel from "@/components/PowerPanel"
import CameraControls from "@/components/CameraControls"
import ImuAttitude from "@/components/ImuAttitude"
import CommandConsole from "@/components/CommandConsole"
import AutonomyPanel from "@/components/AutonomyPanel"
import MapPanel from "@/components/MapPanel"
import MapControls from "@/components/MapControls"

export default function Home() {
  return (
    <>
      <main className="grid flex-1 grid-cols-1 auto-rows-[100px] gap-2.5 p-3 lg:grid-cols-12">
        <div className="row-span-6 flex flex-col gap-2.5 lg:col-span-6">
          <MapPanel className="flex-1" />
          <MapControls />
          <AutonomyPanel />
        </div>
        <CameraPanel title="IntelRealsense RGB Camera" status="live" className="row-span-3 lg:col-span-3" />
        <CameraPanel title="IntelRealsense Depth Camera" status="live" className="row-span-3 lg:col-span-3" />
        <CameraPanel title="Webcam RGB Camera 1" status="live" className="row-span-3 lg:col-span-3" />
        <CameraPanel title="Webcam RGB Camera 2" status="no-signal" className="row-span-3 lg:col-span-3" />
        <Card title="Compass" className="lg:col-span-3 row-span-3" />
        <PowerPanel className="lg:col-span-3 row-span-3" />
        <ImuAttitude className="lg:col-span-3 row-span-3" />
        <CameraControls className="lg:col-span-3 row-span-3" />
      </main>
      <CommandConsole />
    </>
  )
}