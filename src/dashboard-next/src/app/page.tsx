import Card from "@/components/Card"

export default function Home() {
  return (
    <main className="grid flex-1 grid-cols-12 auto-rows-[100px] gap-2.5 p-3">
      <div className="col-span-6 row-span-6 flex flex-col gap-2.5">
        <Card title="Map" className="flex-1" />
        <Card title="Autonomy Mission"/>
      </div>
      <Card title="Camera 1" className="col-span-3 row-span-3" />
      <Card title="Camera 2" className="col-span-3 row-span-3" />
      <Card title="Camera 3" className="col-span-3 row-span-3" />
      <Card title="Camera 4" className="col-span-3 row-span-3" />
      <Card title="Compass" className="col-span-3 row-span-3" />
      <Card title="Power & Jetson" className="col-span-3 row-span-3" />
      <Card title="IMU Attitude" className="col-span-3 row-span-3" />
      <Card title="Camera Controls" className="col-span-3 row-span-3" />
      <Card title="Quick Command Console" className="col-span-12 row-span-2" />
    </main>
  )
}