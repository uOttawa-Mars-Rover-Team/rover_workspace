import Card from "./components/Card"
import StatusPill from "./components/StatusPill"

export default function Home() {
  return (
    <main className="flex-1 p-3">
      <Card title="Test Card">
        <p className="text-muted">This is a test card.</p>
      </Card>
      <div className="flex gap-2">
        <StatusPill label="Bridge" value="Connected" valueClassName="text-ok" />
        <StatusPill label="Latency" value="42 ms"/>
      </div>
    </main>
  )
}